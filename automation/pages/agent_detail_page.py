"""Agent Detail Page - View and manage individual agent.

Handles: /agents/all/{id}
- View agent information (ID, version)
- Manage toolkits (add/remove)
- Internal tools (toggle switches)
- Embedded chat panel
- Actions menu (delete, export)
- Edit agent (includes form from AgentFormPage)
"""

import logging
import re
import time
from urllib.parse import urlparse
from playwright.sync_api import Page, Locator, Download

from .base_page import BasePage
from .agent_form_page import AgentFormPage
from .locator_descriptor import LocatorDescriptor
from .internal_tools import InternalTool, get_tool_testid
from components.mui import Dialog, Popper
from utils.actions import action


logger = logging.getLogger("elitea.pages.agent_detail")


class AgentDetailPage(AgentFormPage):
    """Page object for agent detail/edit page.

    Inherits from AgentFormPage to reuse form filling functionality.
    Adds detail-specific operations like toolkits, chat, and actions menu.
    """

    # ===================================================================
    # LOCATORS - All element locators defined here for easy maintenance
    # ===================================================================

    # --- Information section ---
    information_section = LocatorDescriptor(testid="agent-information-section")
    copy_id_button = LocatorDescriptor(testid="copy-id")
    copy_version_id_button = LocatorDescriptor(testid="copy-version-id")

    # --- Version management (Save As Version / VERSION selector) — testids
    # added in the ELITEA-1888 testid-only rework (see EliteaUI draft PR
    # #567: SaveNewVersionButton.jsx, VersionSelect.jsx,
    # ApplicationVersionSelect.jsx, BaseModal.jsx). `save_as_version_button`
    # itself is inherited from AgentFormPage. ---
    version_selector_trigger = LocatorDescriptor(
        testid="agent-version-selector-trigger",
        description="VERSION dropdown trigger (base ⇄ named-version switcher)"
    )
    create_version_name_input = LocatorDescriptor(
        testid="agent-version-dialog-name-input",
        description='"Create version" dialog — Name field'
    )
    create_version_save_button = LocatorDescriptor(
        testid="agent-version-dialog-save-button",
        description='"Create version" dialog — confirm ("Save") button; '
                     'disabled until Name is non-empty'
    )
    create_version_cancel_button = LocatorDescriptor(
        testid="agent-version-dialog-cancel-button",
        description='"Create version" dialog — Cancel button'
    )
    create_version_close_button = LocatorDescriptor(
        testid="agent-version-dialog-close-button",
        description='"Create version" dialog — X close button'
    )

    # Dynamic (runtime-parameterized) testid for a VERSION-selector option,
    # keyed by version name — the same `version-option-{}` template shared
    # by every version selector consumer (skill/agent/pipeline); see also
    # SkillDetailPage.VERSION_OPTION.
    VERSION_OPTION = '[data-testid="version-option-{}"]'

    # Scoped sub-selector for the pin icon rendered INSIDE a version option
    # (ELITEA-1891 testid-only rework — added via add-data-testid to
    # version.helpers.jsx's buildVersionOption(); see EliteaUI
    # automation/testids commit 4e5b819d). Only rendered on the option whose
    # id equals the agent's `meta.default_version_id` — chain off the
    # ALREADY-testid'd `VERSION_OPTION.format(name)` parent, never a
    # page-level handle: `self.page.locator(self.VERSION_OPTION.format(name))
    # .locator(self.VERSION_OPTION_PIN_ICON)`.
    VERSION_OPTION_PIN_ICON = '[data-testid="version-option-pin-icon"]'

    # Any-version-option selector for reading the VERSION dropdown's full
    # option ORDER (ELITEA-1891) — excludes VERSION_OPTION_PIN_ICON, whose
    # testid also starts with the `version-option-` prefix but lives on a
    # nested non-option child <svg>, not the option MenuItem itself. Purely
    # testid-keyed (no role/CSS-structure dependency).
    VERSION_OPTION_ANY = (
        '[data-testid^="version-option-"]:not([data-testid="version-option-pin-icon"])'
    )

    # --- Variables section (ELITEA-1884 testid-only rework — added via
    # add-data-testid to ApplicationVariables.jsx / VariableList.jsx; see
    # EliteaUI draft PR #568). `ApplicationVariables.jsx` renders `null`
    # (the whole section absent from the DOM, not merely empty/collapsed)
    # when the current Instructions text contains zero `{{name}}`
    # references — confirmed live in the ELITEA-1884 analyst run. ---
    variables_section = LocatorDescriptor(
        testid="agent-variables-section",
        description='"Variables" accordion section — absent from the DOM '
                    "entirely when Instructions has zero {{name}} references"
    )
    # Dynamic (runtime-parameterized) testid templates, keyed by variable
    # name — same class-constant + `.format()` pattern as VERSION_OPTION
    # above (`.agents/testing.md` § Locator policy).
    VARIABLE_ROW = '[data-testid="agent-variable-row-{}"]'
    VARIABLE_INPUT = '[data-testid="agent-variable-input-{}"]'
    # Prefix-match variant: enumerates every currently-rendered variable row
    # (used to read back DOM order, which mirrors first-appearance order in
    # the Instructions text — see get_variable_row_names()).
    VARIABLE_ROW_ANY_SELECTOR = '[data-testid^="agent-variable-row-"]'

    # --- Toolkits section ---
    toolkits_section = LocatorDescriptor(testid="agent-toolkits-section")
    add_toolkit_button = LocatorDescriptor(testid="agent-add-toolkit-button")
    # "+ MCP" add button (ToolMenu.jsx) — shares the Tools section's
    # ToolCard/agent-toolkit-card rendering with Toolkit attachments; see
    # add_mcp() below (ELITEA-1950).
    add_mcp_button = LocatorDescriptor(testid="agent-add-mcp-button")
    # "+ Agent" add button (ToolMenu.jsx) — opens a popper listing other
    # project agents that could be attached as sub-agent tools. Added
    # ELITEA-1887, pushed to automation/testids commit ce74cd40. See
    # open_agent_picker() below.
    add_agent_button = LocatorDescriptor(testid="agent-add-agent-button")
    # "+ Pipeline" add button (ToolMenu.jsx) — opens a popper listing
    # project pipelines that could be attached as sub-agent tools. Added
    # ELITEA-2614 — pre-existing testid on the live app, simply never had a
    # page-object field before this dispatch.
    add_pipeline_button = LocatorDescriptor(testid="agent-add-pipeline-button")
    # Tooltip wrappers for the 4 Tools "+ X" add buttons above — added via
    # `add-data-testid` in the ELITEA-2614 testid-only rework
    # (EliteaAI/EliteaUI@2d05a7f1 on `automation/testids`), mirroring the
    # pre-existing `agent_add_skill_button_tooltip` pattern (SkillMenu.jsx).
    # MUI's `Tooltip` clones its `title` onto `aria-label` on its IMMEDIATE
    # child — here the wrapping `<Box component="span">`, NOT the nested
    # `BaseBtn` that carries the button's own testid above — so a separate
    # testid on the wrapper is the only testid-only way to read the
    # tooltip text (`lockedTooltip` / the "Save the ... first" ternary in
    # `ToolMenu.jsx`). See get_add_toolkit_button_tooltip() etc. below.
    add_toolkit_button_tooltip = LocatorDescriptor(testid="agent-add-toolkit-button-tooltip")
    add_mcp_button_tooltip = LocatorDescriptor(testid="agent-add-mcp-button-tooltip")
    add_agent_button_tooltip = LocatorDescriptor(testid="agent-add-agent-button-tooltip")
    add_pipeline_button_tooltip = LocatorDescriptor(testid="agent-add-pipeline-button-tooltip")
    toolkit_card = LocatorDescriptor(testid="agent-toolkit-card")
    toolkit_delete_button = LocatorDescriptor(testid="agent-toolkit-delete-button")
    toolkit_search_input = LocatorDescriptor(testid="toolkit-search-input")
    toolkit_warning_banner = LocatorDescriptor(testid="credential-warning-banner")
    toolkit_reload_button = LocatorDescriptor(testid="toolkit-reload-button")
    toolkit_open_button = LocatorDescriptor(testid="toolkit-open-button")

    # Agent/Pipeline-type tool card's version selector (ELITEA-1951 — added
    # via add-data-testid to AgentPipelineVersionSelector.jsx; zero
    # data-testid existed on this component before). Dynamic, keyed by
    # `tool.id` (the attached-tool relation id) — same class-constant +
    # `.format()` pattern as VERSION_OPTION/VARIABLE_ROW above. The `_ANY`
    # variants enumerate the trigger/menu when `tool.id` isn't known in
    # advance (this case attaches exactly one Agent-type tool, so `.first`
    # on the ANY selector is unambiguous — same idiom as
    # SKILL_VERSION_OPTION_ANY_SELECTOR).
    AGENT_TOOL_VERSION_SELECTOR_TRIGGER = '[data-testid="agent-tool-version-selector-trigger-{}"]'
    AGENT_TOOL_VERSION_SELECTOR_MENU = '[data-testid="agent-tool-version-selector-menu-{}"]'
    AGENT_TOOL_VERSION_OPTION = '[data-testid="agent-tool-version-option-{}-{}"]'
    AGENT_TOOL_VERSION_SELECTOR_TRIGGER_ANY = '[data-testid^="agent-tool-version-selector-trigger-"]'
    AGENT_TOOL_VERSION_SELECTOR_MENU_ANY = '[data-testid^="agent-tool-version-selector-menu-"]'
    AGENT_TOOL_VERSION_OPTION_ANY = '[data-testid^="agent-tool-version-option-"]'

    # --- Selectors for scoped use (inside parent locators) ---
    # BannerMessage component always uses "credential-warning-banner" testid
    # Distinguish by aria-label content instead
    TOOLKIT_BLOCKED_SELECTOR = '[data-testid="credential-warning-banner"][aria-label*="blocked by your organization"]'
    TOOLKIT_TOOL_BLOCKED_SELECTOR = '[data-testid="credential-warning-banner"][aria-label*="not available anymore"]'
    CHAT_MESSAGE_DELETE_SELECTOR = '[data-testid="chat-message-delete-button"]'
    CHAT_MESSAGE_ITEM_SELECTOR = '[data-testid="chat-message-item"]'
    CHAT_ARTIFACT_FILE_LIST_SELECTOR = '[data-testid="chat-artifact-file-list"]'
    CHAT_ARTIFACT_FILE_CARD_SELECTOR = '[data-testid="chat-artifact-file-card"]'
    CHAT_ANSWER_CONTENT_SELECTOR = '[data-testid="chat-answer-content"]'
    # Outer "Thought for <n> secs" reasoning/tool accordion + its chip-row
    # children (existing testids, ELITEA-2211..2215 batch — same shared
    # ApplicationThinkView.jsx/ActionView.jsx components ChatPage's
    # standalone /chat surface renders through; this page's own scoped
    # string constants per the established CHAT_ANSWER_CONTENT_SELECTOR
    # precedent above, since the embedded chat panel is a distinct DOM
    # scope from ChatPage's LocatorDescriptor fields for the same testids).
    CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR = '[data-testid="chat-answer-thought-accordion"]'
    CHAT_ANSWER_MODEL_CHIP_SELECTOR = '[data-testid="chat-answer-model-chip"]'
    CHAT_ANSWER_TOOL_CHIP_SELECTOR = '[data-testid="chat-answer-tool-chip"]'
    # Nested sub-agent accordion (ELITEA-1951 — added via add-data-testid to
    # SubAgentAccordion.jsx, which previously carried zero data-testid).
    # Dynamic, keyed by the invoked sub-agent's exact name (matches the
    # component's `name` prop, `ApplicationThinkView.jsx`'s
    # `displayName = subEntry?.name || childError?.name || instanceKey`).
    # `_SUMMARY` is the clickable AccordionSummary (reads `aria-expanded`
    # directly, MUI forwards it to the root button element); `_DETAILS`
    # scopes the model/tool chip lookups to THIS nested accordion only,
    # avoiding a collision with the parent's own top-level chips.
    NESTED_AGENT_ACCORDION_SUMMARY = '[data-testid="chat-answer-nested-agent-accordion-summary-{}"]'
    NESTED_AGENT_ACCORDION_DETAILS = '[data-testid="chat-answer-nested-agent-accordion-details-{}"]'
    # Embedded-chat conversation-starter tile (ELITEA-1886) — this page's own
    # call site of the shared EllipsisTextWithTooltip, ChatConversationStarters.jsx,
    # mounted inside the embedded ChatBox on THIS route (/agents/all/{id}). Same
    # literal as ChatPage.CHAT_STARTER_TILE (ELITEA-2369's standalone /chat/{id}
    # landing-view call site, NewConversationView.jsx) by deliberate reuse — the
    # two call sites never render on the same page simultaneously, so there is
    # no collision risk in sharing the testid (AFS ELITEA-1886 Concrete Handles).
    # Static testid, one per rendered tile; select a specific tile via
    # .filter(has_text=...), same idiom as ChatPage.click_chat_starter_tile().
    CHAT_STARTER_TILE = '[data-testid="chat-conversation-starter-tile"]'
    # Agent-only child (TTS read-out button) and its non-last/last-message
    # sibling testid — scoped, per-message-item lookups used by
    # get_last_chat_message_agent_markers() (ELITEA-1885) to distinguish an
    # agent bubble from a user bubble. See CHAT_ANSWER_CONTENT_SELECTOR above
    # for the non-last-message half of the same ternary
    # (`ApplicationAnswer.jsx`'s `isLastMessage ? 'skill-test-last-response'
    # : 'chat-answer-content'`); ``skill_test_last_response`` already exists
    # as a page-level LocatorDescriptor for the common "only message"
    # case, but a scoped string constant is needed here to check its
    # presence within a *specific* message item rather than page-wide.
    CHAT_READ_OUT_BUTTON_SELECTOR = '[data-testid="chat-read-out-button"]'
    SKILL_TEST_LAST_RESPONSE_SELECTOR = '[data-testid="skill-test-last-response"]'
    # Dynamic (runtime-parameterized) testid templates — see
    # .claude/rules/page-objects.md "Dynamic testids" for the naming pattern.
    SKILL_CARD_SELECTOR = '[data-testid="skill-card-{}"]'
    # Prefix-match variant: used when only the skill *name* is known (not the
    # skill_id), to filter all attached-skill cards by rendered name text.
    SKILL_CARD_ANY_SELECTOR = '[data-testid^="skill-card-"]'
    # Static testid (not per-instance dynamic) for the "remove skill" icon
    # button — added via `add-data-testid` for ELITEA-1792 (EliteaUI draft
    # PR #547). Mirrors the shape `remove_toolkit()` uses for the sibling
    # toolkit-card delete button (`[data-testid="agent-toolkit-delete-button"]`
    # scoped via `card.locator(...)`), promoted to a class-level constant per
    # `.claude/rules/page-objects.md` (scoped selectors use UPPER_CASE string
    # constants): scoped within a single skill's card (resolved via
    # `_skill_card()`), so no per-skill dynamic suffix is needed.
    SKILL_CARD_REMOVE_BUTTON_SELECTOR = '[data-testid="skill-card-remove-button"]'
    # Attached-skill SkillCard's custom-icon <img> (ELITEA-2605 — new testid,
    # EliteaAI/EliteaUI@ccc8c001). Same-element-conditional-pair shape as
    # SKILL_MENU_ITEM_ICON_IMG_SELECTOR above — only the `EliteAImage`
    # (custom-icon) branch is tagged, the default `SkillIcon` glyph is not.
    # Scope via ``_skill_card(skill_name).locator(...)``, never page-wide
    # (the testid repeats once per attached-skill card).
    SKILL_CARD_ICON_IMG_SELECTOR = '[data-testid="skill-card-icon-img"]'
    SKILL_MENTION_ITEM_SELECTOR = '[data-testid="skill-mention-item-{}"]'
    # `~`-mention popper row's custom-icon <img> (ELITEA-2605 — new testid,
    # EliteaAI/EliteaUI@ccc8c001, `MentionSkillList.jsx`). Same
    # same-element-conditional-pair shape as SKILL_MENU_ITEM_ICON_IMG_SELECTOR
    # / SKILL_CARD_ICON_IMG_SELECTOR above — only the `EliteAImage`
    # (custom-icon) branch is tagged. Scope via ``.locator()`` off an
    # already name-filtered row from :meth:`get_chat_mention_item`.
    SKILL_MENTION_ITEM_ICON_IMG_SELECTOR = '[data-testid="skill-mention-item-icon-img"]'
    # Version-selector testids (ELITEA-1789 testid-only rework — added via
    # add-data-testid to SkillVersionSelector.jsx; see EliteaUI draft PR #545).
    SKILL_VERSION_TRIGGER_SELECTOR = '[data-testid="skill-version-selector-trigger-{}"]'
    SKILL_VERSION_MENU_SELECTOR = '[data-testid="skill-version-selector-menu-{}"]'
    SKILL_VERSION_OPTION_SELECTOR = '[data-testid="skill-version-option-{}"]'
    # Prefix-match variant: used to enumerate ALL entries in the currently
    # open Versions menu (the per-row testid is keyed by version_name, which
    # isn't known in advance when enumerating) — safe because MUI unmounts
    # MenuItems while their Menu is closed, so only one card's menu items
    # are ever in the DOM at a time.
    SKILL_VERSION_OPTION_ANY_SELECTOR = '[data-testid^="skill-version-option-"]'

    # Shared UnifiedDropdown row testid (SkillMenu.jsx attach popper, same
    # component `Popper.select_menuitem_by_testid` in components/mui.py
    # already targets by raw string) — promoted to a class-level constant
    # here so :meth:`open_skill_menu`/:meth:`get_skill_menu_item` (ELITEA-2605)
    # don't repeat the literal. NOT unique per row (repeats once per
    # dropdown item, same as every other `UnifiedDropdown` consumer) —
    # callers must filter by text/name.
    TOOLKIT_MENU_ITEM_SELECTOR = '[data-testid="toolkit-menu-item"]'
    # SkillMenu dropdown row's custom-icon <img> (ELITEA-2605 — new testid,
    # EliteaAI/EliteaUI@ccc8c001). Same-element-conditional-pair shape: only
    # the custom-icon (`EliteAImage`) branch carries this testid, the
    # default `SkillIcon` glyph branch is untagged (`.agents/testing.md` §
    # Locator policy, "only the used branch is named"). Scope with
    # ``.locator()`` off an already name-filtered row from
    # :meth:`get_skill_menu_item` — never page-wide (the testid repeats
    # once per row).
    SKILL_MENU_ITEM_ICON_IMG_SELECTOR = '[data-testid="skill-menu-item-icon-img"]'

    # --- Sensitive action authorization ---
    sensitive_action_panel = LocatorDescriptor(testid="sensitive-action-panel")
    sensitive_action_authorize_button = LocatorDescriptor(testid="sensitive-action-authorize-button")

    # --- Embedded chat ---
    chat_message_list = LocatorDescriptor(testid="chat-message-list")
    chat_message_item = LocatorDescriptor(testid="chat-message-item")
    chat_message_input = LocatorDescriptor(testid="chat-message-input")
    chat_send_button = LocatorDescriptor(testid="chat-send-button")
    chat_delete_button = LocatorDescriptor(testid="chat-delete-button")
    chat_answer_content = LocatorDescriptor(testid="chat-answer-content")
    chat_artifact_file_list = LocatorDescriptor(testid="chat-artifact-file-list")
    chat_artifact_file_card = LocatorDescriptor(testid="chat-artifact-file-card")
    chat_clear_button = LocatorDescriptor(testid="chat-clear-button")
    skill_test_last_response = LocatorDescriptor(testid="skill-test-last-response")

    # --- Run History panel (ELITEA-1877) ---
    # Opens `RunHistoryContainer`, which REPLACES the Configuration form +
    # embedded chat (not a tab, not an overlay) — see
    # `test-specs/agents/_surface.md` § Run History panel. `pipeline-history-tab`
    # is pre-existing on `main` (shared `ViewRunHistoryButton.jsx`, also used by
    # Pipelines/MCP/Toolkit run history — the name is a naming-precedent smell,
    # not something to fix here); this page-object field is new.
    run_history_open_button = LocatorDescriptor(testid="pipeline-history-tab")
    # `run-history-list-item` / `data-selected` — testid + state attribute
    # added via `add-data-testid` for this case (EliteaUI automation/testids
    # commit a5a9d0f5, RunHistoryListItem.jsx). Same literal testid on every
    # row — rows are positionally distinguished (default sort = Date
    # descending, so index 0 = most recent, index 1 = "not the most recent").
    RUN_HISTORY_LIST_ITEM_SELECTOR = '[data-testid="run-history-list-item"]'
    RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR = (
        '[data-testid="run-history-list-item"][data-selected="true"]'
    )
    # `RunHistoryContainer` accepts an `onClose` prop but never wires it to a
    # rendered element — there is no way to close the panel once opened
    # (filed as EliteaAI/elitea-testing-public#1093, MINOR, doesn't block
    # this case). No "close" locator/method exists on purpose.

    # --- LLM model selector (embedded chat panel, ELITEA-1881) ---
    # `model-selector-button`/`model-selector-name` are static testids on
    # LLMModelSelector.jsx. Each dropdown option carries a DYNAMIC testid
    # keyed by the model's stable API `name` field (e.g.
    # `model-selector-option-eu.anthropic.claude-sonnet-4-5-20250929-v1:0`),
    # added via add-data-testid during the ELITEA-1881 analyst pass
    # (EliteaUI automation/testids commit 0b058c94). Callers select/verify
    # an option by its rendered DISPLAY name (e.g. "Anthropic Claude 4.5
    # Sonnet"), not the API name, so — mirroring
    # SKILL_VERSION_OPTION_ANY_SELECTOR's "keyed by a value not known in
    # advance" precedent — selection filters this prefix-match ANY selector
    # by display text rather than formatting a per-model template.
    model_selector_button = LocatorDescriptor(testid="model-selector-button")
    model_selector_name = LocatorDescriptor(testid="model-selector-name")
    MODEL_SELECTOR_OPTION_ANY_SELECTOR = '[data-testid^="model-selector-option-"]'

    # --- Model Settings (gear) dialog (ELITEA-1880 testid-only rework —
    # added via add-data-testid to LLMModelSelector.jsx (gear button),
    # LLMSettingsDialog.jsx (BaseModal's dataTestId + own Cancel button),
    # MaxTokensSection.jsx (container Box), and ReasoningSlider.jsx (via a
    # new `testId` prop threaded through the SHARED DiscreteSlider.jsx —
    # both ReasoningSlider and CreativitySlider consume DiscreteSlider, so
    # the testid is prop-driven rather than hardcoded in the shared
    # component per `.agents/testing.md` § Locator policy). EliteaUI
    # automation/testids commit ab11bd81. Apply button intentionally has NO
    # testid here — this case only exercises Cancel (see AFS § Concrete
    # Handles: out of scope for THIS case). ---
    model_settings_button = LocatorDescriptor(
        testid="model-settings-button",
        description="Gear icon next to the model selector — opens the Model "
                     "settings dialog",
    )
    model_settings_dialog = LocatorDescriptor(testid="model-settings-dialog")
    model_settings_cancel_button = LocatorDescriptor(testid="model-settings-cancel-button")
    # Reasoning-capable models render this slider (Low/Medium/High); a
    # non-reasoning model renders CreativitySlider instead, which carries no
    # testid (out of scope for this case — see AFS Coverage Map
    # Clarification 1).
    model_settings_reasoning_slider = LocatorDescriptor(testid="model-settings-reasoning-slider")
    # Always rendered regardless of model type (Default/Custom toggle).
    model_settings_max_tokens_section = LocatorDescriptor(testid="model-settings-max-tokens-section")

    # --- Skills section (agent-skills attach/mention flow, ELITEA-1735) ---
    agent_add_skill_button = LocatorDescriptor(testid="agent-add-skill-button")
    # Tooltip wrapper span for the add-skill button (ELITEA-1790 testid-only
    # rework — added via add-data-testid to SkillMenu.jsx; see EliteaUI draft
    # PR #546). MUI's Tooltip clones its accessible label onto this wrapper
    # (not onto the inner, disabled BaseBtn) once the 5-skill limit is
    # reached, so it needs its own testid rather than a raw parent-traversal
    # chained off `agent_add_skill_button`.
    agent_add_skill_button_tooltip = LocatorDescriptor(testid="agent-add-skill-button-tooltip")
    # "Create new" item inside the "+ Skill" dropdown (ELITEA-1999 — added
    # via `add-data-testid`, threading an optional `createNewTestId` prop
    # through UnifiedDropdown.jsx's existing createNewLabel/onCreateNew prop
    # trio; SkillMenu.jsx, the caller for THIS section, supplies the value.
    # Same pattern as ELITEA-2166's `agents-create-new-button`). Navigates to
    # `/skills/create?source_application_id={id}&return_url=...` — see
    # `open_create_new_skill()` below.
    agent_add_skill_create_new_button = LocatorDescriptor(testid="agent-add-skill-create-new-button")
    skills_section = LocatorDescriptor(testid="agent-skills-section")
    skills_counter = LocatorDescriptor(testid="agent-skills-counter")
    skill_mention_list = LocatorDescriptor(testid="skill-mention-list")

    # --- Actions menu ---
    actions_menu_button = LocatorDescriptor(testid="agent-actions-menu-button")
    actions_menu = LocatorDescriptor(testid="agent-actions-menu")
    delete_agent_menuitem = LocatorDescriptor(testid="delete-agent-menuitem")
    # VERSION-group "Export" menuitem (ELITEA-1794 testid-only rework — added
    # via add-data-testid to ExportApplicationButton.jsx's
    # useExportApplicationMenu(); see EliteaUI draft PR #549).
    export_agent_menuitem = LocatorDescriptor(testid="agent-actions-export-menuitem")
    # VERSION-group "Fork" menuitem (ELITEA-1893 testid-only rework — added
    # via add-data-testid: `key: 'agent-actions-fork'` in
    # ForkEntityButton.jsx's useForkEntityMenu(), mirroring the sibling
    # Export menuitem above; see EliteaUI automation/testids commit
    # 61328689). Review R1 fix (commit 5dbc7530): `useForkEntityMenu()` is a
    # SHARED hook also consumed by ToolkitsControls.jsx (Toolkit Fork) and
    # the Pipeline path — the key is now resolved per `entity_name`
    # (`applications` -> `agent-actions-fork`, `toolkits` ->
    # `toolkit-actions-fork`, `pipelines` -> `pipeline-actions-fork`), so
    # this testid value is unchanged for the Agent context but no longer
    # leaks onto Toolkit/Pipeline Fork menuitems.
    fork_menuitem = LocatorDescriptor(testid="agent-actions-fork-menuitem")
    # VERSION-group "Publish"/"Unpublish" menuitems (ELITEA-1892 testid-only
    # rework — added via add-data-testid: `key: 'publish-version'` /
    # `key: 'unpublish-version'` in usePublishVersionMenu.hooks.jsx /
    # useUnpublishVersionMenu.hooks.jsx, same DotMenu `testId: item.key` ->
    # `data-testid={testId}-menuitem` mechanism already backing
    # delete_agent_menuitem/fork_menuitem above. Mutually exclusive per
    # version status: "Publish" renders for a Draft version (canShowPublish),
    # "Unpublish" renders for a Published version (canUnpublish) — never both
    # at once for the same version.
    publish_version_menuitem = LocatorDescriptor(testid="publish-version-menuitem")
    unpublish_version_menuitem = LocatorDescriptor(testid="unpublish-version-menuitem")
    # VERSION-group "Share" menuitem (ELITEA-1898 — pre-existing testid, no
    # EliteaUI change needed). Same `DotMenu.jsx` `testId: item.key` ->
    # `data-testid={testId}-menuitem` mechanism as the menuitems above
    # (`key: 'share-version'` in `ApplicationControls.jsx`'s
    # `useCopyLinkMenu()`). Copies a VERSION-specific link (the URL contains
    # a trailing version-id path segment).
    share_version_menuitem = LocatorDescriptor(testid="share-version-menuitem")
    # AGENT-group "Share" menuitem — SAME mechanism, `key: 'share-agent'`.
    # Copies a generic, version-less agent link (no trailing version-id
    # segment). Kept here as the negative-control target for ELITEA-1898's
    # URL-shape contrast — both items are literally labelled "Share" and are
    # visually identical, so accidentally clicking this one instead of
    # `share_version_menuitem` is a very plausible mistake (AFS Axis 2).
    share_agent_menuitem = LocatorDescriptor(testid="share-agent-menuitem")

    # --- App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared
    # component, testids pre-exist and need no EliteaUI change (same
    # component already used by ChatPage.toast_alert/toast_message and
    # PipelineDetailPage.toast_alert/toast_message; ELITEA-1898 is the first
    # case to need it on the Agent detail page, per existing repo precedent
    # of each page object declaring its own field for this shared
    # component). ---
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )
    # Severity-scoped toast alert selector — testid identity + data-severity
    # state filter, the compliant shape for a state-dependent assertion
    # (mirrors ChatPage.TOAST_ALERT_SEVERITY / PipelineDetailPage.TOAST_ALERT_SEVERITY).
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

    # --- Fork wizard (ELITEA-1893) — shares the ImportWizardModal dialog
    # family with the Agents-list Import flow (AgentsListPage's
    # import_preview_dialog/import_complete_dialog carry the SAME testids;
    # re-declared here because Fork is triggered from the agent-actions
    # menu on THIS page, not from the Agents list toolbar). The dialog
    # container swaps its own testid in place from
    # "agent-import-preview-dialog" (pre-fork) to
    # "agent-import-complete-dialog" (post-fork) — do not assert on a
    # single fixed testid persisting across the fork action. ---
    fork_wizard_dialog = LocatorDescriptor(
        testid="agent-import-preview-dialog",
        description="Fork wizard 'Fork parameters' dialog (pre-fork state)",
    )
    fork_complete_dialog = LocatorDescriptor(
        testid="agent-import-complete-dialog",
        description="Fork wizard 'Fork Complete' dialog (post-fork state — "
                     "same container as fork_wizard_dialog, testid swaps)",
    )
    fork_main_entity_name = LocatorDescriptor(
        testid="agent-import-preview-name",
        description="Fork wizard — Main entity card's name",
    )
    # Every rendered entity-preview card (Main entity + each nested
    # dependency, if any) carries this SAME toggle testid — so its count()
    # is a direct, testid-based proxy for "how many entity cards are
    # showing", used to confirm no "Nested entities" section renders for a
    # dependency-free source agent (AFS Axis 2).
    fork_entity_card_toggle = LocatorDescriptor(
        testid="agent-import-preview-card-toggle",
        description="Fork wizard — 'Show details' toggle, one per rendered "
                     "entity-preview card",
    )
    # Testid corrected in review R1 (ELITEA-1893): the original
    # `agent-fork-project-select` was rendered via a state-conditional
    # `data-testid={isForking ? '...' : '...'}` ternary in IWModalContent.jsx
    # — forbidden per `.agents/testing.md` § Locator policy ("the element
    # keeps ONE testid; state is a separate attribute"). Fixed by giving the
    # SAME ProjectSelect DOM node (shared by both the Import and Fork
    # wizards; `isForking` is a mount-time prop, not per-render-toggled
    # state) a single unconditional testid instead. Declared improvisation:
    # since AgentDetailPage only ever renders this dialog in Fork context
    # (AgentsListPage owns the Import context separately), the shared
    # testid unambiguously resolves the target project selector here — no
    # `data-*` mode filter needed.
    fork_project_select_trigger = LocatorDescriptor(
        testid="agent-import-wizard-project-select",
        description="Fork wizard — target Project selector trigger (shared "
                     "with the Import wizard's own use of the same "
                     "ProjectSelect DOM node — see comment above; EliteaUI "
                     "automation/testids commit 5dbc7530)",
    )
    fork_confirm_button = LocatorDescriptor(
        testid="agent-fork-confirm-button",
        description="Fork wizard — 'Fork' confirm button (added via "
                     "add-data-testid to IWModalForkButton.jsx's "
                     "Button.BaseBtn, mirroring the sibling Import button's "
                     "agent-import-confirm-button; see EliteaUI "
                     "automation/testids commit 61328689)",
    )
    fork_complete_agents_list = LocatorDescriptor(
        testid="agent-import-complete-list-agents",
        description="Fork Complete dialog — forked Agents name list",
    )
    fork_complete_got_it_button = LocatorDescriptor(
        testid="agent-import-complete-got-it-button",
        description="Fork Complete dialog — 'Got it' confirm/navigate button",
    )
    # Dynamic (runtime-parameterized) testid template for the Fork wizard's
    # Project-selector dropdown options — same shared `select-option-{value}`
    # family (SingleSelectMenuItem.jsx) already used by
    # PipelineDetailPage.SELECT_OPTION, keyed by the numeric project id
    # (confirmed live, ELITEA-1893 AFS: select-option-399/400/471).
    FORK_PROJECT_OPTION = '[data-testid="select-option-{}"]'

    # --- Publish wizard (ELITEA-1892) — PublishWizardModal.jsx, non-admin
    # branch only. Case-text drift (CLARIFICATION #612): the TMS case
    # describes a single version-name dialog; the live product is a 3-step
    # wizard (PUBLISH_STEPS = PREPARATION / VALIDATION / PUBLISHING) gated
    # by an AI content-quality check between steps. The dialog container
    # itself carries no dedicated testid (plain MUI [role="dialog"],
    # resolved via components.mui.Dialog) — only its interactive fields do.
    publish_version_name_input = LocatorDescriptor(
        testid="agent-publish-version-name-input",
        description="Publish wizard, Preparation step — version-name input",
    )
    publish_category_select = LocatorDescriptor(
        testid="agent-publish-category-select",
        description="Publish wizard, Preparation step — Category dropdown "
                     "trigger (not named in the case text — a hard "
                     "requirement to enable Continue, see CLARIFICATION #612)",
    )
    publish_agree_checkbox = LocatorDescriptor(
        testid="agent-publish-agree-checkbox",
        description='Publish wizard, Preparation step — "I agree with the '
                     'Publishing Terms" checkbox (not named in the case '
                     "text — a hard requirement to enable Continue)",
    )
    publish_continue_button = LocatorDescriptor(
        testid="agent-publish-continue-button",
        description="Publish wizard, Preparation step — Continue button "
                     "(disabled until name + category + agree-checkbox are "
                     "all filled/checked)",
    )
    publish_confirm_button = LocatorDescriptor(
        testid="agent-publish-confirm-button",
        description="Publish wizard, Validation step — Publish button "
                     "(disabled while the AI publish_validate gate reports "
                     "any Critical issue; canPublish = status !== 'FAIL')",
    )
    publish_error_alert = LocatorDescriptor(
        testid="publish-wizard-error-alert",
        description="Publish wizard — inline error Alert (Validation step), "
                     "renders a rejected publish's error message (agent "
                     "entity: validation_failed — 'modified since "
                     "validation'). Pre-existing testid, added by "
                     "ELITEA-2597's implementer on the shared "
                     "PublishWizardModal.jsx component "
                     "(EliteaAI/EliteaUI@2dafb537, automation/testids); "
                     "confirmed live (ELITEA-2601) to render unmodified for "
                     "the Agent flow — no new testid needed, exposed here "
                     "only because AgentDetailPage never wired it before.",
    )
    publish_terms_content = LocatorDescriptor(
        testid="agent-publish-terms-content",
        description=(
            "Publish wizard, Preparation step — the scrollable Publishing "
            "Terms disclosure text box (PublishingTerms.jsx/TermsContent.jsx, "
            "ELITEA-2600). Contains the platform's documented guarantee that "
            "attached Skills/sub-agents are embedded, not stripped, and are "
            "never independently catalog-listed. Added via add-data-testid "
            "on the shared component's only call site (PreparationStep.jsx), "
            "following that call site's existing agent-publish-* naming even "
            "though the component is entityLabel-shared with the skill-"
            "publish wizard (same pre-existing precedent as its siblings)."
        ),
    )
    # Dynamic (runtime-parameterized) testid for the Publish wizard's
    # Category dropdown options — same shared `select-option-{value}` family
    # (SingleSelectMenuItem.jsx) as FORK_PROJECT_OPTION above, keyed here by
    # the category's display label (e.g. select-option-Quality Assurance)
    # rather than a numeric id.
    PUBLISH_CATEGORY_OPTION = '[data-testid="select-option-{}"]'

    # --- Unpublish confirm dialog (ELITEA-1892) — UnpublishConfirmModal.jsx,
    # non-admin branch (no "Reason" textfield). Heading "Unpublish Agent".
    unpublish_confirm_button = LocatorDescriptor(
        testid="agent-unpublish-confirm-button",
        description='Unpublish confirm dialog — "Unpublish" button',
    )

    # --- "Set as a default" (pin) — ELITEA-1891. Pre-existing via the
    # generic DotMenu `testId: item.key` -> `data-testid={testId}-menuitem`
    # mechanism (same family as delete_agent_menuitem/fork_menuitem above);
    # `aria-disabled="true"` when the currently-viewed version is already
    # the default. ---
    set_as_default_menuitem = LocatorDescriptor(testid="set-as-a-default-menuitem")
    # SetDefaultVersionDialog.jsx's confirm button (ELITEA-1891 testid-only
    # rework — added via add-data-testid: the dialog is a SHARED component
    # (agent + skill "Set as default"), so the testid is wired via a
    # `confirmButtonTestId` prop at THIS page's own call site
    # (useSetDefaultVersion.hooks.jsx), not hardcoded in the shared dialog
    # itself — see EliteaUI automation/testids commit 4e5b819d.
    set_default_version_confirm_button = LocatorDescriptor(
        testid="agent-set-default-version-confirm-button",
        description='"Set as default?" confirm dialog — "Set as a default" button',
    )

    # --- Navigation ---
    back_button = LocatorDescriptor(testid="back-button")

    # --- Icon picker (ELITEA-1899 testid-only rework — added via
    # add-data-testid to EntityIcon.jsx/ApplicationEditForm.jsx/
    # SelectIconDialog.jsx/ProjectIconItem.jsx; see EliteaUI commit
    # 6bb6a23c on automation/testids). `agent_icon_button` is ALSO present
    # on the create-form route (CreateAgentForm.jsx) — both are separate
    # React components sharing this testid string (see this project's
    # dual-component gotcha, `.agents/memory/qa-engineer/
    # agent_form_dual_component_and_icon_picker_quirks.md`). ---
    agent_icon_button = LocatorDescriptor(
        testid="agent-form-icon-button",
        description=(
            "Agent icon avatar/button (opens the icon picker). CRITICAL: "
            "only fires onClick to open the dialog once its hover-triggered "
            "edit-pencil overlay is already mounted — a bare single "
            "`.click()` with no prior `.hover()` only renders the overlay "
            "and does NOT open the dialog (reproduced deterministically "
            "2/2, ELITEA-1899 AFS). Callers must hover() before click()."
        ),
    )
    icon_picker_dialog = LocatorDescriptor(testid="agent-icon-picker-dialog")
    icon_picker_close_button = LocatorDescriptor(testid="agent-icon-picker-close-button")
    icon_picker_default_icon = LocatorDescriptor(testid="agent-icon-picker-default-icon")
    # Inner <img> of agent_icon_button — separate testid (not a raw ".locator
    # img" chain off agent_icon_button) added via add-data-testid to
    # EliteaUI's EliteAImage.jsx/EntityIcon.jsx (ELITEA-1899 review fix-pass;
    # EliteaUI automation/testids commit 558160a6). Only rendered once an
    # icon.url is set — see get_header_icon_src()'s placeholder-SVG quirk.
    agent_icon_img = LocatorDescriptor(
        testid="agent-form-icon-img",
        description="Agent header icon's <img> element (absent until an "
                     "icon.url is set — see get_header_icon_src())",
    )
    # Dynamic (runtime-parameterized) testid templates — same class-constant
    # + `.format()` pattern as VERSION_OPTION / VARIABLE_ROW above.
    ICON_PICKER_OPTION = '[data-testid="agent-icon-picker-option-{}"]'
    ICON_PICKER_UPLOADED = '[data-testid="agent-icon-picker-uploaded-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to agent")
    def navigate(self, agent_id: int):
        """Navigate to a specific agent's detail page and wait until ready.

        Automatically waits for the page to fully load (Information section
        visible and Name field populated). For explicit waiting (e.g., after
        reload), use wait_for_page_load().

        Args:
            agent_id: The numeric agent ID.
        """
        super(AgentDetailPage, self).navigate(f"/agents/all/{agent_id}?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to agent %d and page loaded", agent_id)

    @action("Navigate to agent's Configuration tab (second-tab-safe)")
    def navigate_to_configuration_tab(self, agent_id: int):
        """Navigate directly to the agent's Configuration/Skills panel.

        ELITEA-2601 gotcha, confirmed live: opening a SECOND browser tab on
        a bare ``/agents/all/{id}`` URL (even with ``?viewMode=owner``)
        lands on the Chat tab, not the Configuration/Skills panel — the
        ``destTab=configuration`` query param is REQUIRED to land there
        directly. Added as a sibling of :meth:`navigate` (not a change to
        it) because that method's existing behaviour has real callers
        across the suite that already reach Configuration reliably in a
        SINGLE-tab flow (the default-active-tab difference only manifests
        for a genuinely fresh second tab/page).

        Args:
            agent_id: The numeric agent ID.
        """
        super(AgentDetailPage, self).navigate(
            f"/agents/all/{agent_id}?destTab=configuration&viewMode=owner"
        )
        self.wait_for_page_load()
        logger.info(
            "Navigated to agent %d Configuration tab (second-tab-safe) and page loaded",
            agent_id,
        )

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the agent detail/edit page to fully load.

        Waits for the INFORMATION section (which contains Agent ID) to appear
        and for the Name field to be populated. The MUI form loads the shell
        first and populates fields after the API call returns.
        """
        self.information_section.wait_for(state="visible", timeout=timeout)

        # Wait for the Name input to have a non-empty value
        self.page.wait_for_function(
            """() => {
                const input = document.querySelector('input#name');
                return input && input.value.length > 0;
            }""",
            timeout=timeout,
        )
        logger.info("Agent detail page loaded")

    # ------------------------------------------------------------------
    # Page verification
    # ------------------------------------------------------------------

    def verify_on_detail_page(self, expected_agent_id: int = None):
        """Verify we're on an agent detail page (not create page).

        Args:
            expected_agent_id: Optional agent ID to verify in URL
        """
        url_path = self.page.url
        assert "/agents/all/" in url_path, f"Not on detail page: {url_path}"
        assert "/create" not in url_path, f"Still on create page: {url_path}"

        if expected_agent_id:
            assert f"/{expected_agent_id}" in url_path, (
                f"URL doesn't contain agent ID {expected_agent_id}: {url_path}"
            )

        logger.info(f"Verified on detail page: {url_path}")

    def verify_tabs_visible(self):
        """Verify Configuration and History tabs are visible.

        Uses global timeout (10s) configured in conftest.py.
        """
        self.configuration_tab.wait_for(state="visible")
        self.history_tab.wait_for(state="visible")
        logger.info("Verified tabs are visible")

    # ------------------------------------------------------------------
    # Agent information
    # ------------------------------------------------------------------

    def get_agent_id(self) -> str:
        """Read the Agent ID from the Information section.

        Returns:
            Agent ID as string.
        """
        return self.copy_id_button.text_content().strip()

    def get_version_id(self) -> str:
        """Read the Version ID from the Information section.

        Returns:
            Version ID as string.
        """
        return self.copy_version_id_button.text_content().strip()

    # ------------------------------------------------------------------
    # Version management (Save As Version / VERSION selector, ELITEA-1888)
    # ------------------------------------------------------------------

    @action("Open the Create version dialog")
    def open_save_as_version_dialog(self, timeout: int = 10000):
        """Click "Save As Version" and wait for the "Create version" dialog.

        Uses ``save_as_version_button`` (inherited from AgentFormPage).
        Split from :meth:`confirm_new_version` so callers can assert on
        the dialog's just-opened state (e.g. Save disabled while Name is
        empty) before typing a name.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening the Create version dialog")
        self.save_as_version_button.click()
        Dialog.wait_for(self.page, timeout=timeout)

    @action("Confirm the new agent version")
    def confirm_new_version(self, version_name: str, timeout: int = 10000):
        """Type the version name into the open "Create version" dialog and confirm.

        Call after :meth:`open_save_as_version_dialog`. Types via
        ``press_sequentially`` (MUI/React onChange requirement —
        `.claude/rules/mui-patterns.md`), clicks the dialog's Save button,
        and waits for the dialog to close and for the URL to gain a new
        version-id path segment (mirrors
        ``SkillDetailPage.save_as_version()``'s wait strategy). The app
        also appends a transient ``isFromCreation=true`` query param that
        self-strips once the new version has loaded; this method does not
        assert on it directly.

        Args:
            version_name: Name for the new version (e.g. ``"v2-test"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Confirming new agent version: %r", version_name)
        previous_version_id = self.get_version_id()

        self.create_version_name_input.click()
        self.create_version_name_input.press_sequentially(version_name, delay=50)

        self.create_version_save_button.click()
        Dialog.wait_for_hidden(self.page, timeout=timeout)

        self.page.wait_for_function(
            "prevId => window.location.pathname.split('/').filter(Boolean).pop() !== prevId",
            arg=previous_version_id,
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)

        # The URL's version-id segment updates before the VERSION selector's
        # displayed text re-renders (confirmed live — a race, not a fixed
        # delay: the new version's data loads via a follow-up API call).
        # Poll the trigger's own text rather than sleeping.
        self.page.wait_for_function(
            """name => {
                const el = document.querySelector('[data-testid="agent-version-selector-trigger"]');
                return !!el && el.innerText.trim() === name;
            }""",
            arg=version_name,
            timeout=timeout,
        )
        logger.info(
            "New agent version %r created — URL: %s", version_name, self.page.url
        )

    @action("Save current edits as a new agent version")
    def save_as_version(self, version_name: str, timeout: int = 10000):
        """Click "Save As Version", fill the Name field, and confirm.

        Convenience wrapper combining :meth:`open_save_as_version_dialog`
        and :meth:`confirm_new_version` for callers that don't need to
        assert on the dialog's intermediate state.

        Args:
            version_name: Name for the new version (e.g. ``"v2-test"``).
            timeout: Maximum wait time in milliseconds.
        """
        self.open_save_as_version_dialog(timeout=timeout)
        self.confirm_new_version(version_name, timeout=timeout)

    def get_version_selector_value(self) -> str:
        """Return the currently displayed value of the VERSION selector.

        Returns:
            The version name currently shown on the closed trigger
            (e.g. ``"base"`` or ``"v2-test"``).
        """
        return (self.version_selector_trigger.text_content() or "").strip()

    def open_version_selector(self):
        """Click the VERSION dropdown trigger to open the options list."""
        self.version_selector_trigger.click()

    def is_version_option_visible(self, version_name: str, timeout: int = 5000) -> bool:
        """Check whether a version is present in the open VERSION dropdown.

        LOCATOR: dynamic ``version-option-{version_name}`` testid (see
        ``VERSION_OPTION`` above) — call after ``open_version_selector()``.

        Args:
            version_name: Exact version name (e.g. ``"base"``).
            timeout: Maximum wait time in milliseconds.
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        try:
            option.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_version_option_active(self, version_name: str) -> bool:
        """Check whether a version option is the currently active/selected one.

        Reads the MUI-rendered ``aria-selected`` attribute on the
        ``version-option-{version_name}`` option (confirmed live —
        ``aria-selected="true"`` on the option matching the current
        version, ``"false"`` on the others). Call after
        ``open_version_selector()``.

        Args:
            version_name: Exact version name (e.g. ``"v2-test"``).
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        return option.get_attribute("aria-selected") == "true"

    def get_version_option_text(self, version_name: str) -> str:
        """Return a version option's own rendered text, e.g.
        ``"v2-published - 01.08.2026"`` (name + date baked into one text
        node — see ``VERSION_OPTION`` above; ELITEA-1891).

        LOCATOR: dynamic ``version-option-{version_name}`` testid. Call
        after ``open_version_selector()``.

        Args:
            version_name: Exact version name (e.g. ``"v2-published"``).
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        return (option.text_content() or "").strip()

    def is_version_option_pinned(self, version_name: str) -> bool:
        """Check whether a version option in the open VERSION dropdown shows
        the pin icon (i.e. it is the agent's default/pinned version).

        LOCATOR: scoped sub-selector chained off the already-testid'd
        ``VERSION_OPTION.format(version_name)`` parent — see
        ``VERSION_OPTION_PIN_ICON`` above. Call after
        ``open_version_selector()``.

        Args:
            version_name: Exact version name (e.g. ``"base"``).
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        return option.locator(self.VERSION_OPTION_PIN_ICON).count() > 0

    def get_version_option_order(self, timeout: int = 5000) -> list[str]:
        """Return the VERSION dropdown's option names, in DOM (visual) order.

        LOCATOR: ``VERSION_OPTION_ANY`` (excludes the nested pin-icon
        testid, which also starts with the ``version-option-`` prefix, so
        it is never mistaken for an option itself). Reads each matched
        element's own ``data-testid`` attribute and strips
        the ``version-option-`` prefix — mirrors the live probes this case's
        AFS used. Call after ``open_version_selector()``.

        Args:
            timeout: Maximum wait time in milliseconds for the first option.

        Returns:
            Version names in the order they're rendered, e.g.
            ``["v1-early-draft", "v3-latest-draft", "v2-published", "base"]``.
        """
        options = self.page.locator(self.VERSION_OPTION_ANY)
        options.first.wait_for(state="visible", timeout=timeout)
        count = options.count()
        prefix = "version-option-"
        names: list[str] = []
        for i in range(count):
            testid = options.nth(i).get_attribute("data-testid") or ""
            names.append(testid[len(prefix):] if testid.startswith(prefix) else testid)
        return names

    # ------------------------------------------------------------------
    # Icon picker (ELITEA-1899)
    # ------------------------------------------------------------------

    @action("Open the icon picker dialog")
    def open_icon_picker(self, timeout: int = 10000):
        """Open the agent icon picker dialog.

        LOCATOR: ``agent-form-icon-button`` (see field docstring above).
        Must ``hover()`` immediately before ``click()`` — the icon's
        clickable state only mounts once its hover-triggered edit-pencil
        overlay is rendered; a bare single ``.click()`` with no prior
        ``.hover()`` merely triggers the hover state and does not open the
        dialog (confirmed live, ELITEA-1899 AFS Automation Hints — real
        users are unaffected since mouse movement naturally precedes a
        real click).

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening the agent icon picker dialog")
        self.agent_icon_button.scroll_into_view_if_needed()
        self.agent_icon_button.hover()
        self.agent_icon_button.click()
        self.icon_picker_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Icon picker dialog opened")

    @action("Select a default icon option")
    def select_icon_option(self, index: int, timeout: int = 10000) -> str:
        """Select a "Default" icon option by index and return its resulting src.

        LOCATOR: dynamic ``agent-icon-picker-option-{index}`` testid (see
        ``ICON_PICKER_OPTION`` above). Selecting closes the dialog
        immediately and persists via its own ``PUT
        .../upload_icon/prompt_lib/{project}/{versionId}`` call — decoupled
        from the agent form's Save/Discard state (ELITEA-1899 AFS).

        Args:
            index: 0-based index of the default icon option to select.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The header icon's ``img.src`` value after the dialog closes.
        """
        logger.info("Selecting icon picker option index=%d", index)
        option = self.page.locator(self.ICON_PICKER_OPTION.format(index))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.icon_picker_dialog.wait_for(state="hidden", timeout=timeout)
        self.wait_for_network(timeout=timeout)
        src = self.get_header_icon_src(timeout=timeout)
        logger.info("Icon option %d selected — header icon src: %s", index, src)
        return src

    def get_header_icon_src(self, timeout: int = 10000) -> str:
        """Return the ``src`` of the agent header icon's ``<img>`` element.

        LOCATOR: ``agent-form-icon-img`` (see field docstring above) — its
        own testid, not a raw tag chained off ``agent_icon_button``. A
        freshly-created agent with no icon explicitly selected yet renders
        an inline SVG placeholder (no ``<img>`` at all) instead — confirmed
        live against a fresh agent — so this returns ``""`` in that case
        rather than timing out.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.agent_icon_button.wait_for(state="visible", timeout=timeout)
        try:
            self.agent_icon_img.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        return self.agent_icon_img.get_attribute("src") or ""

    # ------------------------------------------------------------------
    # Variables section (derived live from Instructions text, ELITEA-1884)
    # ------------------------------------------------------------------

    def is_variables_section_visible(self, timeout: int = 5000) -> bool:
        """Return True if the "Variables" accordion section is rendered.

        LOCATOR: ``agent-variables-section`` testid. `ApplicationVariables.jsx`
        returns ``null`` (the section entirely absent from the DOM, not just
        empty/collapsed) whenever the current Instructions text contains zero
        ``{{name}}`` references — confirmed live in the ELITEA-1884 analyst
        run. Callers checking for absence should expect this to return
        ``False`` promptly (no long timeout needed) rather than waiting out
        a full default timeout for a node that will never appear.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.variables_section.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_variable_row_visible(self, variable_name: str, timeout: int = 5000) -> bool:
        """Return True if a variable row for *variable_name* is rendered.

        LOCATOR: dynamic ``agent-variable-row-{variable_name}`` testid (see
        ``VARIABLE_ROW`` above). The Variables list is derived live from the
        Instructions textarea via regex parsing — no save/reload is required
        for a row to appear or disappear after editing Instructions.

        Args:
            variable_name: Exact variable name (e.g. ``"tone"``).
            timeout: Maximum wait time in milliseconds.
        """
        row = self.page.locator(self.VARIABLE_ROW.format(variable_name))
        try:
            row.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_variable_row_hidden(self, variable_name: str, timeout: int = 5000):
        """Wait until the variable row for *variable_name* is absent/hidden.

        Use this (rather than a bare negative ``is_variable_row_visible``
        check) right after editing Instructions to remove a ``{{name}}``
        reference — the row's disappearance is instant/client-side (derived
        re-render off the Instructions textarea, no round-trip), but this
        still avoids a race against React's render cycle.

        Args:
            variable_name: Exact variable name (e.g. ``"department"``).
            timeout: Maximum wait time in milliseconds.
        """
        row = self.page.locator(self.VARIABLE_ROW.format(variable_name))
        row.wait_for(state="hidden", timeout=timeout)

    def get_variable_row_names(self, timeout: int = 5000) -> list[str]:
        """Return variable names in the order their rows render in the DOM.

        LOCATOR: ``VARIABLE_ROW_ANY_SELECTOR`` prefix-match, read back via
        each row's own ``data-testid`` attribute. DOM order mirrors
        first-appearance order of each ``{{name}}`` reference in the
        Instructions text (confirmed live, ELITEA-1884 AFS Axis 2).

        Args:
            timeout: Maximum wait time in milliseconds for the section itself.
        """
        self.variables_section.wait_for(state="visible", timeout=timeout)
        rows = self.page.locator(self.VARIABLE_ROW_ANY_SELECTOR)
        names = []
        for i in range(rows.count()):
            testid = rows.nth(i).get_attribute("data-testid") or ""
            if testid.startswith("agent-variable-row-"):
                names.append(testid[len("agent-variable-row-"):])
        return names

    @action("Fill variable value")
    def fill_variable_value(self, variable_name: str, value: str, timeout: int = 5000):
        """Type a value into a variable's value input.

        LOCATOR: dynamic ``agent-variable-input-{variable_name}`` testid (see
        ``VARIABLE_INPUT`` above). Confirmed live (ELITEA-1883) that both
        ``.fill()`` (direct DOM value set) and ``press_sequentially()``
        round-trip correctly through Save for this field — unlike
        ``instructions_input``, which requires keyboard events for React
        ``onChange`` (`.claude/rules/mui-patterns.md`). Uses ``click()`` +
        ``press_sequentially()`` per the project's MUI convention, for
        consistency with other form fields in this codebase.

        Args:
            variable_name: Exact variable name (e.g. ``"MY_VAR"``).
            value: Value to type into the input.
            timeout: Maximum wait time in milliseconds.
        """
        field = self.page.locator(self.VARIABLE_INPUT.format(variable_name))
        field.wait_for(state="visible", timeout=timeout)
        field.click()
        field.press_sequentially(value, delay=30)
        logger.info("Filled variable '%s' value: %r", variable_name, value)

    def get_variable_value(self, variable_name: str, timeout: int = 5000) -> str:
        """Return the current DOM value of a variable's value input.

        LOCATOR: dynamic ``agent-variable-input-{variable_name}`` testid (see
        ``VARIABLE_INPUT`` above).

        Args:
            variable_name: Exact variable name (e.g. ``"MY_VAR"``).
            timeout: Maximum wait time in milliseconds.
        """
        field = self.page.locator(self.VARIABLE_INPUT.format(variable_name))
        field.wait_for(state="visible", timeout=timeout)
        return field.input_value()

    # ------------------------------------------------------------------
    # Internal tools (switches)
    # ------------------------------------------------------------------

    def _get_tool_switch_locator(self, tool: InternalTool) -> Locator:
        """Get locator for an internal tool switch.

        Uses a robust strategy:
        1. Try data-testid if available (future-proof)
        2. Fall back to text-based locator with parent traversal

        Args:
            tool: The internal tool enum value.

        Returns:
            Locator for the tool's switch/checkbox element.
        """
        testid = get_tool_testid(tool)

        # Try testid first (future-proof when frontend adds data-testid)
        testid_locator = self.page.get_by_test_id(testid)
        if testid_locator.count() > 0:
            return testid_locator.first

        # Fallback: text-based locator
        # Strategy: Find text label, go to parent container, find switch within
        tool_label = self.page.locator(f'text="{tool.value}"').first

        # Try to find parent MUI FormControlLabel
        try:
            # Navigate up to find the FormControlLabel container
            container = tool_label.locator('xpath=ancestor::label[contains(@class, "MuiFormControlLabel")]').first
            if container.count() == 0:
                # Try broader search
                container = tool_label.locator('xpath=ancestor::div[contains(@class, "MuiFormControlLabel")]').first

            # Find the switch input within the container
            switch = container.locator('input[type="checkbox"], input[role="switch"]').first
            return switch
        except Exception:
            # Last resort: find any nearby switch
            return self.page.locator(f'text="{tool.value}"').locator('..').locator('input[type="checkbox"]').first

    def _get_tool_label_locator(self, tool: InternalTool) -> Locator:
        """Get locator for an internal tool's clickable label area.

        Args:
            tool: The internal tool enum value.

        Returns:
            Locator for the tool's label (for clicking to toggle).
        """
        # Strategy 1: Try to find within Toolkits section for better specificity
        # This prevents matching unrelated text elsewhere on the page
        toolkits_section = self.page.locator('div:has(> button:has-text("Toolkits"))')

        # Try MUI FormControlLabel within toolkits section
        mui_label = toolkits_section.locator(f'div.MuiFormControlLabel-root:has-text("{tool.value}")')
        if mui_label.count() > 0:
            return mui_label.first

        # Try generic label within toolkits section
        label = toolkits_section.locator(f'label:has-text("{tool.value}")')
        if label.count() > 0:
            return label.first

        # Fallback: text locator within toolkits section
        text_loc = toolkits_section.locator(f'text="{tool.value}"')
        if text_loc.count() > 0:
            return text_loc.first

        # Last resort: page-wide search
        return self.page.locator(f'text="{tool.value}"').first

    def is_tool_enabled(self, tool: InternalTool) -> bool:
        """Check if an internal tool switch is checked.

        Args:
            tool: The internal tool enum value (e.g. InternalTool.SMART_TOOLS).

        Returns:
            True if tool is enabled, False otherwise.

        Example:
            >>> from pages.internal_tools import InternalTool
            >>> detail_page.is_tool_enabled(InternalTool.PYTHON_SANDBOX)
            True
        """
        try:
            # Try to find the checkbox near the tool text
            # Use multiple strategies since MUI structure can vary

            # Strategy 1: Direct sibling or parent search
            text_loc = self.page.locator(f'text="{tool.value}"').first

            # Try finding checkbox in parent container
            try:
                switch = text_loc.locator('xpath=ancestor::*[1]').locator('input[type="checkbox"]').first
                if switch.count() > 0:
                    return switch.is_checked(timeout=1000)
            except Exception:
                pass

            # Strategy 2: Look for checkbox near the text (within 2 parent levels)
            try:
                switch = text_loc.locator('xpath=ancestor::*[2]').locator('input[type="checkbox"]').first
                if switch.count() > 0:
                    return switch.is_checked(timeout=1000)
            except Exception:
                pass

            # Strategy 3: Use CSS selector to find nearby switch
            try:
                # Find any checkbox that's a sibling or in nearby container
                container = self.page.locator(f':has-text("{tool.value}")').locator('input[type="checkbox"]').first
                return container.is_checked(timeout=1000)
            except Exception:
                pass

            logger.warning("Could not find checkbox for tool: %s", tool.value)
            return False

        except Exception as e:
            logger.warning("Failed to check if tool %s is enabled: %s", tool.value, e)
            return False

    @action("Toggle internal tool")
    def toggle_tool(self, tool: InternalTool, wait_for_update: bool = True, timeout: int = 2000):
        """Toggle an internal tool switch by clicking its label area.

        Args:
            tool: The internal tool enum value (e.g. InternalTool.SMART_TOOLS).
            wait_for_update: Wait for UI to update after toggle
            timeout: Maximum wait time in ms

        Example:
            >>> from pages.internal_tools import InternalTool
            >>> detail_page.toggle_tool(InternalTool.PYTHON_SANDBOX)
        """
        logger.info("Toggling tool: %s", tool.value)

        # Ensure toolkits section is visible and scrolled into view
        self.ensure_toolkits_section_visible()
        self.page.wait_for_timeout(500)  # Let scroll animation complete

        # Find the tool using the proper locator method
        tool_locator = self._get_tool_label_locator(tool)
        tool_locator.wait_for(state="visible", timeout=timeout)
        tool_locator.click(force=True)

        if wait_for_update:
            self.page.wait_for_timeout(1000)  # UI animation
            self.wait_for_network(timeout=1000)

        logger.info(f"Toggled tool: {tool.value}")

    @action("Enable internal tool")
    def enable_tool(self, tool: InternalTool):
        """Enable an internal tool if it's not already enabled.

        Args:
            tool: The internal tool enum value.
        """
        if not self.is_tool_enabled(tool):
            self.toggle_tool(tool)
            logger.info("Enabled tool: %s", tool.value)

    @action("Disable internal tool")
    def disable_tool(self, tool: InternalTool):
        """Disable an internal tool if it's currently enabled.

        Args:
            tool: The internal tool enum value.
        """
        if self.is_tool_enabled(tool):
            self.toggle_tool(tool)
            logger.info("Disabled tool: %s", tool.value)

    def ensure_toolkits_section_visible(self, timeout: int = 5000):
        """Scroll to toolkits section and wait for it to be visible.

        Automatically scrolls to the Toolkits section and waits for
        it to be visible with animation settle time.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.toolkits_section.scroll_into_view_if_needed()
        self.toolkits_section.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(500)  # Animation settle
        logger.debug("Toolkits section scrolled into view")

    def get_available_tools(self) -> list[InternalTool]:
        """Get list of internal tools that are visible on the page.

        Automatically scrolls to the Toolkits section if needed.
        Only looks for tools within the Toolkits section to avoid false positives
        from text appearing elsewhere on the page.

        Returns:
            List of InternalTool enum values for tools present in the UI.

        Example:
            >>> tools = detail_page.get_available_tools()
            >>> assert InternalTool.PYTHON_SANDBOX in tools
        """
        # Ensure toolkits section is visible
        self.ensure_toolkits_section_visible()

        available = []

        for tool in InternalTool:
            try:
                # Look for the tool text on the page
                text_locator = self.page.locator(f'text="{tool.value}"')

                if text_locator.count() > 0:
                    first_match = text_locator.first

                    # Check if it's visible
                    if not first_match.is_visible(timeout=1000):
                        continue

                    # Check if it's in a reasonable Y position (below 500px)
                    # to filter out text in headers/banners
                    try:
                        box = first_match.bounding_box()
                        if box and box['y'] > 500:  # Likely in content area, not header
                            available.append(tool)
                    except Exception:
                        # If we can't get bounding box, include it anyway
                        available.append(tool)

            except Exception as e:
                logger.debug("Tool %s not found: %s", tool.value, e)
                continue

        logger.info("Available tools: %s", [t.value for t in available])
        return available

    # ------------------------------------------------------------------
    # External toolkit management
    # ------------------------------------------------------------------

    @action("Add toolkit")
    def add_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Add an external toolkit to the agent via the Toolkits section.

        Scrolls to the Toolkits section, clicks the "+ Toolkit" button,
        searches for the toolkit in the popper dropdown, and selects it.

        Note: The popper dropdown displays toolkit names with spaces removed
        (e.g. "My Toolkit" → "MyToolkit"), so the match is done against
        the space-stripped name.

        Args:
            toolkit_name: Name (or prefix) of the toolkit to add.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Adding toolkit '%s' to agent", toolkit_name)

        # Ensure the Toolkits section is expanded and visible
        self.ensure_toolkits_section_visible(timeout=timeout)

        # Click the "+ Toolkit" button to open dropdown
        self.add_toolkit_button.wait_for(state="visible", timeout=timeout)
        self.add_toolkit_button.click(force=True)
        self.page.wait_for_timeout(1000)

        # Wait for the popper to appear and search for the toolkit
        popper = Popper.wait_for(self.page, timeout=timeout)

        # Use the search input
        search_input = popper.locator(f'[data-testid="toolkit-search-input"]')
        if search_input.count() > 0 and search_input.is_visible():
            Popper.search(popper, toolkit_name[:20], self.page)

        # The dropdown strips spaces from names, so match against the
        # space-stripped version of the toolkit name
        name_no_spaces = toolkit_name.replace(" ", "")
        Popper.select_menuitem(popper, name_no_spaces, self.page, timeout=timeout)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Toolkit '%s' added to agent", toolkit_name)

    @action("Add MCP")
    def add_mcp(self, mcp_name: str, timeout: int = 10000):
        """Attach a Remote MCP to the agent via the Tools section "+ MCP" button.

        Mirrors :meth:`add_toolkit` — the "+ MCP" button (`agent-add-mcp-button`,
        `ToolMenu.jsx`) opens the same shared `UnifiedDropdown` popper component
        as the Toolkit/Skill/Agent/Pipeline add buttons (confirmed: the popper's
        search input carries the same `toolkit-search-input` testid and menu
        items the same `toolkit-menu-item` testid regardless of entity type —
        `UnifiedDropdown.jsx` renders it unconditionally). Unlike the Toolkit
        popper, MCP names are rendered **without** space-stripping, so the
        match is done against the exact name (ELITEA-1950 AFS § Concrete
        Handles). Attaching is an immediate API-level auto-save
        (`PATCH .../tool/prompt_lib/{project}/{tool_id}` -> 201, mirroring
        `attach_skill()`); the agent-level Save button stays disabled and is
        not clicked. The resulting card and its removal flow are identical to
        `add_toolkit()` / `remove_toolkit()` / `is_toolkit_attached()` — MCP
        and Toolkit cards share the same `ToolCard.jsx` component and
        `agent-toolkit-card` / `agent-toolkit-delete-button` testids, so no
        MCP-specific card/removal methods are needed.

        Args:
            mcp_name: Exact name of the MCP to attach.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Adding MCP '%s' to agent", mcp_name)

        # Ensure the Tools section is expanded and visible
        self.ensure_toolkits_section_visible(timeout=timeout)

        # Click the "+ MCP" button to open the popper
        self.add_mcp_button.wait_for(state="visible", timeout=timeout)
        self.add_mcp_button.click(force=True)
        self.page.wait_for_timeout(1000)

        # Wait for the popper to appear and search for the MCP
        popper = Popper.wait_for(self.page, timeout=timeout)

        search_input = popper.locator('[data-testid="toolkit-search-input"]')
        if search_input.count() > 0 and search_input.is_visible():
            Popper.search(popper, mcp_name[:20], self.page)

        # MCP names are NOT space-stripped in the popper (unlike Toolkit),
        # so match against the exact name.
        Popper.select_menuitem(popper, mcp_name, self.page, timeout=timeout)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("MCP '%s' added to agent", mcp_name)

    @action("Open agent picker")
    def open_agent_picker(self, timeout: int = 10000) -> Locator:
        """Open the Tools section's "+ Agent" picker popper (ELITEA-1887).

        Mirrors :meth:`add_toolkit` / :meth:`add_mcp`'s click-then-wait-for-
        popper pattern, but deliberately does NOT select anything — this
        picker is used to inspect which agents it lists (self-attachment
        exclusion check), never to attach.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator of the visible MUI popper (see ``components.mui.Popper``).
        """
        logger.info("Opening agent picker")
        self.ensure_toolkits_section_visible(timeout=timeout)
        self.add_agent_button.wait_for(state="visible", timeout=timeout)
        self.add_agent_button.click(force=True)
        self.page.wait_for_timeout(1000)
        return Popper.wait_for(self.page, timeout=timeout)

    @action("Search agent picker")
    def search_agent_picker(self, popper: Locator, query: str, settle_ms: int = 1000):
        """Type *query* into the agent picker's search input (ELITEA-1887).

        Reuses the shared ``toolkit-search-input`` testid — the same
        ``UnifiedDropdown`` popper component family as the Toolkit/MCP/Skill
        pickers renders it unconditionally regardless of entity type.

        Args:
            popper: Locator of the popper element (from :meth:`open_agent_picker`).
            query: Text to type into the search field.
            settle_ms: Milliseconds to wait after typing for the debounced
                search request to fire (server-side debounce is 200ms).
        """
        Popper.search(popper, query, self.page, settle_ms=settle_ms)

    def get_agent_picker_menuitem(self, popper: Locator, agent_name: str) -> Locator:
        """Return the picker's menuitem locator for *agent_name*, scoped to *popper*.

        The picker's dynamically-named list items carry no per-item testid
        (same established pattern as :meth:`components.mui.Popper.select_menuitem`'s
        targets), so matching is by exact accessible name via ``role="menuitem"``.
        The returned locator may resolve to zero elements — that's the
        expected/asserted state for ELITEA-1887 (self-attachment blocked):
        the backend does NOT filter the current agent out of its own search
        results (confirmed via network capture — the API response includes
        the self-agent row); self-exclusion is enforced entirely
        client-side (``ToolMenu.jsx:401``). Callers must assert DOM-level
        menu-item absence via this locator, never network-response
        emptiness.

        Args:
            popper: Locator of the popper element.
            agent_name: Exact agent name to look for.

        Returns:
            Locator scoped to the matching menuitem (may be empty/hidden).
        """
        return popper.get_by_role("menuitem", name=agent_name, exact=True)

    @action("Attach agent")
    def attach_agent(self, agent_name: str, timeout: int = 10000):
        """Attach another Agent as a sub-agent tool via the Tools section's
        "+ Agent" picker (ELITEA-1902).

        Mirrors :meth:`add_toolkit` / :meth:`add_mcp`'s shape, but wraps
        :meth:`open_agent_picker` + ``Popper.select_menuitem`` instead of
        duplicating the click-then-wait-for-popper sequence — the picker
        itself already existed (ELITEA-1887, self-attachment exclusion
        check) with no attach convenience method on top of it. The attach
        auto-persists (agent-level Save button stays disabled/returns to
        disabled immediately after the picker selection resolves), same
        auto-persist behavior already documented for `add_toolkit()` /
        `add_mcp()`. The resulting card renders via the shared
        ``agent-toolkit-card`` testid (confirmed design — see the
        `toolkit_card` field's docstring above), so no dedicated
        sub-agent-card/removal methods are needed; reuse
        :meth:`is_toolkit_attached` / :meth:`remove_toolkit`.

        Args:
            agent_name: Exact name of the Agent to attach as a sub-agent tool.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Attaching agent '%s' as a sub-agent tool", agent_name)
        popper = self.open_agent_picker(timeout=timeout)
        Popper.select_menuitem(popper, agent_name, self.page, timeout=timeout)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Agent '%s' attached as a sub-agent tool", agent_name)

    @action("Attach agent (testid-scoped selection)")
    def attach_agent_by_testid(self, agent_name: str, timeout: int = 10000):
        """Attach another Agent as a sub-agent tool, selecting it via the
        ``toolkit-menu-item`` testid instead of :meth:`attach_agent`'s raw
        ``li[role="menuitem"]:has-text(...)`` CSS selection (ELITEA-1951).

        Additive sibling to :meth:`attach_agent` — added because
        :meth:`attach_agent` (via ``Popper.select_menuitem``) was found, during
        this case's implementation, to intermittently fail on a real Playwright
        mouse-simulated ``.click()``: the item visibly highlights (hover state)
        and its overflow tooltip (``TypographyWithConditionalTooltip``, shown
        for a truncated agent name) renders, but the click never reaches the
        underlying ``<li>`` — no attach request fires (or the backend rejects
        a stale reference) and the popper never closes. A raw JS
        ``element.click()`` and a testid-scoped Playwright ``.click()`` both
        landed reliably in the SAME scenario, so the likely cause is a MUI
        Tooltip-portal overlay intercepting the mouse-simulated click's
        computed coordinates specifically when the tooltip is showing — not
        reproducible via a role-based or testid-scoped locator in the same
        live testing. ``Popper.select_menuitem`` itself is NOT modified — it
        has other merged callers relying on its current behavior unchanged
        (`.claude/rules/page-objects.md` § shared-caller files); this method
        mirrors :meth:`Popper.select_menuitem_by_testid`'s existing (ELITEA-1735)
        testid-scoped pattern instead, applied here to the Agent picker (whose
        items already carry ``toolkit-menu-item`` via the shared
        ``UnifiedDropdown`` component, confirmed live — no new testid needed).

        Args:
            agent_name: Exact name of the Agent to attach as a sub-agent tool.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Attaching agent '%s' as a sub-agent tool (testid-scoped)", agent_name)
        popper = self.open_agent_picker(timeout=timeout)
        Popper.select_menuitem_by_testid(popper, agent_name, self.page, timeout=timeout)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Agent '%s' attached as a sub-agent tool (testid-scoped)", agent_name)

    def is_toolkit_attached(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check whether a toolkit is attached to the agent.

        Toolkit cards may display the name with or without spaces, so
        both variants are checked.

        Args:
            toolkit_name: Toolkit name to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if toolkit is attached, False otherwise.
        """
        try:
            self.toolkit_card.filter(has_text=toolkit_name).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    @action("Open tool version selector")
    def open_tool_version_selector(self, timeout: int = 10000) -> Locator:
        """Open the version selector menu on the (single) attached
        Agent/Pipeline-type tool card (ELITEA-1951).

        Assumes exactly one Agent/Pipeline-type tool is attached — this
        case's flow — so the `_ANY`-suffixed trigger selector's `.first` is
        unambiguous (`tool.id` isn't known client-side in advance; same
        idiom as ``SKILL_VERSION_OPTION_ANY_SELECTOR``).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator of the opened version-selector menu (scoped via
            ``AGENT_TOOL_VERSION_SELECTOR_MENU_ANY``).
        """
        trigger = self.page.locator(self.AGENT_TOOL_VERSION_SELECTOR_TRIGGER_ANY).first
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()
        menu = self.page.locator(self.AGENT_TOOL_VERSION_SELECTOR_MENU_ANY).first
        menu.wait_for(state="visible", timeout=timeout)
        return menu

    def get_tool_version_selector_trigger_text(self, timeout: int = 10000) -> str:
        """Return the (single) attached tool card's version-selector trigger text.

        E.g. "base" for a sub-agent whose only version is "base".
        """
        trigger = self.page.locator(self.AGENT_TOOL_VERSION_SELECTOR_TRIGGER_ANY).first
        trigger.wait_for(state="visible", timeout=timeout)
        return (trigger.text_content() or "").strip()

    def get_tool_version_option_texts(self, timeout: int = 10000) -> list[str]:
        """Return the text of every option row in the (already-open) version menu."""
        options = self.page.locator(self.AGENT_TOOL_VERSION_OPTION_ANY)
        options.first.wait_for(state="visible", timeout=timeout)
        return [(options.nth(i).text_content() or "").strip() for i in range(options.count())]

    @action("Remove toolkit")
    def remove_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Remove a toolkit from the agent configuration.

        Hovers over the toolkit card to reveal the hidden delete button (CSS
        hover on cardHeader), clicks the delete button, confirms the dialog,
        and then waits until the toolkit card has actually disappeared from the
        DOM before returning.

        Args:
            toolkit_name: Name of the toolkit to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing toolkit '%s' from agent", toolkit_name)

        # Find the toolkit card scoped to the toolkit name
        card = self.toolkit_card.filter(has_text=toolkit_name).first
        card.wait_for(state="visible", timeout=timeout)
        card.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)

        # Hover the card to reveal the delete button (CSS hover rule)
        card.hover()
        self.page.wait_for_timeout(500)

        # Locate the delete button inside this specific card
        delete_btn = card.locator('[data-testid="agent-toolkit-delete-button"]').first
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle the "Remove toolkit?" confirmation dialog.
        dialog = Dialog.wait_for(self.page)
        Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")

        # Wait for network idle so the PATCH disassociate request completes
        # and any follow-up refetches settle.
        self.wait_for_network(timeout=timeout)

        # Explicitly wait for the toolkit card to disappear from the DOM.
        # This is necessary because React may defer state updates and re-renders
        # asynchronously after the network request completes, which can cause
        # is_toolkit_attached() to still find the card.  A 10-second timeout
        # gives React ample time to propagate the Formik state change.
        try:
            card.wait_for(state="hidden", timeout=10000)
        except Exception:
            # If the card is already gone, that's fine.
            pass

        logger.info("Toolkit '%s' removed from agent", toolkit_name)

    @action("Remove MCP")
    def remove_mcp(self, mcp_name: str, timeout: int = 10000):
        """Remove an attached MCP from the agent configuration.

        Additive sibling to :meth:`remove_toolkit` for the MCP card case —
        `remove_toolkit()` itself is NOT modified, it has other merged
        callers relying on its behavior unchanged (page-objects shared-caller
        rule). The only difference from `remove_toolkit()`: the confirmation
        dialog is located via `Dialog.wait_for_visible()` instead of
        `Dialog.wait_for()`. An unauthenticated MCP card renders a
        `McpAuthModal` (`keepMounted`, per its "Log in" button) that stays in
        the DOM hidden even when closed; plain `Dialog.wait_for()`'s
        `.first` can bind to that permanently-hidden dialog instead of the
        "Remove MCP?" confirmation that actually opens, and time out even
        though the real dialog is visible on screen (confirmed live,
        ELITEA-1950). Everything else — card lookup, hover-reveal delete
        icon, disappearance wait — is identical, since MCP and Toolkit cards
        share the same `ToolCard.jsx` component and testids.

        Args:
            mcp_name: Name of the MCP to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing MCP '%s' from agent", mcp_name)

        card = self.toolkit_card.filter(has_text=mcp_name).first
        card.wait_for(state="visible", timeout=timeout)
        card.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)

        card.hover()
        self.page.wait_for_timeout(500)

        delete_btn = card.locator('[data-testid="agent-toolkit-delete-button"]').first
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle the "Remove MCP?" confirmation dialog — scoped to the
        # actually-visible dialog (see docstring: McpAuthModal quirk).
        dialog = Dialog.wait_for_visible(self.page)
        Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")

        self.wait_for_network(timeout=timeout)

        try:
            card.wait_for(state="hidden", timeout=10000)
        except Exception:
            pass

        logger.info("MCP '%s' removed from agent", mcp_name)

    # ------------------------------------------------------------------
    # Toolkit credential indicators (Enhancement #5114, Bug #5183)
    # ------------------------------------------------------------------

    def _get_toolkit_card(self, toolkit_name: str, timeout: int = 10000):
        """Get the toolkit card element by name.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the toolkit item container.
        """
        card = self.toolkit_card.filter(has_text=toolkit_name).first
        card.wait_for(state="visible", timeout=timeout)
        return card

    def hover_toolkit_card(self, toolkit_name: str, timeout: int = 10000):
        """Hover over a toolkit card to reveal action icons.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        self.ensure_toolkits_section_visible()
        toolkit_card = self._get_toolkit_card(toolkit_name, timeout)
        toolkit_card.hover()
        self.page.wait_for_timeout(500)

    def _get_warning_banner_locator(self):
        """Get locator for credential warning banner on page."""
        return self.toolkit_warning_banner

    def has_toolkit_status_indicator(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows credential status indicator (warning banner).

        Uses data-testid="credential-warning-banner" set on BannerMessage.jsx.
        The banner appears below the toolkit card for any validation error.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning banner is visible.
        """
        self.ensure_toolkits_section_visible()
        try:
            self._get_warning_banner_locator().first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_status_indicator_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the status indicator tooltip text for a toolkit.

        Returns the aria-label attribute of the credential-warning-banner element,
        which contains the validation error message text.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (error message text), or None if not found.
        """
        self.ensure_toolkits_section_visible()
        try:
            warning = self._get_warning_banner_locator().first
            warning.wait_for(state="visible", timeout=timeout)
            return warning.get_attribute("aria-label")
        except Exception:
            return None

    def has_toolkit_warning_message(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if warning message is displayed for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning message is visible.
        """
        return self.has_toolkit_status_indicator(toolkit_name, timeout)

    def get_toolkit_warning_message(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the warning message text (alias for get_toolkit_status_indicator_tooltip).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Warning message text, or None if not found.
        """
        return self.get_toolkit_status_indicator_tooltip(toolkit_name, timeout)

    def is_toolkit_blocked(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows 'blocked by your organization' indicator.

        Used to verify guardrails blocking is applied without pylon reload.

        The blocked banner appears as a sibling element after the toolkit card,
        not inside it. We look for the banner following the card with the given name.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        try:
            card.wait_for(state="visible", timeout=timeout)
        except Exception:
            return False

        # The blocked banner is a sibling element after the toolkit card.
        # Look for it using xpath following-sibling or by checking the parent container.
        # First try: banner inside the card (in case UI structure changes)
        blocked_inside = card.locator(self.TOOLKIT_BLOCKED_SELECTOR)
        if blocked_inside.count() > 0:
            try:
                blocked_inside.wait_for(state="visible", timeout=1000)
                return True
            except Exception:
                pass

        # Second try: banner as following sibling of the card
        blocked_sibling = card.locator("xpath=following-sibling::*[1]").filter(
            has=self.page.locator(self.TOOLKIT_BLOCKED_SELECTOR)
        )
        if blocked_sibling.count() > 0:
            try:
                blocked_sibling.wait_for(state="visible", timeout=timeout)
                return True
            except Exception:
                pass

        # Third try: any blocked banner visible in the TOOLS section that mentions this toolkit type
        # The banner text contains the toolkit type (e.g., "Github toolkit is blocked")
        tools_section = self.page.locator('[data-testid="tools-section"], .tools-section, text="TOOLS"').first.locator("xpath=ancestor::*[3]")
        blocked_banner = tools_section.locator(self.TOOLKIT_BLOCKED_SELECTOR)
        try:
            blocked_banner.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_tool_blocked_in_toolkit(self, toolkit_name: str, timeout: int = 10000) -> bool:
        """Check if toolkit shows 'Some tools are not available anymore' indicator.

        Used to verify guardrails tool blocking is applied without pylon reload.
        Waits for the banner to appear (it may render with a slight delay after page load).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if tool blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        try:
            card.wait_for(state="visible", timeout=timeout)
        except Exception:
            return False

        # The banner may appear inside the card, as a sibling, or elsewhere in the TOOLS section.
        # Use a combined locator with 'or' to wait for any of these locations.
        blocked_banner = self.page.locator(self.TOOLKIT_TOOL_BLOCKED_SELECTOR)
        try:
            blocked_banner.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def has_toolkit_reload_button(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit card has reload button (visible on hover).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if reload button is visible.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_reload_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_reload_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the reload button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_reload_button.wait_for(state="visible", timeout=timeout)
            return self.toolkit_reload_button.get_attribute("aria-label")
        except Exception:
            return None

    def click_toolkit_reload_button(self, toolkit_name: str, timeout: int = 10000):
        """Click the reload button on a toolkit card.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        self.toolkit_reload_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked reload button for toolkit '%s'", toolkit_name)

    def has_toolkit_open_in_new_tab_button(
        self, toolkit_name: str, timeout: int = 5000
    ) -> bool:
        """Check if toolkit card has open-in-new-tab button (visible on hover).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if open-in-new-tab button is visible.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_open_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_open_in_new_tab_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the open-in-new-tab button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_open_button.wait_for(state="visible", timeout=timeout)
            return self.toolkit_open_button.get_attribute("aria-label")
        except Exception:
            return None

    def click_toolkit_open_in_new_tab(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str:
        """Click the open-in-new-tab button for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            URL of the new tab (toolkit detail page).
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        self.toolkit_open_button.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            self.toolkit_open_button.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        url = new_page.url
        logger.info("Opened toolkit in new tab: %s", url)
        return url

    # ------------------------------------------------------------------
    # Skills section (attach/detach skills on the agent version)
    # ------------------------------------------------------------------

    @action("Expand Skills section")
    def ensure_skills_section_visible(self, timeout: int = 5000):
        """Scroll to the Skills accordion section and wait for it to render.

        LOCATOR: ``agent-skills-section`` testid on the accordion content
        container (`ApplicationSkills.jsx`) — added in ELITEA-1735's
        testid-only rework, replacing the prior ``get_by_text("skills
        added.")`` handle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.skills_section.scroll_into_view_if_needed()
        self.skills_section.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(300)  # Animation settle

    @action("Attach skill")
    def attach_skill(self, skill_name: str, timeout: int = 10000):
        """Attach a skill to the agent version via the Skills section "+ Skill" button.

        LOCATOR: Clicks ``agent-add-skill-button`` (the "+ Skill" `BaseBtn`
        in `SkillMenu.jsx`) — added in ELITEA-1735's testid-only rework,
        replacing the prior `get_by_role("button", name="Skill")` handle
        (shipped off a since-retracted "accessible name is stable" amendment;
        see `.agents/role-overrides.md` § Implementer slot). Waits for the
        UnifiedDropdown popper (shared with the Toolkits "+ Toolkit" flow)
        and selects the matching item via the additive
        ``Popper.select_menuitem_by_testid`` helper (scoped to
        ``[data-testid="toolkit-menu-item"]``, confirmed live for the
        skill-attach flow specifically — see the ELITEA-1735 AFS Handles
        Reference). Attachment is an immediate API-level auto-save (PATCH
        .../skill/prompt_lib/{project}/{id} -> 201); no agent-level Save is
        required afterward.

        Args:
            skill_name: Exact name of the skill to attach.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Attaching skill '%s' to agent", skill_name)
        self.ensure_skills_section_visible(timeout=timeout)
        counter_before = self.get_skills_counter_text(timeout=timeout)

        self.agent_add_skill_button.wait_for(state="visible", timeout=timeout)
        self.agent_add_skill_button.click(force=True)

        popper = Popper.wait_for(self.page, timeout=timeout)
        Popper.select_menuitem_by_testid(popper, skill_name, self.page, timeout=timeout)
        self.wait_for_network(timeout=timeout)

        # The attach PATCH resolving is not sufficient — the Skills section
        # reads from an RTK Query cache that must invalidate + refetch before
        # the counter/card reflect the new attachment. Poll for the counter
        # text to actually change rather than trusting networkidle alone.
        deadline = time.time() + timeout / 1000
        counter_after = counter_before
        while time.time() < deadline:
            counter_after = self.get_skills_counter_text(timeout=1000)
            if counter_after != counter_before:
                break
            self.page.wait_for_timeout(300)

        if counter_after == counter_before:
            logger.warning(
                "Skills counter did not change after attaching '%s' (still %r)",
                skill_name, counter_after,
            )
        logger.info("Skill '%s' attached to agent (counter: %r -> %r)", skill_name, counter_before, counter_after)

    @action("Open the '+ Skill' attach dropdown (read-only)")
    def open_skill_menu(self, timeout: int = 10000) -> Locator:
        """Open the Skills-section "+ Skill" attach dropdown (SkillMenu.jsx)
        and return the MuiPopper Locator, WITHOUT selecting any item.

        Read-only companion to :meth:`attach_skill` (which opens + selects +
        attaches in one call, ELITEA-1735) — added for ELITEA-2605, which
        needs to inspect a candidate row (its custom-icon `<img>`) BEFORE
        deciding whether to select it. Does not change attachment state;
        callers that only inspect should close the popper afterward (e.g.
        ``page.keyboard.press("Escape")``) rather than clicking a row, or
        call :meth:`attach_skill` separately (which re-opens its own popper
        fresh) to actually attach.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the open MuiPopper-root.
        """
        logger.info("Opening '+ Skill' dropdown (read-only)")
        self.ensure_skills_section_visible(timeout=timeout)
        self.agent_add_skill_button.wait_for(state="visible", timeout=timeout)
        self.agent_add_skill_button.click(force=True)
        return Popper.wait_for(self.page, timeout=timeout)

    def get_skill_menu_item(self, popper: Locator, skill_name: str, timeout: int = 5000) -> Locator:
        """Return the SkillMenu dropdown row Locator for an exact skill name.

        LOCATOR: :attr:`TOOLKIT_MENU_ITEM_SELECTOR`, filtered by name text
        (same shared-row testid :meth:`attach_skill` selects via
        ``Popper.select_menuitem_by_testid`` — not unique per row, so this
        must stay scoped to *popper* and filtered by *skill_name*).

        Args:
            popper: The open MuiPopper Locator (from :meth:`open_skill_menu`).
            skill_name: Exact name of the skill row to locate.
            timeout: Maximum wait time in milliseconds.
        """
        row = popper.locator(self.TOOLKIT_MENU_ITEM_SELECTOR).filter(has_text=skill_name).first
        row.wait_for(state="visible", timeout=timeout)
        return row

    @action("Open Create New Skill from Agent")
    def open_create_new_skill(self, timeout: int = 10000):
        """Open the "+ Skill" dropdown and click "Create new".

        Navigates to ``/skills/create?source_application_id={agent_id}&
        return_url=...`` (`SkillMenu.jsx`'s `handleCreateNew()`) — the
        entry point for the Build-with-AI-from-Agent round-trip (ELITEA-1999):
        creating a Skill from here (manually or via Build with AI) redirects
        back to this Agent editor and auto-attaches the new Skill, instead of
        landing on the Skill's own details page.

        LOCATOR: ``agent-add-skill-create-new-button`` — see the field's
        docstring for the `add-data-testid` provenance.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening 'Create new' from the Skills add-menu")
        self.ensure_skills_section_visible(timeout=timeout)
        self.agent_add_skill_button.wait_for(state="visible", timeout=timeout)
        self.agent_add_skill_button.click(force=True)
        self.agent_add_skill_create_new_button.wait_for(state="visible", timeout=timeout)
        self.agent_add_skill_create_new_button.click()
        logger.info("Clicked 'Create new' — navigating to the Skill-create page")

    def get_skills_counter_text(self, timeout: int = 5000) -> str:
        """Return the Skills section counter text, e.g. "2/5 skills added.".

        LOCATOR: ``agent-skills-counter`` testid on the `Typography` node
        (`ApplicationSkills.jsx`) — added in ELITEA-1735's testid-only
        rework, replacing the prior ``get_by_text("skills added.")`` handle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.skills_counter.wait_for(state="visible", timeout=timeout)
        return (self.skills_counter.text_content() or "").strip()

    def wait_for_skills_counter(self, expected_prefix: str, timeout: int = 10000) -> str:
        """Poll the Skills section counter until it starts with *expected_prefix*.

        The Skills section reads from an RTK Query cache that refetches
        asynchronously — after a full page reload the counter can render
        transiently as "0/5 skills added." before the real attachment data
        arrives (same underlying cache-invalidation timing already handled
        in ``attach_skill()``). A single unconditioned read right after
        reload/navigation is a race; poll until it settles or times out.

        Args:
            expected_prefix: Text the counter should start with, e.g. "1/".
            timeout: Maximum wait time in milliseconds.

        Returns:
            The final counter text observed (whether or not it matched).
        """
        deadline = time.time() + timeout / 1000
        counter_text = self.get_skills_counter_text(timeout=timeout)
        while not counter_text.startswith(expected_prefix) and time.time() < deadline:
            self.page.wait_for_timeout(300)
            counter_text = self.get_skills_counter_text(timeout=1000)
        return counter_text

    def is_add_skill_button_disabled(self, timeout: int = 5000) -> bool:
        """Return True if the Skills section "+ Skill" button is disabled.

        The button becomes disabled the instant 5/5 skills are attached
        (proactive disable — not merely an on-click rejection); see
        ``get_add_skill_button_tooltip()`` for the accompanying message.

        LOCATOR: ``agent-add-skill-button`` testid (ELITEA-1735) — the SAME
        DOM node in both the enabled and disabled state (only the `disabled`
        prop toggles on `SkillMenu.jsx`'s `BaseBtn`), so no separate
        disabled-state lookup is needed (ELITEA-1790 testid-only rework;
        superseded the prior `[aria-label="Maximum number of skills
        reached"] button` raw handle).

        Args:
            timeout: Maximum wait time in milliseconds for the button.
        """
        self.ensure_skills_section_visible(timeout=timeout)
        self.agent_add_skill_button.wait_for(state="visible", timeout=timeout)
        return not self.agent_add_skill_button.is_enabled()

    def get_add_skill_button_tooltip(self, timeout: int = 5000) -> str | None:
        """Return the "+ Skill" button's tooltip text ("Maximum number of
        skills reached") once the 5-skill limit is reached.

        LOCATOR: ``agent-add-skill-button-tooltip`` testid (ELITEA-1790
        testid-only rework — added via `add-data-testid` to `SkillMenu.jsx`;
        see EliteaUI draft PR #546) on the MUI `<Box component="span">`
        Tooltip wrapper. MUI relocates the accessible tooltip label to this
        wrapper rather than the inner (disabled) button, since disabled
        elements don't fire hover/focus. Superseded the prior
        `[aria-label="Maximum number of skills reached"]` raw handle.
        Returns None if not found within the timeout (e.g. below the limit,
        where the wrapper carries no label).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.agent_add_skill_button_tooltip.wait_for(state="visible", timeout=timeout)
            return self.agent_add_skill_button_tooltip.get_attribute("aria-label")
        except Exception:
            return None

    def _get_tool_add_button_tooltip(self, wrapper: Locator, timeout: int) -> str | None:
        """Shared implementation for the 4 Tools "+ X" button tooltip getters.

        Args:
            wrapper: The button's Tooltip-wrapper `LocatorDescriptor` field
                (e.g. :attr:`add_toolkit_button_tooltip`).
            timeout: Maximum wait time in milliseconds.
        """
        try:
            wrapper.wait_for(state="visible", timeout=timeout)
            return wrapper.get_attribute("aria-label")
        except Exception:
            return None

    def get_add_toolkit_button_tooltip(self, timeout: int = 5000) -> str | None:
        """Return the "+ Toolkit" button's tooltip text (`lockedTooltip`
        when the version is locked, or the "Save first" hint when unsaved).

        See :attr:`add_toolkit_button_tooltip`'s docstring for why the
        wrapper (not the button) carries the `aria-label`. Returns None if
        the wrapper never appears within the timeout.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        return self._get_tool_add_button_tooltip(self.add_toolkit_button_tooltip, timeout)

    def get_add_mcp_button_tooltip(self, timeout: int = 5000) -> str | None:
        """Return the "+ MCP" button's tooltip text — see
        :meth:`get_add_toolkit_button_tooltip`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        return self._get_tool_add_button_tooltip(self.add_mcp_button_tooltip, timeout)

    def get_add_agent_button_tooltip(self, timeout: int = 5000) -> str | None:
        """Return the "+ Agent" button's tooltip text — see
        :meth:`get_add_toolkit_button_tooltip`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        return self._get_tool_add_button_tooltip(self.add_agent_button_tooltip, timeout)

    def get_add_pipeline_button_tooltip(self, timeout: int = 5000) -> str | None:
        """Return the "+ Pipeline" button's tooltip text — see
        :meth:`get_add_toolkit_button_tooltip`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        return self._get_tool_add_button_tooltip(self.add_pipeline_button_tooltip, timeout)

    def _skills_section_content(self):
        """Return a locator scoped to the Skills accordion's content container.

        LOCATOR: ``agent-skills-section`` testid on the shared
        `containerStyles` Box (`ApplicationSkills.jsx`) that wraps the
        header row (add-skill button + counter) and the `SkillCard` list —
        added in ELITEA-1735's testid-only rework, replacing the prior
        counter-text-based ancestor-xpath walk.
        """
        return self.skills_section

    def is_skill_attached(self, skill_name: str, timeout: int = 5000) -> bool:
        """Check whether a skill card for *skill_name* is rendered in the Skills section.

        LOCATOR: SkillCard's name `Typography` still has no data-testid of
        its own (only the outer card container does, as
        ``skill-card-{skill_id}`` — see ``SKILL_CARD_SELECTOR``), so this
        keeps matching by rendered skill-name text, scoped within the
        Skills section's testid-bearing content container
        (``_skills_section_content()``) — NOT page-wide — so this can't
        false-positive on the skill name appearing elsewhere (e.g. a chat
        response echoing the name, or a stray identical string on another
        part of the page). Kept skill-name-keyed (rather than switching to
        ``SKILL_CARD_SELECTOR``'s skill_id) because this method has 10+
        merged callers across the skills test suite that only have the
        name in scope — additive-only per `.claude/rules/page-objects.md`
        § shared-caller files.

        Args:
            skill_name: Name of the skill to look for.
            timeout: Maximum wait time in milliseconds.
        """
        self.ensure_skills_section_visible(timeout=timeout)
        try:
            self._skills_section_content().get_by_text(
                skill_name, exact=True,
            ).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def _skill_card(self, skill_name: str, timeout: int = 5000):
        """Return a locator scoped to a single attached skill's card.

        LOCATOR: `skill-card-{skill_id}` — added in the ELITEA-1735 rework
        (draft EliteaUI#540, not yet on `main`; confirmed live against
        `automation/testids`). The skill's numeric id isn't known to
        callers of this method (only the skill *name* is), so this filters
        every `[data-testid^="skill-card-"]` element (within the Skills
        section content container, so it can't false-positive elsewhere on
        the page) by its rendered name text — same `.filter(has_text=...)`
        pattern already used for toolkit cards (`_get_toolkit_card()` above).
        Replaces the ELITEA-1789 rework's prior `get_by_text(skill_name,
        exact=True)` + `xpath=ancestor::div[3]` walk with a testid-scoped
        lookup (ELITEA-1789 testid-only rework).

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skills_section_content().locator(
            self.SKILL_CARD_ANY_SELECTOR
        ).filter(has_text=skill_name).first
        card.wait_for(state="visible", timeout=timeout)
        return card

    def get_skill_card_icon_src(self, skill_name: str, timeout: int = 5000) -> str:
        """Return an attached skill's SkillCard custom-icon `<img>` src, or
        `""` if the card shows the default (non-custom) glyph instead.

        LOCATOR: :attr:`SKILL_CARD_ICON_IMG_SELECTOR`, scoped to the card
        resolved by :meth:`_skill_card` (ELITEA-2605). Mirrors
        ``SkillFormPage.get_form_icon_src()``'s "absence = default icon"
        convention — the `EliteAImage` `<img>` only renders when
        `skill.icon_meta.url` is set; the default `SkillIcon` SVG glyph
        renders instead (no `<img>`, no src) otherwise.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        icon_img = card.locator(self.SKILL_CARD_ICON_IMG_SELECTOR)
        try:
            icon_img.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        return icon_img.get_attribute("src") or ""

    def _get_skill_id_from_card(self, card: Locator) -> str:
        """Extract the skill_id embedded in a card's `skill-card-{skill_id}` testid.

        Args:
            card: Locator scoped to a single skill card (from `_skill_card()`).

        Returns:
            The skill_id string parsed out of the card's data-testid attribute.
        """
        testid = card.get_attribute("data-testid") or ""
        return testid.removeprefix("skill-card-")

    def get_skill_card_by_id(self, skill_id: str) -> Locator:
        """Return a locator for a single attached skill's card by its skill_id.

        LOCATOR: `skill-card-{skill_id}` (`SKILL_CARD_SELECTOR`) — the
        skill_id-keyed counterpart to `_skill_card()`, which is name-keyed
        because most callers don't have the id in scope. Callers that DO
        have the skill_id (e.g. right after creating it via the API/UI) use
        this instead of reaching for `SKILL_CARD_SELECTOR` directly, keeping
        the dynamic-testid template a page-object-internal detail
        (`.claude/rules/page-objects.md` — locators are class-level fields,
        never built in test/spec files).

        Args:
            skill_id: The attached skill's id, as embedded in its card's
                `skill-card-{skill_id}` testid.
        """
        return self.page.locator(self.SKILL_CARD_SELECTOR.format(skill_id))

    def get_skill_version_text(self, skill_name: str, timeout: int = 5000) -> str:
        """Return the currently displayed version text on a skill's card.

        LOCATOR: `skill-version-selector-trigger-{skill_id}` — added via
        `add-data-testid` in the ELITEA-1789 testid-only rework (EliteaUI
        draft PR #545), replacing the prior `.version-text` CSS-class
        handle. See Known Defect
        github.com/EliteaAI/elitea-testing-public/issues/46: the trigger
        still carries no ARIA role / `tabIndex=-1` / no accessible name —
        a testid closes the automation-handle gap only, not the surviving
        keyboard-accessibility half of that issue.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        skill_id = self._get_skill_id_from_card(card)
        trigger = card.locator(self.SKILL_VERSION_TRIGGER_SELECTOR.format(skill_id))
        trigger.wait_for(state="visible", timeout=timeout)
        return (trigger.text_content() or "").strip()

    @action("Open skill version selector")
    def open_skill_version_selector(self, skill_name: str, timeout: int = 10000):
        """Click a skill card's version-selector trigger to open the Versions menu.

        LOCATOR: `skill-version-selector-trigger-{skill_id}` for the click
        target, `skill-version-selector-menu-{skill_id}` to confirm the menu
        opened — both added via `add-data-testid` in the ELITEA-1789
        testid-only rework (EliteaUI draft PR #545), replacing the prior
        `.version-text` CSS-class click + raw `get_by_text("Versions")`
        handle. The "Versions" `<Menu>` React-portals to `document.body`
        (confirmed live via `browser_evaluate`: not a DOM descendant of the
        skill's card) — so the menu testid is looked up page-wide, not
        scoped to the card.

        Args:
            skill_name: Exact name of the attached skill whose version
                selector should be opened.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        skill_id = self._get_skill_id_from_card(card)

        trigger = card.locator(self.SKILL_VERSION_TRIGGER_SELECTOR.format(skill_id))
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()

        menu = self.page.locator(self.SKILL_VERSION_MENU_SELECTOR.format(skill_id))
        menu.wait_for(state="visible", timeout=timeout)

    def is_versions_menu_open(self, skill_name: str, timeout: int = 2000) -> bool:
        """Check whether the "Versions" menu (opened by the version selector) is visible.

        LOCATOR: `skill-version-selector-menu-{skill_id}` — the menu portals
        to `document.body`, so it's resolved page-wide once `skill_id` is
        known via the skill's card (ELITEA-1789 testid-only rework).

        Args:
            skill_name: Exact name of the attached skill whose menu is checked.
            timeout: Maximum wait time in milliseconds.
        """
        try:
            skill_id = self._get_skill_id_from_card(
                self._skill_card(skill_name, timeout=timeout)
            )
            self.page.locator(self.SKILL_VERSION_MENU_SELECTOR.format(skill_id)).wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def get_versions_menu_item_names(self, skill_name: str, timeout: int = 5000) -> list[str]:
        """Return the text of every version entry in the open Versions menu.

        LOCATOR: the menu header carries `skill-version-selector-menu-{skill_id}`;
        each entry carries `skill-version-option-{version_name}`. Enumeration
        (rather than a single known-name lookup) uses the PREFIX-match
        `skill-version-option-` selector page-wide (not scoped to the card,
        since the menu portals to `document.body`) — MUI unmounts `MenuItem`s
        while their `<Menu>` is closed, so only the currently-open menu's
        entries are ever in the DOM, making the prefix match safe (ELITEA-1789
        testid-only rework — replaces the prior raw `get_by_text("Versions")`
        + `xpath=ancestor::div[2]` + `get_by_role("menuitem")` chain).

        Args:
            skill_name: Exact name of the attached skill whose menu is read.
            timeout: Maximum wait time in milliseconds.
        """
        skill_id = self._get_skill_id_from_card(
            self._skill_card(skill_name, timeout=timeout)
        )
        menu_header = self.page.locator(self.SKILL_VERSION_MENU_SELECTOR.format(skill_id))
        menu_header.wait_for(state="visible", timeout=timeout)

        items = self.page.locator(self.SKILL_VERSION_OPTION_ANY_SELECTOR)
        items.first.wait_for(state="visible", timeout=timeout)
        return [
            (items.nth(i).text_content() or "").strip()
            for i in range(items.count())
        ]

    def close_versions_menu(self):
        """Close the open Versions menu by pressing Escape."""
        self.page.keyboard.press("Escape")

    def get_skill_version_selector_trigger(self, skill_name: str, timeout: int = 5000) -> Locator:
        """Return the version-selector trigger Locator for a skill's card.

        LOCATOR: `skill-version-selector-trigger-{skill_id}`
        (`SKILL_VERSION_TRIGGER_SELECTOR`), scoped off :meth:`_skill_card`
        — same handle :meth:`open_skill_version_selector` clicks, exposed
        directly for callers (ELITEA-2614) that need to inspect the
        trigger itself (e.g. its `aria-label`) rather than open the menu.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        skill_id = self._get_skill_id_from_card(card)
        return card.locator(self.SKILL_VERSION_TRIGGER_SELECTOR.format(skill_id))

    @action("Select a skill's version from the Versions menu")
    def select_skill_version(self, skill_name: str, version_name: str, timeout: int = 10000):
        """Open a skill card's version selector and click a specific version option.

        LOCATOR: reuses :meth:`open_skill_version_selector`'s skill_id
        resolution + trigger click to open the "Versions" menu, then clicks
        the target entry via ``SKILL_VERSION_OPTION_SELECTOR`` — the
        template constant already defined at class level (ELITEA-1789
        testid-only rework), never previously called from a public method
        (ELITEA-1789's own case only ever had one saved version, so
        selecting a non-base option was never exercised — ELITEA-2610 is
        the first caller). Selecting a version is an immediate API-level
        auto-save (PATCH .../skill/prompt_lib/{project}/{skill_id} -> 201),
        mirroring :meth:`attach_skill`'s counter-polling pattern: rather
        than trust networkidle alone, poll the trigger's own text until it
        reflects *version_name* before returning, so callers can safely
        send the next chat message right after this call.

        Args:
            skill_name: Exact name of the attached skill.
            version_name: Exact version name to select (e.g. "casual", "base").
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting version %r for skill %r", version_name, skill_name)
        self.open_skill_version_selector(skill_name, timeout=timeout)

        option = self.page.locator(self.SKILL_VERSION_OPTION_SELECTOR.format(version_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()

        card = self._skill_card(skill_name, timeout=timeout)
        skill_id = self._get_skill_id_from_card(card)
        trigger = card.locator(self.SKILL_VERSION_TRIGGER_SELECTOR.format(skill_id))

        deadline = time.time() + timeout / 1000
        current = ""
        while time.time() < deadline:
            current = (trigger.text_content() or "").strip()
            if current == version_name:
                break
            self.page.wait_for_timeout(300)

        if current != version_name:
            logger.warning(
                "Version trigger did not update to %r within timeout (still %r)",
                version_name, current,
            )
        logger.info("Skill %r version selector now shows %r", skill_name, current)

    @action("Attempt to open a skill's version selector (locked version — expect no-op)")
    def attempt_open_skill_version_selector(self, skill_name: str, timeout: int = 5000) -> bool:
        """Click a skill card's version-selector trigger and report whether
        the Versions menu actually opened.

        On a locked (published/embedded) agent version,
        `SkillVersionSelector.jsx`'s trigger has `onClick={isUpdating ||
        disabled ? undefined : handleOpen}` — clicking a `Box` with no
        `onClick` handler is a legal Playwright click that simply does
        nothing (source-confirmed, ELITEA-2614). Distinguishes an
        intentional "attempt and observe no-op" from
        :meth:`open_skill_version_selector`, which asserts the menu DOES
        open and would just time out here without telling the caller
        whether the click itself was refused or merely slow.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds for the trigger
                itself; the post-click menu check uses a short fixed
                window (menus that DO open render near-instantly).

        Returns:
            True if the Versions menu opened after the click, False if it
            stayed closed (the expected outcome on a locked version).
        """
        trigger = self.get_skill_version_selector_trigger(skill_name, timeout=timeout)
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()
        return self.is_versions_menu_open(skill_name, timeout=1500)

    @action("Hover a skill's card to reveal its hover-only action buttons")
    def hover_skill_card(self, skill_name: str, timeout: int = 5000) -> Locator:
        """Hover a skill's card and return its Locator, revealing the
        hover-only "remove skill" / "open in new tab" icon buttons
        (`SkillCard.jsx`'s `actionButton` style flips `display:none` ->
        `flex` only on the card's `:hover` CSS rule).

        Extracted from :meth:`remove_skill`'s hover-prep steps for callers
        (ELITEA-2614) that need to ASSERT on the revealed buttons
        (disabled state, `aria-label`) without actually removing anything.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds for the card itself.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        card.scroll_into_view_if_needed()
        card.hover()
        self.page.wait_for_timeout(500)  # hover-reveal CSS transition
        return card

    def get_skill_card_remove_button(self, skill_name: str, timeout: int = 5000) -> Locator:
        """Return the "remove skill" icon button Locator for a skill's card.

        LOCATOR: `SKILL_CARD_REMOVE_BUTTON_SELECTOR`, scoped off
        :meth:`_skill_card` (same handle :meth:`remove_skill` clicks).
        DOM-attribute reads (`get_attribute("aria-label")`,
        `is_disabled()`) work regardless of the card's hover state; callers
        that need real VISIBILITY should call :meth:`hover_skill_card`
        first.

        Args:
            skill_name: Exact name of the attached skill.
            timeout: Maximum wait time in milliseconds.
        """
        card = self._skill_card(skill_name, timeout=timeout)
        return card.locator(self.SKILL_CARD_REMOVE_BUTTON_SELECTOR)

    def is_remove_skill_button_visible(self, skill_name: str, timeout: int = 5000) -> bool:
        """Point-in-time check: is the "remove skill" icon button currently
        present for the given skill's card?

        The button is **hover-revealed** — absent from the accessibility
        tree for an un-hovered card (ELITEA-1792 exploration). The real
        mouse cursor is moved to a neutral corner first: a prior action
        (e.g. clicking a popper menu item during ``attach_skill()``) can
        leave the browser's actual cursor resting over a card that renders
        in roughly the same screen position once the popper closes, which
        keeps that card's CSS ``:hover`` state engaged even though no test
        code explicitly hovered it — confirmed live in ELITEA-1792
        exploration. Moving the mouse away first makes this a genuine
        "unhovered" check rather than an accidental false-positive.

        LOCATOR: `skill-card-remove-button` — added via `add-data-testid`
        in the ELITEA-1792 testid-only rework (EliteaUI draft PR #547),
        replacing the prior `get_by_role("button", name="remove skill")`
        handle. Scoped within the specific skill's card (`_skill_card()`)
        via `SKILL_CARD_REMOVE_BUTTON_SELECTOR`. The "open in new tab"
        sibling button is untouched by this test and still carries no
        `data-testid` — out of scope for this rework.

        VISIBILITY, not DOM presence: the button element is always in the
        DOM (`SkillCard.jsx`'s `actionButton` style is `display: none` by
        default, flipped to `display: flex` only on the card's `:hover`
        CSS rule) — a `data-testid` attribute exists on it regardless of
        hover state. The prior `get_by_role` handle queried the
        accessibility tree, which excludes `display:none` elements, so it
        naturally encoded the hover-reveal semantics this method's callers
        rely on. A DOM-presence check (`.count() > 0`) on the testid would
        silently always return True and break that semantic — confirmed
        live during this rework (initial `.count()` implementation failed
        the "not visible before hover" assertion in
        ``test_remove_attached_skill_from_agent.py``). `.is_visible()`
        replicates the accessibility-tree behavior correctly.

        Args:
            skill_name: Exact name of the attached skill whose card is checked.
            timeout: Maximum wait time in milliseconds for the card itself.
        """
        self.page.mouse.move(0, 0)
        card = self._skill_card(skill_name, timeout=timeout)
        return card.locator(self.SKILL_CARD_REMOVE_BUTTON_SELECTOR).is_visible()

    @action("Remove skill")
    def remove_skill(self, skill_name: str, timeout: int = 10000):
        """Remove an attached skill from the agent (ELITEA-1792).

        Mirrors ``remove_toolkit()`` above: the "remove skill" icon button
        (and its "open in new tab" sibling) is **hover-revealed** — absent
        from the accessibility tree for an un-hovered card (ELITEA-1792
        exploration) — so the card must be hovered first.

        LOCATOR: `skill-card-remove-button` — added via `add-data-testid`
        in the ELITEA-1792 testid-only rework (EliteaUI draft PR #547),
        replacing the prior `get_by_role("button", name="remove skill")`
        handle. Scoped to the specific card (via ``_skill_card()``) through
        the class-level `SKILL_CARD_REMOVE_BUTTON_SELECTOR` constant. The
        "open in new tab" sibling is never clicked or asserted by this
        test, so it's still untested and still carries no `data-testid` —
        out of scope for this rework.

        Clicking the icon does **not** remove the skill instantly: it opens
        a "Remove skill?" confirmation dialog (same shape as the "Remove
        toolkit?" dialog handled in ``remove_toolkit()``) with "Cancel" /
        "Remove" buttons. Confirming fires the detach auto-save (PATCH
        .../skill/prompt_lib/{project}/{skill-id} -> 200, contrast with
        attach's 201) — no agent-level Save is required afterward.

        Args:
            skill_name: Exact name of the attached skill to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing skill '%s' from agent", skill_name)

        card = self._skill_card(skill_name, timeout=timeout)
        card.scroll_into_view_if_needed()
        card.hover()
        self.page.wait_for_timeout(500)  # hover-reveal CSS transition

        remove_btn = card.locator(self.SKILL_CARD_REMOVE_BUTTON_SELECTOR)
        remove_btn.wait_for(state="visible", timeout=5000)
        remove_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle the "Remove skill?" confirmation dialog.
        dialog = Dialog.wait_for(self.page)
        Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")

        # Wait for network idle so the detach PATCH + Skills refetch settle.
        self.wait_for_network(timeout=timeout)

        # Explicitly wait for the skill's card to disappear from the DOM —
        # the Skills section reads from an RTK Query cache that refetches
        # asynchronously (same timing caveat as attach_skill()).
        try:
            card.wait_for(state="hidden", timeout=10000)
        except Exception:
            pass

        logger.info("Skill '%s' removed from agent", skill_name)

    # ------------------------------------------------------------------
    # Instructions field skill mention ("~" trigger) — ELITEA-1791
    # ------------------------------------------------------------------
    #
    # This is a DIFFERENT entry point from send_chat_message_with_mention()
    # above: that method drives the embedded-chat message input
    # (data-testid="chat-message-input"), while these methods drive the
    # Instructions accordion field (data-testid="agent-instructions-input",
    # inherited from AgentFormPage.instructions_input). Both surfaces
    # render the same "Mention skill" popper component, but the two input
    # fields are separate and must not be confused.

    def _instructions_mention_container(self, timeout: int = 10000):
        """Return a locator scoped to the open "Mention skill" panel.

        LOCATOR: ``skill_mention_list`` (``data-testid="skill-mention-list"``,
        class field above) — the same panel component the embedded-chat
        mention flow (``send_chat_message_with_mention``) already targets by
        testid. The Instructions-field mention panel and the embedded-chat
        mention panel render the identical shared component
        (``MentionSkillList.jsx``), so the existing testid applies here for
        free (ELITEA-1791 testid-only rework, issue #33).
        """
        self.skill_mention_list.wait_for(state="visible", timeout=timeout)
        return self.skill_mention_list

    @action("Type ~ in Instructions field")
    def type_tilde_in_instructions(self, timeout: int = 10000) -> Locator:
        """Type "~" in the Agent Instructions field and wait for the
        "Mention skill" suggestion panel to appear.

        Targets ``instructions_input`` (the Instructions accordion textarea,
        accessible name "Guidelines for the AI agent") — NOT the embedded
        chat input (see module note above). No fixed wait / network-idle
        wait is used: the mention list is a client-side filter over data
        the page already holds (attached-skills data fetched when the
        Skills accordion loaded), so no additional network request fires
        between typing "~" and the panel appearing (ELITEA-1791
        exploration) — this waits only on the "Mention skill" header text
        becoming visible.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator scoped to the mention suggestion panel container, for
            asserting on the candidate rows it contains.
        """
        logger.info("Typing ~ in Instructions field to open mention panel")
        self.instructions_input.click()
        self.instructions_input.press_sequentially("~", delay=50)
        return self._instructions_mention_container(timeout=timeout)

    def get_instructions_mention_item(self, skill_name: str, timeout: int = 5000) -> Locator:
        """Return a locator for a mention candidate row by exact skill name,
        scoped to the open "Mention skill" panel (Instructions field).

        Use this for both positive assertions (row is visible) and negative
        assertions (``expect(locator).to_have_count(0)`` for a skill that
        must NOT be offered) — a count-based assertion on this exact-text
        locator is stronger than counting rows, since it can't be fooled by
        the unattached skill appearing under a different label.

        Args:
            skill_name: Exact name of the skill to look for.
            timeout: Maximum wait time in milliseconds for the panel header.
        """
        container = self._instructions_mention_container(timeout=timeout)
        return container.locator(self.SKILL_MENTION_ITEM_SELECTOR.format(skill_name))

    @action("Select skill from Instructions mention panel")
    def select_skill_from_instructions_mention(self, skill_name: str, timeout: int = 5000):
        """Click a skill row in the open "Mention skill" panel (Instructions
        field), inserting "~<skill_name>" as plain text into the field.

        Must be called while the panel is open (after
        ``type_tilde_in_instructions()``).

        Args:
            skill_name: Exact name of the attached skill to select.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting '%s' from Instructions mention panel", skill_name)
        item = self.get_instructions_mention_item(skill_name, timeout=timeout).first
        item.wait_for(state="visible", timeout=timeout)
        item.click()
        self.page.wait_for_timeout(300)

    @action("Clear Instructions field")
    def clear_instructions_field(self):
        """Clear the Instructions field content (case step 6's own described
        technique: "removing Skill A reference" before re-triggering "~").

        Uses Playwright's ``clear()`` — the same MUI-field-clearing call
        already trusted elsewhere in this page object (``fill_form()`` in
        ``AgentFormPage``) — rather than a manual Control+a/Delete key
        sequence: exploration found the manual sequence unreliable here
        (only the leading "~" was removed, not the full mention text),
        while ``clear()`` empties the field reliably and still fires
        React's ``onChange`` (unlike ``fill()`` with a non-empty value,
        which is the pattern ``clear()`` itself is exempt from per
        `.claude/rules/mui-patterns.md`).
        """
        self.instructions_input.click()
        self.instructions_input.clear()

    # ------------------------------------------------------------------
    # Embedded chat (right panel)
    # ------------------------------------------------------------------

    def _embedded_chat_messages(self):
        """Return a locator for all message items in the embedded chat.

        Scoped inside the chat message list container.
        """
        return self.chat_message_list.locator(self.CHAT_MESSAGE_ITEM_SELECTOR)

    def get_chat_message_count(self) -> int:
        """Return the current number of messages visible in the embedded chat.

        Use this before sending a message to capture the baseline count,
        then pass the count to ``wait_for_chat_response(initial_count=...)``.

        Returns:
            Integer count of message items currently in the chat.
        """
        return self._embedded_chat_messages().count()

    def get_last_message_tool_chip_texts(self, timeout: int = 10000) -> list[str]:
        """Return the text of every ``chat-answer-tool-chip`` in the LAST
        embedded-chat message, scoped to that message only (ELITEA-2610).

        Distinct from :meth:`get_nested_agent_tool_chip_texts`, which is
        scoped INSIDE a nested sub-agent's own accordion details (a parent
        agent invoking another agent as a tool). This reader is for the
        TOP-LEVEL case — an agent invoking a skill directly, no nested
        sub-agent involved — and scopes to the last ``chat-message-item``
        so that across multiple turns in one conversation, only the most
        recent turn's chip(s) are read, never an earlier turn's.

        Args:
            timeout: Maximum wait time in milliseconds for at least one
                chip to appear in the last message.

        Returns:
            List of chip text strings (e.g. ``["Skill: my-skill-name"]``).
        """
        last_msg = self._embedded_chat_messages().last
        chips = last_msg.locator(self.CHAT_ANSWER_TOOL_CHIP_SELECTOR)
        chips.first.wait_for(state="visible", timeout=timeout)
        return [(chips.nth(i).text_content() or "").strip() for i in range(chips.count())]

    def get_chat_starter_tiles(self):
        """Return the Locator matching ALL rendered embedded-chat conversation
        starter tiles (ELITEA-1886) — use ``.count()`` to verify the configured
        starter chips render before any message is sent.
        """
        return self.page.locator(self.CHAT_STARTER_TILE)

    @action("Click a conversation starter tile in the embedded chat")
    def click_chat_starter_tile(self, match_text: str, timeout: int = 10000) -> str:
        """Click the embedded-chat starter tile whose text CONTAINS *match_text*
        (ELITEA-1886) — resolves via ``CHAT_STARTER_TILE`` + ``.filter(has_text=...)``,
        same idiom as :meth:`ChatPage.click_chat_starter_tile`. Returns the
        tile's own full (stripped) text at click time, so callers can assert
        the composer was populated with the SAME text actually clicked rather
        than a hardcoded literal.
        """
        tile = self.page.locator(self.CHAT_STARTER_TILE).filter(has_text=match_text)
        tile.first.wait_for(state="visible", timeout=timeout)
        starter_text = (tile.first.text_content() or "").strip()
        tile.first.click()
        return starter_text

    def get_last_chat_message_agent_markers(self) -> tuple[bool, bool, bool]:
        """Return agent/user code-path markers for the last (or only) message.

        Scoped inside the last ``chat-message-item`` — works equally for a
        single-message list, where "last" == "only" (ELITEA-1885: welcome
        message before any user message).

        Returns:
            ``(has_read_out, has_answer_marker, has_delete_button)``:

            - ``has_read_out`` — ``chat-read-out-button`` present
              (agent-only: TTS read-out, rendered by ``ApplicationAnswer.jsx``).
            - ``has_answer_marker`` — either ``skill-test-last-response``
              (this item is the last/only message) or ``chat-answer-content``
              (non-last) is present — the ``isLastMessage ? ... : ...``
              ternary from ``ApplicationAnswer.jsx``.
            - ``has_delete_button`` — ``chat-message-delete-button`` present
              (user-message-only, per ``UserMessage.jsx``).

            A message rendered via the agent code path has
            ``(True, True, False)``. Returns ``(False, False, False)`` if the
            chat has no messages.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return (False, False, False)

        last_msg = messages.last
        has_read_out = last_msg.locator(self.CHAT_READ_OUT_BUTTON_SELECTOR).count() > 0
        has_answer_marker = (
            last_msg.locator(self.CHAT_ANSWER_CONTENT_SELECTOR).count() > 0
            or last_msg.locator(self.SKILL_TEST_LAST_RESPONSE_SELECTOR).count() > 0
        )
        has_delete_button = last_msg.locator(self.CHAT_MESSAGE_DELETE_SELECTOR).count() > 0
        return (has_read_out, has_answer_marker, has_delete_button)

    @action("Send embedded chat message")
    def send_chat_message(self, message: str, timeout: int = 10000):
        """Type and send a message in the embedded chat panel.

        Uses press_sequentially() instead of fill() to trigger React onChange.
        MUI inputs don't update React state with fill() — the Send button
        stays disabled because React thinks the input is empty.

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending message in embedded chat: %s", message[:60])
        self.chat_message_input.wait_for(state="visible", timeout=timeout)
        self.chat_message_input.click()
        self.chat_message_input.clear()
        self.chat_message_input.press_sequentially(message, delay=10)
        self.page.wait_for_timeout(300)

        self.chat_send_button.wait_for(state="visible", timeout=timeout)
        self.chat_send_button.click()
        logger.info("Message sent in embedded chat")

    @action("Send embedded chat message with skill mention")
    def send_chat_message_with_mention(
        self, skill_name: str, prompt: str, timeout: int = 10000,
    ):
        """Type "~<skill_name> <prompt>" in the embedded chat and send it.

        LOCATOR: Typing "~" opens the "Mention skill" popper
        (`MentionSkillList.jsx`), now carrying the ``skill-mention-list``
        testid on its container and ``skill-mention-item-{skill-name}`` on
        each row (`MentionToolItem.jsx`'s additive optional ``testId``
        prop) — added in ELITEA-1735's testid-only rework, replacing the
        prior "Mention skill" header-text + ancestor-xpath walk. Uses
        ``press_sequentially`` (never ``fill()``) throughout: selecting a
        mention item inserts a chip into the input, and appending the
        prompt text via ``fill()`` would replace the whole textbox value
        and destroy that chip, so the prompt is also typed via
        ``press_sequentially`` (ELITEA-1735 exploration).

        Args:
            skill_name: Exact name of the attached skill to mention.
            prompt: Text to append after the mention chip.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Sending mention message: ~%s %s", skill_name, prompt[:60])
        self.chat_message_input.wait_for(state="visible", timeout=timeout)
        self.chat_message_input.click()
        self.chat_message_input.press_sequentially("~", delay=50)

        # Wait for the "Mention skill" popper and select the matching item
        # by its dynamic testid, scoped within the popper's own container.
        self.skill_mention_list.wait_for(state="visible", timeout=timeout)
        mention_item = self.skill_mention_list.locator(
            self.SKILL_MENTION_ITEM_SELECTOR.format(skill_name)
        ).first
        mention_item.wait_for(state="visible", timeout=timeout)
        mention_item.click()
        self.page.wait_for_timeout(300)

        self.chat_message_input.press_sequentially(f" {prompt}", delay=30)
        self.page.wait_for_timeout(300)

        self.chat_send_button.wait_for(state="visible", timeout=timeout)
        self.chat_send_button.click()
        logger.info("Mention message sent (~%s)", skill_name)

    @action("Type ~ in embedded chat")
    def type_tilde_in_chat(self, timeout: int = 10000) -> Locator:
        """Type "~" in the embedded chat message input and wait for the
        "Mention skill" popper to appear, WITHOUT selecting any item.

        Read-only counterpart to :meth:`send_chat_message_with_mention`
        (ELITEA-2605) — that method types "~", selects a row, appends a
        prompt, and sends in one call; this method stops right after the
        popper opens, so a caller can inspect a row (e.g. its custom-icon
        `<img>`) before deciding whether to select it. Mirrors
        :meth:`type_tilde_in_instructions`'s read-only shape for the
        Instructions-field mention entry point.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator scoped to the open ``skill_mention_list`` popper.
        """
        logger.info("Typing ~ in embedded chat to open mention popper")
        self.chat_message_input.wait_for(state="visible", timeout=timeout)
        self.chat_message_input.click()
        self.chat_message_input.press_sequentially("~", delay=50)
        self.skill_mention_list.wait_for(state="visible", timeout=timeout)
        return self.skill_mention_list

    def get_chat_mention_item(self, skill_name: str, timeout: int = 5000) -> Locator:
        """Return the embedded-chat "~"-mention popper row Locator for an
        exact skill name.

        LOCATOR: :attr:`SKILL_MENTION_ITEM_SELECTOR`, scoped to the open
        ``skill_mention_list`` popper (call after :meth:`type_tilde_in_chat`).

        Args:
            skill_name: Exact name of the attached skill to look for.
            timeout: Maximum wait time in milliseconds.
        """
        self.skill_mention_list.wait_for(state="visible", timeout=timeout)
        row = self.skill_mention_list.locator(
            self.SKILL_MENTION_ITEM_SELECTOR.format(skill_name)
        ).first
        row.wait_for(state="visible", timeout=timeout)
        return row

    # ------------------------------------------------------------------
    # LLM model selector (embedded chat panel, ELITEA-1881)
    # ------------------------------------------------------------------

    @action("Open LLM model selector")
    def open_model_selector(self, timeout: int = 5000):
        """Click the embedded chat panel's model selector to open the dropdown.

        LOCATOR: ``model-selector-button`` testid.

        Args:
            timeout: Maximum wait for the first option to become visible.
        """
        logger.info("Opening LLM model selector")
        self.model_selector_button.click()
        self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR).first.wait_for(
            state="visible", timeout=timeout
        )

    def get_selected_model_name(self) -> str:
        """Return the currently displayed model name on the closed selector.

        LOCATOR: ``model-selector-name`` testid.
        """
        return (self.model_selector_name.text_content() or "").strip()

    def is_model_option_visible(self, display_name: str, timeout: int = 5000) -> bool:
        """Return True if a model option with *display_name* is visible in
        the open dropdown.

        LOCATOR: ``MODEL_SELECTOR_OPTION_ANY_SELECTOR``, filtered by the
        option's rendered display text (see class-level docstring comment
        for why display text — not the dynamic testid's API-name suffix —
        is the selection key).

        Args:
            display_name: Exact rendered model name (e.g.
                "Anthropic Claude 4.5 Sonnet").
            timeout: Maximum wait time in milliseconds.
        """
        option = self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR).filter(
            has_text=display_name
        )
        try:
            option.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_visible_model_option_names(self, timeout: int = 5000) -> list[str]:
        """Return the rendered display text of every currently-visible option
        in the OPEN model-selector dropdown (ELITEA-2075).

        Call after :meth:`open_model_selector`. Additive — does not touch
        :meth:`is_model_option_visible`/:meth:`select_llm_model`, which stay
        the exact-match entry points; this is for callers that must find an
        option by a PARTIAL/fuzzy match (e.g. "any Sonnet 4.5-family model"
        when the exact case-text model name doesn't exist verbatim in this
        environment).
        """
        options = self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR)
        options.first.wait_for(state="visible", timeout=timeout)
        return [(options.nth(i).text_content() or "").strip() for i in range(options.count())]

    def close_model_selector(self, timeout: int = 5000):
        """Close the open model-selector dropdown via Escape, without
        selecting anything.

        Mirrors ``ChatPage.close_open_dialogs()``'s Escape-key pattern.
        Use after verifying option visibility (e.g. Step 3) when the caller
        doesn't want to leave the dropdown open before a subsequent
        :meth:`open_model_selector` call — reopening while it's already
        open would toggle it closed instead.
        """
        self.page.keyboard.press("Escape")
        self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR).first.wait_for(
            state="hidden", timeout=timeout
        )

    @action("Select LLM model")
    def select_llm_model(self, display_name: str, timeout: int = 5000):
        """Select a model from the OPEN model-selector dropdown by its
        rendered display name.

        Call after :meth:`open_model_selector`. Does not click Save — the
        caller decides when to persist via ``save_button``/``click_save()``
        (inherited from ``AgentFormPage``).

        Args:
            display_name: Exact rendered model name (e.g.
                "Anthropic Claude 4.5 Sonnet").
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting LLM model: %s", display_name)
        option = self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR).filter(
            has_text=display_name
        )
        option.first.wait_for(state="visible", timeout=timeout)
        option.first.click()
        logger.info("LLM model '%s' selected", display_name)

    # ------------------------------------------------------------------
    # Model Settings dialog (embedded chat panel, ELITEA-1880)
    # ------------------------------------------------------------------

    @action("Open Model settings dialog")
    def open_model_settings_dialog(self, timeout: int = 5000):
        """Click the gear icon and wait for the Model settings dialog to open.

        LOCATOR: ``model-settings-button`` -> ``model-settings-dialog``.
        """
        logger.info("Opening Model settings dialog")
        self.model_settings_button.click()
        self.model_settings_dialog.wait_for(state="visible", timeout=timeout)

    def is_reasoning_slider_visible(self, timeout: int = 5000) -> bool:
        """Return True if the Reasoning slider (Low/Medium/High) is shown.

        LOCATOR: ``model-settings-reasoning-slider``. Rendered only for a
        reasoning-capable model (``model.supports_reasoning``) — a
        non-reasoning model renders the Creativity/Temperature slider
        instead, which carries no testid (out of this case's scope). Call
        after :meth:`open_model_settings_dialog`.
        """
        try:
            self.model_settings_reasoning_slider.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_reasoning_slider_text(self, timeout: int = 5000) -> str:
        """Return the Reasoning slider's own rendered text (label + Low/Medium/High).

        LOCATOR: ``model-settings-reasoning-slider``. Call after
        :meth:`open_model_settings_dialog` once
        :meth:`is_reasoning_slider_visible` is True.
        """
        self.model_settings_reasoning_slider.wait_for(state="visible", timeout=timeout)
        return (self.model_settings_reasoning_slider.text_content() or "").strip()

    def get_max_tokens_section_text(self, timeout: int = 5000) -> str:
        """Return the Max Completion Tokens section's own rendered text
        (label + Default/Custom toggle) — always present regardless of
        model type.

        LOCATOR: ``model-settings-max-tokens-section``. Call after
        :meth:`open_model_settings_dialog`.
        """
        self.model_settings_max_tokens_section.wait_for(state="visible", timeout=timeout)
        return (self.model_settings_max_tokens_section.text_content() or "").strip()

    @action("Close Model settings dialog via Cancel")
    def close_model_settings_dialog_via_cancel(self, timeout: int = 5000):
        """Click Cancel and wait for the Model settings dialog to close.

        LOCATOR: ``model-settings-cancel-button``. Discards any local
        (unapplied) edits made inside the dialog — this case never edits a
        setting, so Cancel and Apply are behaviorally equivalent here (AFS
        step 7 observation).
        """
        logger.info("Closing Model settings dialog via Cancel")
        self.model_settings_cancel_button.click()
        self.model_settings_dialog.wait_for(state="hidden", timeout=timeout)

    @action("Clear embedded chat")
    def clear_embedded_chat(self, timeout: int = 10000):
        """Click the "Clear the chat" button in the embedded chat panel.

        LOCATOR: ``chat-clear-button`` testid on ``ClearChatButton.jsx`` —
        added in ELITEA-1735's testid-only rework, replacing the prior
        ``get_by_label("clear the chat").first`` handle. The old handle
        worked only by DOM order: `RunHistoryContainer.jsx` carries the
        identical literal ``aria-label="clear the chat"`` on an unrelated
        button elsewhere on the agent detail page, so a `.first` pick was a
        footgun, not a contract. The new testid is scoped to the shared
        `ClearChatButton.jsx` component (5 consumers incl. this page) and
        disambiguates unambiguously.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clearing embedded chat")
        self.chat_clear_button.wait_for(state="visible", timeout=timeout)
        self.chat_clear_button.click()
        self.page.wait_for_timeout(500)
        logger.info("Embedded chat cleared")

    def wait_for_chat_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 2000,
        timeout: int = 60000,
    ):
        """Wait for the AI response in the embedded chat to complete.

        Waits for new messages to appear beyond initial_count, then waits
        for the "Clear chat" button to become visible (indicates response
        is complete and ready).

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this long (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for embedded chat response (initial_count=%d, timeout=%dms)",
            initial_count, timeout,
        )
        messages = self._embedded_chat_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message beyond initial_count
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for "Clear chat" button to appear (indicates response is complete)
        remaining_ms = max(1000, int((deadline - time.time()) * 1000))
        try:
            self.chat_clear_button.wait_for(state="visible", timeout=remaining_ms)
            logger.info("Clear chat button visible — response complete")
        except Exception:
            logger.warning("Clear chat button not visible within timeout")

        # Wait for loading indicators to disappear (RotatingMessages.jsx)
        loading_phrases = [
            "Waking the agent", "Packing its tools", "Wiring integrations",
            "Fetching keys", "Installing skills", "Learning your playbook",
            "Safety checks", "Quick sandbox", "Final polish",
        ]

        # Wait for the actual response content to stabilize
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                # Read ONLY from skill-test-last-response — never fall back to
                # the raw <li> text. ApplicationAnswer.jsx renders the header
                # (participant name, "to"/"Message" reply-to text, relative
                # timestamp) and the "Thought for Ns" accordion OUTSIDE the
                # `Answer` element that carries this testid, and both of
                # those can go static (and pass a naive stability check)
                # before the real answer body starts streaming — the
                # "...toMessage less than a minute ago Thought for less than
                # a second..." false-stable signature. Treating "testid not
                # yet rendered" as content is exactly what let that header
                # text masquerade as a stabilized response.
                if self.skill_test_last_response.count() > 0:
                    current = self.skill_test_last_response.last.text_content() or ""
                else:
                    current = ""
            except Exception:
                current = ""

            if not current.strip():
                # Not ready yet (testid absent, or Answer rendered with no
                # content inside it). Reset the stability window instead of
                # letting an empty/absent read masquerade as "unchanged".
                logger.debug("skill-test-last-response not present or empty, waiting...")
                last_content = ""
                stable_start = time.time()
                self.page.wait_for_timeout(300)
                continue

            # Skip if still showing loading message
            is_loading = any(phrase in current for phrase in loading_phrases)
            if is_loading:
                logger.debug("Still loading: %r", current[:50] if current else "")
                self.page.wait_for_timeout(300)
                continue

            if current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Embedded chat response stabilized (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(300)

        logger.warning("Embedded chat response did not stabilize within timeout")

    def get_chat_artifact_file_names(self, timeout: int = 10000) -> list[str]:
        """Return the names of all artifact file cards shown in the last chat message.

        After an agent creates files via the Artifact toolkit, the chat
        response renders a ``data-testid="chat-artifact-file-list"`` container
        holding individual ``data-testid="chat-artifact-file-card"`` cards,
        each carrying a ``data-name`` attribute with the file name.

        LOCATOR: Scoped to the last ``chat-message-item`` to avoid picking up
        cards from previous turns.

        Args:
            timeout: Maximum wait time for the file-list container to appear.

        Returns:
            List of file name strings (e.g. ["report1.txt", "a.txt", ...]).
            Returns an empty list if no artifact cards are present.
        """
        last_msg = self._embedded_chat_messages().last
        try:
            file_list = last_msg.locator(self.CHAT_ARTIFACT_FILE_LIST_SELECTOR)
            file_list.wait_for(state="visible", timeout=timeout)
        except TimeoutError:
            logger.warning(
                "Timed out waiting for chat-artifact-file-list after %dms — "
                "artifact cards may not have rendered",
                timeout,
            )
            raise
        except Exception:
            logger.info("No chat-artifact-file-list found in last message")
            return []

        cards = file_list.locator(self.CHAT_ARTIFACT_FILE_CARD_SELECTOR)
        count = cards.count()
        names: list[str] = []
        for i in range(count):
            name = cards.nth(i).get_attribute("data-name") or ""
            if name:
                names.append(name)
        logger.info("Artifact file cards in last message (%d): %s", len(names), names)
        return names

    def get_last_chat_message(self) -> str:
        """Return the text content of the last AI message in embedded chat.

        The AI response text is inside the last li.MuiListItem-root.
        Extracts text from the response container.

        Returns:
            Last message text as string.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return ""

        ai_msg = messages.last
        # Extract text from the answer content div
        response_div = ai_msg.locator(self.CHAT_ANSWER_CONTENT_SELECTOR)
        if response_div.count() > 0:
            text = response_div.text_content() or ""
            return text.strip()

        # Fallback: get all text from the message
        text = ai_msg.text_content() or ""
        return text.strip()

    def get_last_chat_response_text(self) -> str:
        """Return the body text of the last AI response in embedded chat.

        ``get_last_chat_message()`` looks for ``data-testid="chat-answer-content"``,
        but ``ApplicationAnswer.jsx`` only sets that testid on non-last
        messages — the *last* message uses ``data-testid="skill-test-last-response"``
        instead (``isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'``).
        So for the last message ``get_last_chat_message()`` falls through to
        raw ``text_content()``, which includes header metadata (agent name,
        "Thought for N secs" trace, timestamps) mixed into the body — unusable
        for exact-formatting assertions (ELITEA-1735 exploration). This method
        reads the correct testid for the last message directly, mirroring
        ``SkillDetailPage.get_last_test_response()``. Uses the class-level
        ``skill_test_last_response`` field (promoted out of an inline
        ``get_by_test_id()`` call in ELITEA-1735's testid-only rework — the
        testid itself was already correct and present on `main`, only its
        Python-side shape violated the page-object locator policy).

        Returns:
            Last AI response body text as string (stripped), or "" if no
            messages are present yet.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return ""

        if self.skill_test_last_response.count() > 0:
            return (self.skill_test_last_response.last.text_content() or "").strip()

        # Fall back to the general-purpose extraction for older UI builds
        # that don't render the skill-test-last-response testid.
        return self.get_last_chat_message()

    def get_last_chat_message_full_text(self) -> str:
        """Return the RAW text of the entire last embedded-chat ``<li>``.

        Unlike :meth:`get_last_chat_response_text` (which reads only the
        answer body), this includes the "Thought for Ns" trace accordion —
        where the responding model's display name (e.g. "Anthropic Claude
        4.5 Sonnet") is rendered as plain text with no dedicated testid.
        Confirmed live during ELITEA-1881 implementation
        (``ApplicationThinkView.jsx``'s reasoning-step label) — flagged in
        the ELITEA-1881 AFS Concrete Handles table as "not remediated,
        flagging for a future add-data-testid pass" rather than in scope
        for this case's own remediation. Use this only for a substring
        containment check (e.g. "is the model name present anywhere in
        this response"); it is not a clean assertion target on its own.

        Returns:
            Full raw text of the last message ``<li>``, or "" if no
            messages are present yet.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return ""
        return (messages.last.text_content() or "").strip()

    def get_outer_thought_accordion(self, timeout: int = 10000) -> Locator:
        """Return the last embedded-chat message's outer "Thought for Ns"
        accordion (``chat-answer-thought-accordion``, existing testid,
        ELITEA-2211..2215 batch).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        accordion = self._embedded_chat_messages().last.locator(
            self.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR
        )
        accordion.wait_for(state="visible", timeout=timeout)
        return accordion

    @action("Expand nested sub-agent accordion")
    def expand_nested_agent_accordion(self, agent_name: str, timeout: int = 10000) -> Locator:
        """Expand the nested sub-agent accordion for *agent_name* inside the
        last message's outer thought accordion (ELITEA-1951).

        LOCATOR: ``NESTED_AGENT_ACCORDION_SUMMARY`` — a testid added via
        ``add-data-testid`` to ``SubAgentAccordion.jsx``, keyed by the exact
        invoked sub-agent name. Idempotent: does nothing if already expanded
        (reads ``aria-expanded`` first, MUI forwards it to the summary's
        root element).

        Args:
            agent_name: Exact name of the invoked sub-agent.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The summary Locator (post-expansion).
        """
        self.get_outer_thought_accordion(timeout=timeout)
        summary = self.page.locator(self.NESTED_AGENT_ACCORDION_SUMMARY.format(agent_name))
        summary.wait_for(state="visible", timeout=timeout)
        if summary.get_attribute("aria-expanded") != "true":
            summary.click()
            self.page.wait_for_timeout(300)  # accordion expand transition
        return summary

    def get_nested_agent_accordion_details(self, agent_name: str, timeout: int = 10000) -> Locator:
        """Return the (expanded) nested sub-agent accordion's details container.

        Scoped via ``NESTED_AGENT_ACCORDION_DETAILS`` — expands the
        accordion first if it isn't already (details unmount from the DOM
        while collapsed, per ``SubAgentAccordion.jsx``'s
        ``slotProps={{transition: {unmountOnExit: true}}}``).

        Args:
            agent_name: Exact name of the invoked sub-agent.
            timeout: Maximum wait time in milliseconds.
        """
        self.expand_nested_agent_accordion(agent_name, timeout=timeout)
        details = self.page.locator(self.NESTED_AGENT_ACCORDION_DETAILS.format(agent_name))
        details.wait_for(state="visible", timeout=timeout)
        return details

    def get_nested_agent_tool_chip_locator(
        self, agent_name: str, toolkit_name: str | None = None, timeout: int = 10000
    ) -> Locator:
        """Return the Locator for ``chat-answer-tool-chip`` elements inside the
        nested sub-agent accordion for *agent_name*.

        **Two DISTINCT chips share this testid inside the same details
        container** (confirmed live, ELITEA-1951 implementation) — DOM order:
        (1) the PARENT's own "called this agent as a tool" chip, text is just
        the bare agent name (never changes — it's not a toolkit/tool call, so
        there is no "{toolkit}: {tool}" segment to fill in); (2) the
        sub-agent's OWN nested MCP tool-call chip, text
        "{toolkit}: {tool} ({agent})". Pass *toolkit_name* to filter to
        chip (2) specifically — omitting it (or using ``.first``) risks
        matching chip (1) instead, which is a real implementation mistake
        this case's own AFS didn't flag (its documented DOM order didn't
        mention chip (1) as living inside the details container too).

        Returns the LOCATOR, not read text — the chip's final "{toolkit}: {tool}
        ({agent})" text fills in progressively while the sub-agent's own tool
        call resolves (a bare ``.text_content()`` right after visibility can
        catch an in-flight intermediate render). Callers should poll for the
        expected text via ``expect(locator.first).to_contain_text(...)``
        before reading it.

        Args:
            agent_name: Exact name of the invoked sub-agent.
            toolkit_name: If given, filter to the chip whose text contains
                this toolkit name (disambiguates from the agent-name-only chip).
            timeout: Maximum wait time in milliseconds.
        """
        details = self.get_nested_agent_accordion_details(agent_name, timeout=timeout)
        chips = details.locator(self.CHAT_ANSWER_TOOL_CHIP_SELECTOR)
        if toolkit_name:
            chips = chips.filter(has_text=toolkit_name)
        return chips

    def get_nested_agent_tool_chip_texts(
        self, agent_name: str, toolkit_name: str | None = None, timeout: int = 10000
    ) -> list[str]:
        """Return the text of every ``chat-answer-tool-chip`` inside the
        nested sub-agent accordion for *agent_name* — pass *toolkit_name* to
        filter to the sub-agent's own MCP tool-call chip specifically (see
        :meth:`get_nested_agent_tool_chip_locator`'s docstring: TWO chips
        share this testid, only one of them is a toolkit/tool call).

        Reads a snapshot of CURRENT text — callers that need the tool call's
        FINAL, settled text should poll via
        :meth:`get_nested_agent_tool_chip_locator` + ``expect(...).to_contain_text()``
        first (see that method's docstring for why).
        """
        chips = self.get_nested_agent_tool_chip_locator(
            agent_name, toolkit_name=toolkit_name, timeout=timeout
        )
        chips.first.wait_for(state="visible", timeout=timeout)
        return [(chips.nth(i).text_content() or "").strip() for i in range(chips.count())]

    def get_nested_agent_model_chip_texts(self, agent_name: str, timeout: int = 10000) -> list[str]:
        """Return the text of every ``chat-answer-model-chip`` inside the
        nested sub-agent accordion for *agent_name*.
        """
        details = self.get_nested_agent_accordion_details(agent_name, timeout=timeout)
        chips = details.locator(self.CHAT_ANSWER_MODEL_CHIP_SELECTOR)
        chips.first.wait_for(state="visible", timeout=timeout)
        return [(chips.nth(i).text_content() or "").strip() for i in range(chips.count())]

    # ------------------------------------------------------------------
    # Run History panel (ELITEA-1877)
    # ------------------------------------------------------------------

    @action("Open Run History panel")
    def open_run_history(self, timeout: int = 10000):
        """Click the Run History button and wait for the panel to replace
        the Configuration form + embedded chat.

        ``RunHistoryContainer`` REPLACES the whole form+chat grid — it is
        not a tab and not an overlay — so "opened" is confirmed by waiting
        for at least one ``run-history-list-item`` row to render (the list
        fetch, ``GET .../conversations/prompt_lib/...``, is a real network
        round trip; poll rather than a fixed timeout).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening Run History panel")
        self.run_history_open_button.wait_for(state="visible", timeout=timeout)
        self.run_history_open_button.click()
        self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).first.wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Run History panel opened")

    def get_run_history_item_count(self) -> int:
        """Return the number of rows currently listed in the Run History panel.

        Returns:
            Integer count of ``run-history-list-item`` rows.
        """
        return self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).count()

    def get_run_history_item_texts(self) -> list[str]:
        """Return the full rendered text of every Run History row (ELITEA-1876).

        Each ``run-history-list-item`` row renders its Date, Version, and
        Duration columns as plain child ``<Typography>`` text nodes
        (``RunHistoryTooltipCell.jsx``) — no per-cell testid is needed, the
        row's own text already exposes all three.

        Returns:
            List of each row's full text content, in current display order.
        """
        return self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).all_text_contents()

    @action("Select Run History item")
    def select_run_history_item(self, index: int, timeout: int = 10000):
        """Click the Run History row at *index* (0 = most recent — default
        sort is Date descending) and wait for its conversation detail to load.

        Args:
            index: Zero-based row index in the currently-rendered list.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting Run History item at index %d", index)
        row = self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).nth(index)
        row.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "/elitea_core/conversation/prompt_lib/" in r.url
            and r.request.method == "GET",
            timeout=timeout,
        ):
            row.click()
        logger.info("Run History item %d selected", index)

    def is_run_history_item_selected(self, index: int, timeout: int = 5000) -> bool:
        """Return whether the Run History row at *index* carries
        ``data-selected="true"``.

        Args:
            index: Zero-based row index in the currently-rendered list.
            timeout: Maximum wait time for the row to be present.

        Returns:
            True if that row is the one currently marked selected.
        """
        row = self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).nth(index)
        row.wait_for(state="visible", timeout=timeout)
        return row.get_attribute("data-selected") == "true"

    def get_run_history_chat_messages_text(self, timeout: int = 10000) -> str:
        """Return the concatenated text of every message in the Run History
        panel's chat (the selected row's conversation).

        ``RunHistoryChat.jsx`` renders the SAME shared ``ChatMessageList``
        component as the main embedded chat, so this reuses
        ``chat_message_list``/``CHAT_MESSAGE_ITEM_SELECTOR`` unchanged —
        confirmed live: only one instance of ``chat-message-list`` exists on
        the page while History is open (the main embedded chat is unmounted).

        Waits (bounded by *timeout*) for at least one message item to render
        before reading — ``select_run_history_item()`` only awaits the
        conversation-detail GET response, which can resolve slightly ahead of
        React committing the message list, producing a transient "" read.

        Args:
            timeout: Maximum wait time in milliseconds for the first message
                item to appear before giving up and reading whatever is present.

        Returns:
            Joined text of all ``chat-message-item`` elements, or "" if none
            render within *timeout*.
        """
        messages = self._embedded_chat_messages()
        try:
            messages.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            logger.warning("No Run History chat message rendered within %dms", timeout)
        count = messages.count()
        if count == 0:
            return ""
        return "\n".join((messages.nth(i).text_content() or "") for i in range(count))

    def wait_for_sensitive_action_authorization(
        self, timeout: int = 30000, click_authorize: bool = True
    ) -> bool:
        """Wait for the Sensitive Action Authorization panel to appear.

        This panel appears when an agent tries to call a tool that is marked
        as sensitive in Admin UI Guardrails configuration.

        Args:
            timeout: Maximum wait time in milliseconds.
            click_authorize: If True, clicks the Authorize button when panel appears.

        Returns:
            True if the authorization panel appeared, False otherwise.
        """
        logger.info("Waiting for Sensitive Action Authorization panel")
        try:
            self.sensitive_action_panel.wait_for(state="visible", timeout=timeout)
            logger.info("Sensitive Action Authorization panel appeared")

            if click_authorize:
                self.sensitive_action_authorize_button.first.click()
                self.page.wait_for_timeout(2000)
                logger.info("Clicked Authorize button")

            return True
        except Exception:
            logger.warning("Sensitive Action Authorization panel did NOT appear within %dms", timeout)
            return False

    # ------------------------------------------------------------------
    # Actions menu (three-dot menu)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the three-dot actions menu on the agent detail page.

        Uses JavaScript click to bypass MUI overlay interception.
        """
        logger.info("Opening actions menu")
        self.actions_menu_button.evaluate("el => el.click()")
        self.actions_menu.wait_for(state="visible", timeout=5000)

    @action("Delete agent")
    def delete_agent_via_menu(self, timeout: int = 10000):
        """Delete the current agent via the three-dot menu.

        Opens the menu, clicks "Delete agent", types the agent name into
        the confirmation dialog, and clicks Delete.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting agent via menu")
        # Read the current agent name before opening the menu
        agent_name = self.get_name()

        self.open_actions_menu()
        self.delete_agent_menuitem.click()

        # Handle type-to-confirm dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)

        # Type the agent name into the confirmation input
        Dialog.type_to_confirm(dialog, agent_name)
        self.page.wait_for_timeout(300)

        # Click the Delete button
        Dialog.click_button(dialog, "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Agent deleted via menu")

    @action("Export agent via menu")
    def export_agent_via_menu(self, timeout: int = 10000) -> Download:
        """Export the current Agent version via the actions overflow menu
        (ELITEA-1794).

        Opens the overflow (three-dot) menu (``open_actions_menu()``) and
        clicks the VERSION-scoped "Export" menuitem — located between "Set
        as a default" (disabled) and "Share" in the menu's VERSION group
        (``ApplicationControls.jsx`` / ``useExportApplicationMenu()``).
        Resolved via the ``agent-actions-export-menuitem`` data-testid (added
        via `add-data-testid` in ELITEA-1794's testid-only rework; see
        EliteaUI draft PR #549) — analogous to the Skill overflow menu's
        export item (``export-version-menuitem`` data-testid).

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object for the exported
            ``{agent-name}.agent.md`` file.
        """
        logger.info("Exporting agent via actions menu")
        self.open_actions_menu()

        with self.page.expect_download(timeout=timeout) as download_info:
            self.export_agent_menuitem.click()

        download = download_info.value
        logger.info("Agent exported — filename: %s", download.suggested_filename)
        return download

    # ------------------------------------------------------------------
    # Fork wizard (ELITEA-1893)
    # ------------------------------------------------------------------

    @action("Open Fork wizard")
    def open_fork_wizard(self, timeout: int = 10000):
        """Open the Fork wizard via the actions overflow menu (VERSION group).

        Opens the overflow (three-dot) menu (``open_actions_menu()``) and
        clicks the VERSION-scoped "Fork" menuitem, then waits for the
        wizard dialog (``agent-import-preview-dialog``, titled "Fork
        parameters") to become visible.

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening Fork wizard via actions menu")
        self.open_actions_menu()
        self.fork_menuitem.click()
        self.fork_wizard_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Fork wizard dialog visible")

    @action("Select Fork target project")
    def select_fork_target_project(self, project_id: int, timeout: int = 10000):
        """Open the Fork wizard's Project selector and pick a target project.

        LOCATOR: ``fork_project_select_trigger`` opens the dropdown; the
        option is resolved via the dynamic ``select-option-{project_id}``
        testid (see ``FORK_PROJECT_OPTION`` above) — a stable, semantic
        handle keyed by the project's actual numeric id, not its list
        position (confirmed live, ELITEA-1893 AFS).

        Args:
            project_id: Numeric id of the target project (must differ from
                the agent's current project).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting Fork target project id=%d", project_id)
        self.fork_project_select_trigger.click()
        option = self.page.locator(self.FORK_PROJECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("Fork target project id=%d selected", project_id)

    @action("Confirm Fork")
    def confirm_fork(self, timeout: int = 15000):
        """Click the Fork wizard's "Fork" confirm button.

        Waits for the dialog to re-render in place as the "Fork Complete"
        state (``agent-import-complete-dialog`` — same container, testid
        swaps once the fork operation succeeds; see class docstring note
        on ``fork_wizard_dialog``/``fork_complete_dialog``).

        Args:
            timeout: Maximum wait time in milliseconds for the success dialog.
        """
        logger.info("Confirming Fork")
        self.fork_confirm_button.click()
        self.fork_complete_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Fork Complete dialog visible")

    @action("Confirm Fork complete (Got it)")
    def confirm_fork_complete(self, timeout: int = 15000) -> int:
        """Click "Got it" on the Fork Complete dialog.

        Auto-navigates to the newly forked Agent's detail page, inside the
        target project. Parses and returns the new Agent's numeric ID from
        the resulting URL.

        Args:
            timeout: Maximum wait time in milliseconds for the navigation.

        Returns:
            The forked Agent's numeric ID.
        """
        self.fork_complete_got_it_button.click()
        self.page.wait_for_url(re.compile(r".*/agents/all/\d+"), timeout=timeout)
        self.wait_for_network(timeout=5000)

        match = re.search(r"/agents/all/(\d+)", self.page.url)
        if not match:
            raise ValueError(
                f"Could not parse forked Agent ID from URL: {self.page.url}"
            )
        forked_agent_id = int(match.group(1))
        logger.info(
            "Fork complete — navigated to forked agent id=%d (%s)",
            forked_agent_id, self.page.url,
        )
        return forked_agent_id

    # ------------------------------------------------------------------
    # Publish / Unpublish wizard (ELITEA-1892)
    # ------------------------------------------------------------------

    def close_actions_menu(self, timeout: int = 5000):
        """Close the open actions (three-dot) menu by pressing Escape.

        Mirrors :meth:`close_versions_menu`'s Escape-press pattern for the
        VERSION-options menu. Needed between two separate
        :meth:`open_actions_menu` calls in the same test (e.g. checking the
        VERSION group's menuitem before *and* after Publish/Unpublish).
        """
        self.page.keyboard.press("Escape")
        self.actions_menu.wait_for(state="hidden", timeout=timeout)

    @action("Open Publish wizard")
    def open_publish_wizard(self, timeout: int = 10000):
        """Open the Publish wizard via the actions overflow menu (VERSION group).

        Opens the overflow menu and clicks the VERSION-scoped "Publish"
        menuitem, then waits for the wizard's Preparation step (the
        version-name input) to render. Confirmed live: `usePublishVersion
        .hooks.js`'s ``canShowPublish`` gate requires
        ``applications.publish`` permission AND the version's status to be
        Draft — only render this menuitem when both hold.

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening Publish wizard via actions menu")
        self.open_actions_menu()
        self.publish_version_menuitem.click()
        Dialog.wait_for(self.page, timeout=timeout)
        self.publish_version_name_input.wait_for(state="visible", timeout=timeout)
        logger.info("Publish wizard Preparation step visible")

    @action("Fill the Publish wizard's Preparation step")
    def fill_publish_preparation_step(
        self, version_name: str, category_name: str, timeout: int = 10000
    ):
        """Fill the Preparation step: version name, Category, agree-checkbox.

        Call after :meth:`open_publish_wizard`. All three fields are
        required to enable "Continue" — Category and the Publishing-Terms
        checkbox are NOT named in the TMS case text (CLARIFICATION #612)
        but are hard requirements in the live product.

        Args:
            version_name: Name for the new (to-be-published) version, e.g.
                ``"v1-release"``.
            category_name: Exact display label of the Category option to
                select, e.g. ``"Quality Assurance"``.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info(
            "Filling Publish wizard Preparation step — version=%r category=%r",
            version_name, category_name,
        )
        self.publish_version_name_input.click()
        self.publish_version_name_input.press_sequentially(version_name, delay=50)

        self.publish_category_select.click()
        option = self.page.locator(self.PUBLISH_CATEGORY_OPTION.format(category_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()

        self.publish_agree_checkbox.click()
        logger.info("Publish wizard Preparation step filled")

    def is_publish_continue_enabled(self) -> bool:
        """Return whether the Preparation step's "Continue" button is enabled."""
        return self.publish_continue_button.is_enabled()

    @action("Continue from Publish wizard Preparation step")
    def click_publish_continue(self, timeout: int = 15000) -> int:
        """Click "Continue" and wait for the ``publish_validate`` response.

        Waits for ``POST .../publish_validate/prompt_lib/{project}/{versionId}``
        (AFS § Network Behavior — never a fixed sleep) and returns its HTTP
        status: ``200`` when the AI content-quality gate passes (no
        Critical issues — the Validation step's "Publish" button becomes
        enabled), ``422`` when Critical issues remain (button stays
        disabled).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            HTTP status code of the ``publish_validate`` response.
        """
        logger.info("Clicking Publish wizard Continue")
        with self.page.expect_response(
            lambda r: "publish_validate" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as validate_info:
            self.publish_continue_button.click()
        status = validate_info.value.status
        # The response resolving does not guarantee the Validation step's DOM
        # has re-rendered yet (one more React tick) — confirmed live: an
        # immediate is_visible() check on publish_confirm_button raced and
        # returned False even though the button rendered moments later.
        # The button itself is always present on the Validation step
        # regardless of the Critical-issue outcome (only its enabled state
        # differs — canPublish = status !== 'FAIL'), so waiting for
        # visibility here is safe for both the 200 and 422 cases.
        self.publish_confirm_button.wait_for(state="visible", timeout=timeout)
        logger.info("publish_validate responded status=%d", status)
        return status

    @action("Confirm Publish")
    def confirm_publish(self, timeout: int = 15000) -> int:
        """Click the Validation step's "Publish" button and wait for the
        publish request to resolve.

        Waits for ``POST .../publish/prompt_lib/{project}/{versionId}`` to
        resolve and returns its HTTP status — callers should assert 200.
        Publish clones the Draft version into a brand-new version that
        carries the Published status; it does not flip the original Draft
        version's status in place (AFS Axis 2).

        Does NOT wait for / assert on a post-publish navigation: confirmed
        live (ELITEA-1892 exploration, filed as
        https://github.com/EliteaAI/elitea-testing-public/issues/614) that
        the app's own auto-navigation to the new version is unreliable — it
        can briefly navigate to the new version's URL and then silently
        revert to the previously-active version, with no error surfaced
        (network trace: two ``GET .../version/.../{new_id}`` calls
        immediately followed by two ``GET .../version/.../{old_id}`` calls).
        The underlying data is unaffected (verified via API — the new
        version really is ``published``); only the client-side navigation
        is unreliable. Callers MUST use :meth:`select_version_by_name` to
        reliably land on the new version afterward — do not assume Publish
        alone leaves you there.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            HTTP status code of the ``publish`` response.
        """
        logger.info("Confirming Publish")
        with self.page.expect_response(
            lambda r: "/publish/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as publish_info:
            self.publish_confirm_button.click()
        status = publish_info.value.status
        self.wait_for_network(timeout=timeout)
        logger.info("Publish confirmed — status=%d", status)
        return status

    @action("Continue from Publish wizard Preparation step, capturing the raw response")
    def click_publish_continue_and_capture_response(self, timeout: int = 15000):
        """Click "Continue" and wait for the ``publish_validate`` response,
        returning the raw Playwright ``Response`` (not just the status).

        Additive sibling of :meth:`click_publish_continue` — that method's
        ``int``-only return is an established contract with real callers
        (``test_agent_publish_unpublish_version.py``,
        ``test_agent_version_selector_order.py``); this method exists
        because callers that need the response BODY (``critical_issues[]``/
        ``warnings[]``/``recommendations[]`` — each entry carrying
        ``field``/``context``/``issue``/``fix``, per
        ``ValidationResult.jsx``'s ``buildPlainText()``) cannot get it from
        an ``int``. Mirrors ``SkillDetailPage.click_publish_continue()``'s
        own ``Response``-returning shape (ELITEA-2597), added here for the
        AGENT entity (ELITEA-2601 — per-skill validation-issue attribution
        assertions need the ``context: "skill: <name>"`` field, which only
        the response body carries).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The matched Playwright ``Response`` for the
            ``publish_validate`` call.
        """
        logger.info("Clicking Publish wizard Continue (capturing response)")
        with self.page.expect_response(
            lambda r: "publish_validate" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as validate_info:
            self.publish_continue_button.click()
        response = validate_info.value
        self.publish_confirm_button.wait_for(state="visible", timeout=timeout)
        logger.info("publish_validate responded status=%d", response.status)
        return response

    def is_publish_confirm_enabled(self) -> bool:
        """Return whether the Validation step's "Publish" button is enabled.

        Mirrors ``SkillDetailPage.is_publish_confirm_enabled()`` — added
        here for the AGENT entity (ELITEA-2601), which previously only had
        ``is_publish_continue_enabled()`` for the Preparation step.
        """
        return self.publish_confirm_button.is_enabled()

    @action("Confirm Publish, capturing the raw response")
    def confirm_publish_and_capture_response(self, timeout: int = 15000):
        """Click the Validation step's "Publish" button and wait for the
        ``publish`` request to resolve, returning the raw Playwright
        ``Response`` (not just the status).

        Additive sibling of :meth:`confirm_publish` — same reconciliation
        rationale as :meth:`click_publish_continue_and_capture_response`
        above: ``confirm_publish()`` is an established ``int``-returning
        contract with real callers, so a ``Response``-returning override
        would silently shadow it. Callers that need the response BODY's
        ``error``/``msg`` fields (e.g. distinguishing the AGENT entity's
        ``validation_failed`` "modified since validation" rejection,
        ELITEA-2601) use this method instead. Mirrors
        ``SkillDetailPage.confirm_publish_and_capture_response()``.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The matched Playwright ``Response`` for the ``publish`` call.
        """
        logger.info("Confirming Publish (capturing response)")
        with self.page.expect_response(
            lambda r: "/publish/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as publish_info:
            self.publish_confirm_button.click()
        response = publish_info.value
        logger.info("Publish confirmed — status=%d", response.status)
        return response

    def get_publish_error_message(self, timeout: int = 5000) -> str:
        """Return the Publish wizard's inline error Alert text.

        LOCATOR: ``publish-wizard-error-alert`` (pre-existing, shared with
        the Skill flow — see the ``publish_error_alert`` field docstring).
        Renders the SAME ``msg`` text the ``publish`` response body
        carries, inline in the Validation step, once a rejected publish
        attempt (e.g. a stale ``validation_failed`` token) lands.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.publish_error_alert.wait_for(state="visible", timeout=timeout)
        return (self.publish_error_alert.text_content() or "").strip()

    @action("Close Publish wizard via Escape")
    def close_publish_wizard(self, timeout: int = 5000):
        """Close the Publish wizard dialog by pressing Escape.

        Mirrors ``SkillDetailPage.close_publish_wizard()`` — added here for
        the AGENT entity (ELITEA-2601). Escape calls the SAME ``onClose``
        handler as the (untestid'd) "Cancel" button, and both re-opening
        and closing reset the shared wizard's state, so re-opening after
        this always starts a fresh Preparation step (confirmed live,
        ELITEA-2601, matching the Skill flow's already-documented shape).

        Args:
            timeout: Maximum wait time in milliseconds for the dialog to hide.
        """
        logger.info("Closing Publish wizard via Escape")
        self.page.keyboard.press("Escape")
        self.publish_confirm_button.wait_for(state="hidden", timeout=timeout)
        logger.info("Publish wizard closed")

    @action("Select a version by name from the VERSION dropdown")
    def select_version_by_name(
        self, version_name: str, timeout: int = 10000, attempts: int = 2
    ) -> str:
        """Explicitly select a version from the VERSION dropdown and wait
        for its data to load, returning its numeric id.

        The reliable way to land on (and stay on) a specific version — see
        :meth:`confirm_publish`'s docstring for why auto-navigation after
        Publish cannot be trusted (issue #614). Explicitly opening the
        VERSION dropdown and clicking a named option is a normal,
        deliberate user action and was confirmed live to navigate
        correctly and durably (no reversion observed after selecting this
        way).

        Each attempt is a full select+reload CYCLE (re-open the dropdown,
        re-click the option, reload) — not just a re-poll of an
        already-open dropdown — mirroring
        :meth:`wait_for_publish_status_menuitem`'s bounded-attempts shape.
        Escalation added PR #615 review round 2: confirmed live that even
        the single reload this method already performed as belt-and-braces
        can occasionally still not be enough on its own (~1/10 runs
        observed during this case's verification) — the underlying store
        can still be mid-sync across one reload — so a second full cycle
        is attempted before giving up.

        This method stays DOM-only by design (page objects never reach
        into the API layer — see project layering) and always raises on a
        poll that never converges; it does NOT itself decide whether that
        timeout is #614's cosmetic staleness or a different, real bug.
        Callers that need that distinction (e.g. to route a *confirmed*
        #614 occurrence into a soft-assertion mechanism) should catch the
        ``AssertionError`` and independently confirm the version's real
        status via the API before treating it as the known defect — see
        ``test_agent_publish_unpublish_version.py``'s
        ``_confirm_new_version_via_api()`` for the reference pattern.

        Args:
            version_name: Exact version name to select, e.g. ``"v1-release"``.
            timeout: Maximum wait time in milliseconds, per wait condition.
            attempts: Number of full select+reload cycles to try.

        Returns:
            The selected version's numeric id, read from the Information
            panel once the wait condition confirms the VERSION trigger
            text, the Information panel's version-id, and the URL all
            agree (the same three-way consistency check as documented for
            the Save As Version flow's race — see :meth:`confirm_new_version`).

        Raises:
            AssertionError: if the version-id-matches condition never
                converges after ``attempts`` full select+reload cycles.
                The message notes issue #614 as the SUSPECTED cause (DOM
                status staleness) — this is a hypothesis, not a confirmed
                diagnosis; only a caller-side API check can confirm it.
        """
        logger.info("Selecting version %r from the VERSION dropdown", version_name)

        version_id_matches_js = """name => {
            const trigger = document.querySelector('[data-testid="agent-version-selector-trigger"]');
            const versionIdEl = document.querySelector('[data-testid="copy-version-id"]');
            if (!trigger || trigger.innerText.trim() !== name) return false;
            if (!versionIdEl) return false;
            const currentId = versionIdEl.innerText.trim();
            if (!currentId) return false;
            const seg = window.location.pathname.split('/').filter(Boolean).pop();
            return seg === currentId;
        }"""

        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            self.open_version_selector()
            option = self.page.locator(self.VERSION_OPTION.format(version_name))
            option.wait_for(state="visible", timeout=timeout)
            option.click()

            try:
                self.page.wait_for_function(
                    version_id_matches_js, arg=version_name, timeout=timeout
                )
            except Exception as exc:  # noqa: BLE001 - retried below, re-raised with context above
                last_exc = exc
                logger.warning(
                    "select_version_by_name: VERSION trigger/id/URL never "
                    "agreed on %r pre-reload (attempt %d/%d) — retrying",
                    version_name, attempt, attempts,
                )
                continue

            # Belt-and-braces (issue #614): the VERSION trigger/URL/Information-
            # panel id can agree while OTHER version-scoped client state (the
            # overflow menu's Publish/Unpublish item, driven by the version's
            # `status` field from a separate store) still lags — confirmed live
            # to occasionally persist across several menu re-opens, not just a
            # single render tick. A hard reload forces every panel to refetch
            # fresh from the server (which is always correct per the API), so
            # it clears staleness a same-page re-render cannot. Uses the SAME
            # precise wait condition (not a generic "page loaded" heuristic) to
            # avoid reading an intermediate, not-yet-hydrated paint.
            self.page.reload(wait_until="domcontentloaded")
            try:
                self.page.wait_for_function(
                    version_id_matches_js, arg=version_name, timeout=timeout
                )
            except Exception as exc:  # noqa: BLE001 - retried below, re-raised with context above
                last_exc = exc
                logger.warning(
                    "select_version_by_name: VERSION trigger/id/URL never "
                    "agreed on %r post-reload (attempt %d/%d) — retrying the "
                    "full select+reload cycle (issue #614 escalation)",
                    version_name, attempt, attempts,
                )
                continue

            selected_version_id = self.get_version_id()
            logger.info(
                "Version %r selected — id=%s (URL: %s)",
                version_name, selected_version_id, self.page.url,
            )
            return selected_version_id

        raise AssertionError(
            f"select_version_by_name: VERSION trigger/Information-panel id/"
            f"URL never converged on {version_name!r} after {attempts} full "
            f"select+reload attempts (suspected issue #614 client-side "
            f"status staleness — caller must independently confirm via the "
            f"API before treating this as the known defect) — last error: "
            f"{last_exc}"
        )

    def wait_for_version_trigger_and_id(
        self, version_name: str, version_id: str, timeout: int = 10000
    ) -> None:
        """Wait until the VERSION selector trigger AND the Information
        panel's version-id both agree with the given ``(version_name,
        version_id)`` pair.

        Same client-state race documented on :meth:`confirm_new_version`
        ("the URL's version-id segment updates before the VERSION
        selector's displayed text re-renders — a race, not a fixed delay")
        and :meth:`select_version_by_name` (the three-way
        trigger/version-id/URL convergence check) — this is the two-way
        (trigger, version-id) form for a caller that already trusts the URL
        (e.g. a fresh tab opened by navigating directly to a
        version-specific copied link, ELITEA-1898) and only needs the
        CLIENT-SIDE render state to catch up post-navigation.

        LOCATOR: polls ``agent-version-selector-trigger`` and
        ``copy-version-id`` via ``document.querySelector`` inside the
        predicate — ``wait_for_function`` executes in-page JS, which cannot
        reference a Playwright ``Locator`` directly, so the two testids
        (also the ``version_selector_trigger`` / ``copy_version_id_button``
        ``LocatorDescriptor`` fields above) are inlined as literal
        ``[data-testid="…"]`` strings here rather than duplicated as a
        second selector elsewhere.

        Args:
            version_name: Expected VERSION-selector trigger text, e.g.
                ``"v1-test"``.
            version_id: Expected version id, as rendered by
                ``copy-version-id`` (i.e. :meth:`get_version_id`'s value).
            timeout: Maximum wait time in milliseconds.
        """
        self.page.wait_for_function(
            """([name, expectedId]) => {
                const trigger = document.querySelector(
                    '[data-testid="agent-version-selector-trigger"]'
                );
                const versionIdEl = document.querySelector(
                    '[data-testid="copy-version-id"]'
                );
                if (!trigger || trigger.innerText.trim() !== name) return false;
                if (!versionIdEl) return false;
                return versionIdEl.innerText.trim() === expectedId;
            }""",
            arg=[version_name, version_id],
            timeout=timeout,
        )
        logger.info(
            "VERSION trigger/version-id converged on name=%r id=%r",
            version_name, version_id,
        )

    def wait_for_publish_status_menuitem(
        self, expect_unpublish: bool, timeout: int = 10000, attempts: int = 4
    ) -> None:
        """Poll the actions overflow menu (closing and reopening between
        attempts) until it shows the expected Publish/Unpublish menuitem.

        Confirmed live (issue #614): the overflow menu's Publish/Unpublish
        menuitem can render from a STALE version-status snapshot for a beat
        even after the VERSION selector, Information-panel version-id, and
        URL have all already agreed on the correct version (observed in
        ~1/4 runs during this case's implementation) — a single
        point-in-time ``is_visible()`` check right after switching versions
        is not reliable. Re-opening the menu (a fresh render pass) is what
        picks up the corrected status, so this closes and reopens between
        bounded attempts rather than polling a single already-open menu
        (MUI doesn't live-update an already-rendered menu's items).

        This method stays DOM-only by design (page objects never reach
        into the API layer — see project layering) and always raises on a
        poll that never converges; it does NOT itself decide whether that
        timeout is #614's cosmetic staleness or a different, real bug.
        Callers that need that distinction (e.g. to route a *confirmed*
        #614 occurrence into a soft-assertion mechanism) should catch the
        ``AssertionError`` and independently confirm the version's real
        status via the API before treating it as the known defect — see
        ``test_agent_publish_unpublish_version.py``'s
        ``_confirm_version_status_via_api()`` for the reference pattern.

        Args:
            expect_unpublish: ``True`` to wait for "Unpublish" (Published
                version), ``False`` to wait for "Publish" (Draft version).
            timeout: Total time budget in milliseconds, split across attempts.
            attempts: Number of open/check/close cycles to try.

        Raises:
            AssertionError: if the expected menuitem never appeared. The
                message notes issue #614 as the SUSPECTED cause (DOM status
                staleness) — this is a hypothesis, not a confirmed
                diagnosis; only a caller-side API check can confirm it.
        """
        target = self.unpublish_version_menuitem if expect_unpublish else self.publish_version_menuitem
        label = "Unpublish" if expect_unpublish else "Publish"
        per_attempt_timeout = max(timeout // attempts, 1000)
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            self.open_actions_menu()
            try:
                target.wait_for(state="visible", timeout=per_attempt_timeout)
                logger.info(
                    "Actions menu shows %r on attempt %d/%d", label, attempt, attempts
                )
                return
            except Exception as exc:  # noqa: BLE001 - re-raised with context below
                last_exc = exc
                logger.warning(
                    "Actions menu did not show %r on attempt %d/%d — retrying",
                    label, attempt, attempts,
                )
                self.close_actions_menu()

        # Escalation (PR #615 review round 2): the close/reopen loop above
        # forces a fresh RENDER but not a fresh FETCH — per the observed
        # residual flake (~1/10 runs), the underlying store can still be
        # mid-sync even across several re-renders. A full reload (the same
        # belt-and-braces technique :meth:`select_version_by_name` already
        # uses for this exact defect) forces every panel — including
        # whatever store backs this menuitem — to refetch fresh from the
        # server, clearing staleness a same-page re-render alone cannot.
        # One extra open/check after the reload before giving up.
        logger.warning(
            "Actions menu never showed %r after %d attempts — reloading "
            "and retrying once more (issue #614 escalation)",
            label, attempts,
        )
        self.page.reload(wait_until="domcontentloaded")
        try:
            self.wait_for_network(timeout=per_attempt_timeout)
        except Exception:
            # networkidle is a best-effort settle, not a hard requirement —
            # this app keeps persistent WebSocket connections open (same
            # documented behavior as BasePage.navigate(), which wraps this
            # exact wait in the same try/except for the same reason), so
            # networkidle can legitimately never fire. domcontentloaded
            # (already awaited by the reload above) is what actually
            # matters here. PR #615 review round 2 bugfix: this call was
            # previously unguarded, so a networkidle timeout leaked a raw
            # Playwright TimeoutError straight past this method's own
            # AssertionError contract (observed live: "Timeout 2500ms
            # exceeded" bypassing the caller's except AssertionError
            # handling entirely) instead of feeding into the bounded-
            # attempts/AssertionError flow callers rely on.
            logger.debug(
                "networkidle not reached after reload escalation for %r — "
                "continuing (persistent WebSocket connections expected)",
                label,
            )
        self.open_actions_menu()
        try:
            target.wait_for(state="visible", timeout=per_attempt_timeout)
            logger.info("Actions menu shows %r after reload escalation", label)
            return
        except Exception as exc:  # noqa: BLE001 - re-raised with context below
            last_exc = exc
            self.close_actions_menu()

        raise AssertionError(
            f"Actions menu never showed the expected {label!r} menuitem "
            f"after {attempts} attempts plus a reload escalation (suspected "
            f"issue #614 client-side status staleness — caller must "
            f"independently confirm via the API before treating this as "
            f"the known defect) — last error: {last_exc}"
        )

    @action("Open Unpublish confirm dialog")
    def open_unpublish_dialog(self, timeout: int = 10000):
        """Open the Unpublish confirmation dialog via the actions overflow menu.

        Opens the overflow menu and clicks the VERSION-scoped "Unpublish"
        menuitem (only rendered for a Published version —
        ``useUnpublishVersionMenu.hooks.jsx``'s ``canUnpublish`` gate), then
        waits for the "Unpublish Agent" confirmation dialog
        (``UnpublishConfirmModal.jsx``) to become visible.

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening Unpublish confirm dialog via actions menu")
        self.open_actions_menu()
        self.unpublish_version_menuitem.click()
        Dialog.wait_for(self.page, timeout=timeout)
        self.unpublish_confirm_button.wait_for(state="visible", timeout=timeout)
        logger.info("Unpublish confirm dialog visible")

    @action("Confirm Unpublish")
    def confirm_unpublish(self, timeout: int = 15000) -> int:
        """Click the Unpublish confirm dialog's "Unpublish" button.

        Waits for ``POST .../unpublish/prompt_lib/{project}/{versionId}`` to
        resolve and for the dialog to close. Callers should assert the
        returned status is 200.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            HTTP status code of the ``unpublish`` response.
        """
        logger.info("Confirming Unpublish")
        with self.page.expect_response(
            lambda r: "/unpublish/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as unpublish_info:
            self.unpublish_confirm_button.click()
        status = unpublish_info.value.status
        Dialog.wait_for_hidden(self.page, timeout=timeout)
        logger.info("Unpublish confirmed — status=%d", status)
        return status

    @action("Set the currently-viewed version as the agent's default")
    def set_current_version_as_default(self, timeout: int = 10000) -> int:
        """Pin the CURRENTLY VIEWED version as the agent's default version
        (ELITEA-1891).

        Opens the actions overflow menu, clicks "Set as a default"
        (``set_as_default_menuitem``), and confirms in the
        ``SetDefaultVersionDialog`` that opens
        (``useSetDefaultVersion.hooks.jsx``'s ``handleSetDefaultVersion`` —
        it pins whichever version is currently loaded into the form, not a
        version picked from this method's arguments). Waits for the
        ``PATCH .../default_version/prompt_lib/{project}/{applicationId}``
        request to resolve and for the dialog to close.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            HTTP status code of the ``default_version`` PATCH response.
        """
        logger.info("Setting the currently-viewed version as default")
        self.open_actions_menu()
        self.set_as_default_menuitem.click()
        Dialog.wait_for(self.page, timeout=timeout)
        self.set_default_version_confirm_button.wait_for(state="visible", timeout=timeout)

        with self.page.expect_response(
            lambda r: "/default_version/prompt_lib/" in r.url and r.request.method == "PATCH",
            timeout=timeout,
        ) as set_default_info:
            self.set_default_version_confirm_button.click()
        status = set_default_info.value.status
        Dialog.wait_for_hidden(self.page, timeout=timeout)
        logger.info("Set-as-default confirmed — status=%d", status)
        return status

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    @action("Navigate back")
    def click_back_button(self, timeout: int = 5000):
        """Click the back arrow button on the agent detail page.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking back button")
        self.back_button.click()
        self.wait_for_network(timeout=timeout)
