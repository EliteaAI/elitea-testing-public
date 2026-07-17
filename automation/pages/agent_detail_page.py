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
    toolkit_card = LocatorDescriptor(testid="agent-toolkit-card")
    toolkit_delete_button = LocatorDescriptor(testid="agent-toolkit-delete-button")
    toolkit_search_input = LocatorDescriptor(testid="toolkit-search-input")
    toolkit_warning_banner = LocatorDescriptor(testid="credential-warning-banner")
    toolkit_reload_button = LocatorDescriptor(testid="toolkit-reload-button")
    toolkit_open_button = LocatorDescriptor(testid="toolkit-open-button")

    # --- Selectors for scoped use (inside parent locators) ---
    TOOLKIT_BLOCKED_SELECTOR = '[data-testid="toolkit-blocked-banner"]'
    TOOLKIT_TOOL_BLOCKED_SELECTOR = '[data-testid="toolkit-tools-unavailable-banner"]'
    CHAT_MESSAGE_DELETE_SELECTOR = '[data-testid="chat-message-delete-button"]'
    CHAT_MESSAGE_ITEM_SELECTOR = '[data-testid="chat-message-item"]'
    CHAT_ARTIFACT_FILE_LIST_SELECTOR = '[data-testid="chat-artifact-file-list"]'
    CHAT_ARTIFACT_FILE_CARD_SELECTOR = '[data-testid="chat-artifact-file-card"]'
    CHAT_ANSWER_CONTENT_SELECTOR = '[data-testid="chat-answer-content"]'
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
    SKILL_MENTION_ITEM_SELECTOR = '[data-testid="skill-mention-item-{}"]'
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

    # --- Skills section (agent-skills attach/mention flow, ELITEA-1735) ---
    agent_add_skill_button = LocatorDescriptor(testid="agent-add-skill-button")
    # Tooltip wrapper span for the add-skill button (ELITEA-1790 testid-only
    # rework — added via add-data-testid to SkillMenu.jsx; see EliteaUI draft
    # PR #546). MUI's Tooltip clones its accessible label onto this wrapper
    # (not onto the inner, disabled BaseBtn) once the 5-skill limit is
    # reached, so it needs its own testid rather than a raw parent-traversal
    # chained off `agent_add_skill_button`.
    agent_add_skill_button_tooltip = LocatorDescriptor(testid="agent-add-skill-button-tooltip")
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

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        blocked_indicator = card.locator(self.TOOLKIT_BLOCKED_SELECTOR)
        try:
            blocked_indicator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_tool_blocked_in_toolkit(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows 'Some tools are not available anymore' indicator.

        Used to verify guardrails tool blocking is applied without pylon reload.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if tool blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        blocked_indicator = card.locator(self.TOOLKIT_TOOL_BLOCKED_SELECTOR)
        try:
            blocked_indicator.wait_for(state="visible", timeout=timeout)
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

    def _get_skill_id_from_card(self, card: Locator) -> str:
        """Extract the skill_id embedded in a card's `skill-card-{skill_id}` testid.

        Args:
            card: Locator scoped to a single skill card (from `_skill_card()`).

        Returns:
            The skill_id string parsed out of the card's data-testid attribute.
        """
        testid = card.get_attribute("data-testid") or ""
        return testid.removeprefix("skill-card-")

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

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending message in embedded chat: %s", message[:60])
        self.chat_message_input.wait_for(state="visible", timeout=timeout)
        self.chat_message_input.fill(message)
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
        stable_duration_ms: int = 3000,
        timeout: int = 60000,
    ):
        """Wait for the AI response in the embedded chat to stabilize.

        Waits for new messages to appear beyond initial_count, then waits
        for the last message's text content to stop changing for
        stable_duration_ms.

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this long (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for embedded chat response (initial_count=%d, stable=%dms, timeout=%dms)",
            initial_count, stable_duration_ms, timeout,
        )
        messages = self._embedded_chat_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message beyond initial_count
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for the last AI message to have a Delete button (= response complete)
        ai_msg = messages.last
        try:
            ai_msg.locator(self.CHAT_MESSAGE_DELETE_SELECTOR).wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilize
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                current = ai_msg.text_content() or ""
            except Exception:
                current = ""

            if current and current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Embedded chat response stabilized (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(500)

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
