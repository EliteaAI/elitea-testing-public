"""Skill Detail Page - View and manage an individual skill.

Handles: /skills/all/{skill_id}
- View/edit skill form (inherited from SkillFormPage)
- SkillTestPanel — stateless LLM prediction panel
- Overflow menu with delete skill action
"""

import re
import logging
import time
from playwright.sync_api import Page

from playwright.sync_api import Download

from .skill_form_page import SkillFormPage
from .locator_descriptor import LocatorDescriptor, OptionalLocatorDescriptor
from components.mui import Dialog
from utils.actions import action


logger = logging.getLogger("elitea.pages.skill_detail")


class SkillDetailPage(SkillFormPage):
    """Page object for the skill detail/edit page.

    Inherits form operations from SkillFormPage.
    Adds SkillTestPanel interaction and overflow menu (delete).

    URL: /skills/all/{skill_id}
    """

    # --- Navigation ---
    # Shared BackButton.jsx component (EliteaUI src/components/BackButton.jsx),
    # reused across every entity-detail page header (agents, skills,
    # credentials, ...) via StyledTabs.jsx's `leftButton` slot. Same
    # pre-existing testid already wired as AgentDetailPage.back_button
    # (automation/pages/agent_detail_page.py:542) — not a new element,
    # just not yet exposed on this page object (ELITEA-2429).
    back_button = LocatorDescriptor(testid="back-button")

    # Information section (used for wait_for_page_load)
    information_section = LocatorDescriptor(
        testid="skill-information-section",
        description="Skill information accordion section"
    )

    # SkillTestPanel outer container
    test_panel = LocatorDescriptor(
        testid="skill-test-panel",
        description="SkillTestPanel container"
    )

    # ------------------------------------------------------------------
    # LLM model selector + Model Settings dialog (SkillTestPanel, ELITEA-2436)
    # ------------------------------------------------------------------
    # These testids are NOT new — they were added on the Agent detail page's
    # embedded chat panel for ELITEA-1880/ELITEA-1881 (see
    # `agent_detail_page.py`'s equivalent fields) and are inherited for free
    # here because both pages render the exact same shared
    # `LLMModelSelector`/`LLMSettingsDialog` widget
    # (`src/[fsd]/widgets/llm-model-selector/`). Only `model_settings_apply_button`
    # (now-live, no prior LocatorDescriptor field on either page) and
    # `model_settings_creativity_slider`/its `-input` twin (added via
    # add-data-testid for THIS case, see below) are new.
    model_selector_button = LocatorDescriptor(testid="model-selector-button")
    model_selector_name = LocatorDescriptor(testid="model-selector-name")
    MODEL_SELECTOR_OPTION_ANY_SELECTOR = '[data-testid^="model-selector-option-"]'

    model_settings_button = LocatorDescriptor(
        testid="model-settings-button",
        description="Gear icon next to the model selector — opens the Model settings dialog",
    )
    model_settings_dialog = LocatorDescriptor(testid="model-settings-dialog")
    model_settings_cancel_button = LocatorDescriptor(testid="model-settings-cancel-button")
    # New finding (AFS Concrete Handles): this testid now exists on
    # LLMSettingsDialog.jsx's Apply button (it did not at ELITEA-1880
    # analysis time) but had no LocatorDescriptor field on either detail
    # page yet.
    model_settings_apply_button = LocatorDescriptor(testid="model-settings-apply-button")
    # Reasoning-capable models render this slider (Low/Medium/High); a
    # non-reasoning model renders CreativitySlider instead.
    model_settings_reasoning_slider = LocatorDescriptor(testid="model-settings-reasoning-slider")
    # Non-reasoning models (e.g. gpt-5-mini) render this slider instead of
    # Reasoning. Wrapper testid added via add-data-testid for ELITEA-2436
    # (CreativitySlider.jsx, mirroring ReasoningSlider.jsx's existing
    # `testId="model-settings-reasoning-slider"` prop-threading through the
    # shared DiscreteSlider.jsx). A SECOND, distinct `inputTestId` prop was
    # also threaded through DiscreteSlider (declared improvisation — the AFS
    # only asked for the wrapper; MUI's `<Slider>` renders the interactive
    # `<input type="range">` as a separate internal node the wrapper's
    # data-testid never reaches, same family as the documented
    # "MUI testid lands on wrapper, not input" gotcha) — this case's step 2
    # must MOVE the slider, not just assert its presence, so the underlying
    # input needs its OWN testid rather than reusing the AFS's suggested
    # `[aria-label="Creativity level"]` raw handle or the pre-existing raw
    # `input[aria-valuemin=...]` precedent in
    # `user_profile_settings_page.py::set_speed()` (tracked tech debt, not
    # precedent per `.agents/testing.md`). Scoped ONLY to CreativitySlider —
    # ReasoningSlider does NOT receive `inputTestId` since this case never
    # drives the Reasoning slider's input (canon #511 scope discipline).
    model_settings_creativity_slider = LocatorDescriptor(testid="model-settings-creativity-slider")
    model_settings_creativity_slider_input = LocatorDescriptor(
        testid="model-settings-creativity-slider-input",
        description="The real <input type=range> inside the Creativity slider "
                     "wrapper — use this (not the wrapper) to focus + arrow-key "
                     "the slider value",
    )
    model_settings_max_tokens_section = LocatorDescriptor(testid="model-settings-max-tokens-section")

    # Dynamic (runtime-parameterized) testid for a model-selector dropdown
    # option, keyed by the model's stable API `name` (mirrors
    # AgentDetailPage's identical constant/pattern).
    MODEL_SELECTOR_OPTION = '[data-testid="model-selector-option-{}"]'
    # Dynamic testid for a Reasoning-slider level mark (1=Low, 2=Medium, 3=High).
    MODEL_SETTINGS_REASONING_LEVEL = '[data-testid="model-settings-reasoning-level-{}"]'

    # ------------------------------------------------------------------
    # SkillTestPanel response action buttons (ELITEA-2442)
    # ------------------------------------------------------------------
    # Same underlying ApplicationAnswer.jsx component the Chat surface
    # renders (ELITEA-2436 precedent) — both testids already exist live,
    # only the LocatorDescriptor field was missing on this page. Mirrors
    # ChatPage.read_out_button / ChatPage.copy_action_button exactly
    # (chat_page.py:526 / :481); SkillDetailPage has no shared base with
    # ChatPage so the fields are duplicated here, not inherited.
    read_out_button = LocatorDescriptor(
        testid="chat-read-out-button",
        description="Read out (speaker) button on the test-panel AI response",
    )
    copy_action_button = LocatorDescriptor(
        testid="chat-copy-button",
        description="Copy-to-clipboard button on the test-panel AI response",
    )
    # Voice mini player — appears after clicking Read out (Layer 2 proof).
    # Mirrors ChatPage.voice_mini_player (OptionalLocatorDescriptor since the
    # container is not present until Read-out is clicked).
    voice_mini_player = OptionalLocatorDescriptor(
        testid="chat-voice-mini-player",
        description="Voice mini player container, appears after Read-out click",
    )
    voice_play_stop_button = LocatorDescriptor(
        testid="chat-voice-play-stop-button",
        description="Play/Stop button in the voice mini player",
    )

    # Overflow menu trigger button
    controls_menu_button = LocatorDescriptor(
        testid="skill-controls-menu-button",
        description="Skill controls overflow menu button"
    )

    # Overflow menu — SKILL-scoped pin/unpin toggle item ("Pin to top" /
    # "Unpin from top"). Testid added via add-data-testid for ELITEA-2435
    # (see test-specs/skills/l3_skill-pin-unpin-flow_ELITEA-2435.md,
    # Concrete Handles) — SkillControls.jsx's pinMenuItem spread never set a
    # `key`, unlike its sibling delete-skill item, so DotMenu.jsx's
    # `testId: item.key` convention rendered `data-testid={undefined}`; same
    # one-line fix shape already landed for Credentials (EliteaAI/EliteaUI#569).
    pin_toggle_menuitem = LocatorDescriptor(
        testid="pin-toggle-skill-menuitem",
        description="Pin/Unpin toggle menu item inside the three-dot menu",
    )

    # Overflow menu — VERSION-scoped Export item (distinct from the
    # SKILL-scoped items further down the same menu)
    export_version_menu_item = LocatorDescriptor(
        testid="export-version-menuitem",
        description="Export the current (base) version via the overflow menu"
    )

    # Overflow menu — "Share" items (ELITEA-2439). SkillControls.jsx wires
    # the same useCopyLinkMenu() hook the Agent flow uses (ELITEA-1898,
    # AgentDetailPage.share_version_menuitem/share_agent_menuitem) — two
    # visually-identical "Share" menu items, one per DotMenu section.
    # share_version_menuitem copies a URL carrying the CURRENT version's id
    # as a distinct trailing path segment (useProjectEntityLink({versionId})
    # in SkillControls.jsx); share_skill_menuitem is the negative-control
    # target — it omits the version id (no versionId override passed to the
    # hook). Confirmed live via a11y snapshot of the open menu (AFS Concrete
    # Handles) — both pre-existing testids, no add-data-testid round trip.
    share_version_menuitem = LocatorDescriptor(
        testid="share-version-menuitem",
        description="VERSION-group 'Share' item — copies a version-specific link",
    )
    # Negative-control target for the version-id contrast assertion — do not
    # click this expecting a version-specific URL, it deliberately omits the
    # version id (AFS Axis 2).
    share_skill_menuitem = LocatorDescriptor(
        testid="share-skill-menuitem",
        description="SKILL-group 'Share' item — copies a generic, version-less link",
    )

    # ------------------------------------------------------------------
    # Fork wizard (ELITEA-2602) — shares the ImportWizardModal dialog
    # family with the Agent/Pipeline Fork flows (AgentDetailPage's
    # fork_wizard_dialog/fork_complete_dialog/etc. carry the SAME testids;
    # re-declared here since Fork is triggered from the SKILL controls menu
    # on THIS page). The "Fork" menuitem testid is the ONE skill-specific
    # value — SkillControls.jsx implements its own `key: 'fork'` menu entry
    # (via its own useForkSkill-driven DotMenu item), NOT the shared
    # ForkEntityButton.jsx/useForkEntityMenu() hook Agent/Pipeline/Toolkit
    # use — confirmed via source read of SkillControls.jsx. The dialog
    # container swaps its own testid in place from
    # "agent-import-preview-dialog" (pre-fork) to
    # "agent-import-complete-dialog" (post-fork) — do not assert on a
    # single fixed testid persisting across the fork action.
    # ------------------------------------------------------------------
    fork_menuitem = LocatorDescriptor(
        testid="fork-menuitem",
        description="Skill overflow menu — 'Fork' item (generic testid, "
                     "unique within this menu — SkillControls.jsx's own "
                     "key, not the shared agent-actions-fork family)",
    )
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
    # Every rendered entity-preview card carries this SAME toggle testid —
    # its count() is a direct proxy for "how many entity cards are showing"
    # (this skill has only a Main entity card, no Nested entities section).
    fork_entity_card_toggle = LocatorDescriptor(
        testid="agent-import-preview-card-toggle",
        description="Fork wizard — 'Show details' toggle, one per rendered "
                     "entity-preview card",
    )
    fork_project_select_trigger = LocatorDescriptor(
        testid="agent-import-wizard-project-select",
        description="Fork wizard — target Project selector trigger "
                     "(shared ProjectSelect DOM node, same testid as "
                     "AgentDetailPage.fork_project_select_trigger)",
    )
    fork_confirm_button = LocatorDescriptor(
        testid="agent-fork-confirm-button",
        description='Fork wizard — "Fork" confirm button',
    )
    fork_complete_skills_list = LocatorDescriptor(
        testid="agent-import-complete-list-skills",
        description="Fork Complete dialog — forked Skills name list "
                     "(IWModalSucceedContent.jsx's per-entity-type list, "
                     "keyed 'skills')",
    )
    fork_complete_got_it_button = LocatorDescriptor(
        testid="agent-import-complete-got-it-button",
        description="Fork Complete dialog — 'Got it' confirm/navigate button",
    )
    # Dynamic (runtime-parameterized) testid template for the Fork wizard's
    # Project-selector dropdown options — same shared `select-option-{value}`
    # family already used by AgentDetailPage.FORK_PROJECT_OPTION /
    # PipelineDetailPage.SELECT_OPTION, keyed by the numeric project id.
    FORK_PROJECT_OPTION = '[data-testid="select-option-{}"]'

    # Sidebar project switcher (ELITEA-2602) — same shared testid already
    # wired by ChatPage/PipelinesListPage/AnalyticsPage's own fields
    # (identical shared sidebar component); NEW field on this page.
    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger-combobox",
        description="Sidebar project switcher trigger (shows current project name)",
    )
    # Dynamic (runtime-parameterized) testid for a project-switcher dropdown
    # option, keyed by numeric project id — same shared SingleSelectMenuItem
    # family as FORK_PROJECT_OPTION above.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    # ------------------------------------------------------------------
    # Version management (Save As Version / VERSION selector) — testids
    # added in the ELITEA-1738 rework (see EliteaUI `automation/testids`:
    # SaveSkillVersionButton.jsx, SingleSelect.jsx, SingleSelectMenuItem.jsx,
    # version.helpers.jsx, SkillTabBar.jsx).
    # ------------------------------------------------------------------

    save_as_version_button = LocatorDescriptor(
        testid="skill-save-as-version-button",
        description='"Save As Version" button in the version tab bar'
    )

    create_version_dialog = LocatorDescriptor(
        testid="skill-create-version-dialog",
        description='"Create version" dialog opened by "Save As Version"'
    )

    # Wrapper testid lands on the MuiFormControl-root (InputBase's leftProps
    # spread onto MuiTextField), not the real <input> — same split documented
    # for CreateSkillForm's Name/Description fields. Use the *_field
    # descriptor below to type into the actual input element.
    create_version_name_input = LocatorDescriptor(
        testid="skill-create-version-name-input",
        description='"Create version" dialog — Name field wrapper'
    )

    create_version_name_input_field = LocatorDescriptor(
        testid="skill-create-version-name-input-field",
        description='"Create version" dialog — Name field, real <input> element'
    )

    create_version_save_button = LocatorDescriptor(
        testid="skill-create-version-save-button",
        description='"Create version" dialog — confirm ("Save") button'
    )

    version_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide Toast component's message container (reused "
                     "for the 'Version \"{name}\" created' toast)"
    )

    version_selector = LocatorDescriptor(
        testid="skill-version-select",
        description="VERSION selector (base ⇄ named-version switcher)"
    )

    # "Set as default?" confirmation dialog — Skill flow. Wired via
    # add-data-testid for ELITEA-2437 (SetDefaultVersionDialog.jsx already
    # accepted an optional confirmButtonTestId prop; EditSkill.jsx's call
    # site never passed it before this).
    set_default_version_confirm_button = LocatorDescriptor(
        testid="skill-set-default-version-confirm-button",
        description='"Set as default?" dialog — confirm ("Set as a default") button'
    )

    # Dynamic (runtime-parameterized) testid for a VERSION-selector option,
    # keyed by version name — set in buildVersionOption() (EliteaUI
    # version.helpers.jsx), shared by every version selector consumer
    # (skill/agent/pipeline), not just this page.
    VERSION_OPTION = '[data-testid="version-option-{}"]'

    # Scoped sub-selector for the pin icon rendered INSIDE a version option
    # (ELITEA-1738 rework, pre-existing testid). Only rendered on the option
    # whose id equals the skill's default version — chain off the
    # already-testid'd VERSION_OPTION.format(name) parent, never a
    # page-level handle. Same shape as AgentDetailPage.VERSION_OPTION_PIN_ICON.
    VERSION_OPTION_PIN_ICON = '[data-testid="version-option-pin-icon"]'

    # Pin/"set as default" hover control on a non-default, non-published
    # version's dropdown row — dynamic (name-keyed) testid added via
    # add-data-testid for ELITEA-2437 (EliteaUI version.helpers.jsx's
    # `<Box id="show-on-hover" onClick={... handleSetDefaultVersion(id)}>`
    # had no testid at all before this). Rendered as a descendant of the
    # MenuItem carrying VERSION_OPTION's testid (SingleSelectMenuItem.jsx
    # renders `option.icon` inside that MenuItem) — always scope this
    # under a VERSION_OPTION locator, never look it up page-wide.
    VERSION_OPTION_SET_DEFAULT = '[data-testid="version-option-set-default-{}"]'

    # Any-version-option selector for reading the VERSION dropdown's full
    # option ORDER — excludes both VERSION_OPTION_PIN_ICON and
    # VERSION_OPTION_SET_DEFAULT, whose testids also start with the
    # `version-option-` prefix but live on nested non-option children, not
    # the option MenuItem itself. Purely testid-keyed (no role/CSS-structure
    # dependency); mirrors AgentDetailPage.VERSION_OPTION_ANY (ELITEA-1891).
    VERSION_OPTION_ANY = (
        '[data-testid^="version-option-"]'
        ':not([data-testid="version-option-pin-icon"])'
        ':not([data-testid^="version-option-set-default-"])'
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to skill detail")
    def navigate(self, skill_id: int):
        """Navigate to a specific skill's detail page and wait until ready.

        Args:
            skill_id: Numeric skill ID.
        """
        super(SkillDetailPage, self).navigate(f"/skills/all/{skill_id}")
        self.wait_for_page_load()
        logger.info("Navigated to skill %d detail page", skill_id)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the skill detail page to fully load.

        Waits for the Information section to appear and network to settle.
        """
        self.page.get_by_test_id("skill-information-section").wait_for(
            state="visible", timeout=timeout,
        )
        self.wait_for_network(timeout=10000)
        logger.info("Skill detail page loaded")

    # ------------------------------------------------------------------
    # Page verification
    # ------------------------------------------------------------------

    def verify_on_detail_page(self):
        """Assert that the browser is on a skill detail page (not create)."""
        url = self.page.url
        assert "/skills/all/" in url, f"Not on skill detail page: {url}"
        assert "/create" not in url, f"Still on create page: {url}"
        logger.info("Verified on skill detail page: %s", url)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    @action("Navigate back")
    def click_back_button(self, timeout: int = 5000):
        """Click the back arrow button in the skill editor header.

        Mirrors ``AgentDetailPage.click_back_button()`` — same shared
        ``BackButton.jsx`` component/testid.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking back button")
        self.back_button.click()
        self.wait_for_network(timeout=timeout)

    # ------------------------------------------------------------------
    # Skill information
    # ------------------------------------------------------------------

    def get_skill_id(self) -> str:
        """Read the Skill ID from the Information section via the URL.

        Falls back to the 'Copy ID' button text if URL parsing fails.

        URL pattern is ``/skills/all/{skillId}`` (base version, one digit
        segment) or ``/skills/all/{skillId}/{versionId}`` (a named version
        is active, two digit segments) — the Skill ID is always the
        *first* digit segment, so this scans forward and returns on the
        first match (fixed from a reversed/last-match scan that returned
        the Version ID instead of the Skill ID once a second digit segment
        was present — ELITEA-1738; identical result for existing
        single-segment callers).

        Returns:
            Skill ID as string.
        """
        url = self.page.url
        # Extract the numeric ID from the URL path segment
        # e.g. /skills/all/42 → "42"; /skills/all/42/43 → "42"
        parts = [p for p in url.split("?")[0].rstrip("/").split("/") if p]
        for part in parts:
            if part.isdigit():
                return part

        raise RuntimeError(f"Cannot determine skill ID from URL: {url}")

    # ------------------------------------------------------------------
    # SkillTestPanel
    # ------------------------------------------------------------------

    def _test_panel_messages(self):
        """Return locator for all chat-message-item elements in the test panel."""
        return self.page.get_by_test_id("chat-message-item")

    def get_test_message_count(self) -> int:
        """Return the current number of messages in the test panel.

        Returns:
            Integer count of message items.
        """
        return self._test_panel_messages().count()

    @action("Send test message")
    def send_test_message(self, message: str, timeout: int = 5000):
        """Type and send a message in the SkillTestPanel.

        Scopes the chat input and send button to the skill-test-panel container
        to avoid conflicts with any other chat panels on the page.

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending test message: %r", message[:60])
        chat_input = self.page.get_by_test_id("chat-message-input")
        chat_input.wait_for(state="visible", timeout=timeout)
        chat_input.fill(message)
        self.page.wait_for_timeout(300)

        send_btn = self.page.get_by_test_id("chat-send-button")
        send_btn.wait_for(state="visible", timeout=timeout)
        send_btn.click()
        logger.info("Test message sent")

    def wait_for_test_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 3000,
        timeout: int = 30000,
    ):
        """Wait for the AI response in the test panel to stabilize.

        Waits for new messages to appear beyond initial_count, then waits
        for the last message content to stop changing.

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this duration (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for test response (initial=%d, stable=%dms, timeout=%dms)",
            initial_count, stable_duration_ms, timeout,
        )
        messages = self._test_panel_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message to appear
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for the delete button to appear on the last response (stream complete).
        delete_btn = self.page.get_by_test_id("chat-delete-button").last
        try:
            delete_btn.wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilize — read via skill-test-last-response (last AI message).
        # The last message in the skill test panel uses testid "skill-test-last-response";
        # non-last messages use "chat-answer-content".
        last_response = self.page.get_by_test_id("skill-test-last-response")
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                current = (last_response.text_content() or "")
            except Exception:
                current = ""

            if current and current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Test response stabilized (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(500)

        logger.warning("Test response did not stabilize within timeout")

    def get_last_test_response(self) -> str:
        """Return the text content of the last AI response in the test panel.

        Reads from data-testid="chat-answer-content" (last element).

        Returns:
            Response text as string (stripped).
        """
        # The last message in the skill test panel uses testid "skill-test-last-response".
        return (self.page.get_by_test_id("skill-test-last-response").text_content() or "").strip()

    # ------------------------------------------------------------------
    # LLM model selector (SkillTestPanel, ELITEA-2436)
    # ------------------------------------------------------------------

    @action("Open LLM model selector")
    def open_model_selector(self, timeout: int = 5000):
        """Click the test panel's model selector to open the dropdown.

        LOCATOR: ``model-selector-button`` testid. Mirrors
        ``AgentDetailPage.open_model_selector()`` — same shared widget.
        """
        logger.info("Opening LLM model selector (skill test panel)")
        self.model_selector_button.click()
        self.page.locator(self.MODEL_SELECTOR_OPTION_ANY_SELECTOR).first.wait_for(
            state="visible", timeout=timeout
        )

    def get_selected_model_name(self) -> str:
        """Return the currently displayed model name on the closed selector.

        LOCATOR: ``model-selector-name`` testid.
        """
        return (self.model_selector_name.text_content() or "").strip()

    @action("Select LLM model")
    def select_llm_model(self, model_name: str, timeout: int = 5000):
        """Select a model from the OPEN model-selector dropdown by its
        stable API ``name`` (dynamic testid suffix, e.g. ``gpt-5-mini``).

        Call after :meth:`open_model_selector`.

        Args:
            model_name: The model's stable API name (matches the
                ``model-selector-option-{name}`` dynamic testid suffix).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting LLM model: %s", model_name)
        option = self.page.locator(self.MODEL_SELECTOR_OPTION.format(model_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("LLM model '%s' selected", model_name)

    # ------------------------------------------------------------------
    # Model Settings dialog (SkillTestPanel, ELITEA-2436)
    # ------------------------------------------------------------------

    @action("Open Model settings dialog")
    def open_model_settings_dialog(self, timeout: int = 5000):
        """Click the gear icon and wait for the Model settings dialog to open.

        LOCATOR: ``model-settings-button`` -> ``model-settings-dialog``.
        """
        logger.info("Opening Model settings dialog (skill test panel)")
        self.model_settings_button.click()
        self.model_settings_dialog.wait_for(state="visible", timeout=timeout)

    def is_reasoning_slider_visible(self, timeout: int = 5000) -> bool:
        """Return True if the Reasoning slider (Low/Medium/High) is shown.

        LOCATOR: ``model-settings-reasoning-slider``. Rendered only for a
        reasoning-capable model. Call after :meth:`open_model_settings_dialog`.
        """
        try:
            self.model_settings_reasoning_slider.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_reasoning_slider_text(self, timeout: int = 5000) -> str:
        """Return the Reasoning slider's own rendered text (label + Low/Medium/High).

        LOCATOR: ``model-settings-reasoning-slider``.
        """
        self.model_settings_reasoning_slider.wait_for(state="visible", timeout=timeout)
        return (self.model_settings_reasoning_slider.text_content() or "").strip()

    def is_creativity_slider_visible(self, timeout: int = 5000) -> bool:
        """Return True if the Creativity slider is shown (non-reasoning model).

        LOCATOR: ``model-settings-creativity-slider``. Call after
        :meth:`open_model_settings_dialog`.
        """
        try:
            self.model_settings_creativity_slider.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_creativity_slider_value(self, timeout: int = 5000) -> int:
        """Return the Creativity slider's current numeric position (1-5).

        LOCATOR: ``model-settings-creativity-slider-input`` — the real
        ``<input type="range">`` inside the slider wrapper.
        """
        self.model_settings_creativity_slider_input.wait_for(state="visible", timeout=timeout)
        value = self.model_settings_creativity_slider_input.get_attribute("value")
        return int(value) if value is not None else -1

    @action("Adjust Creativity slider")
    def increase_creativity_slider(self, timeout: int = 5000):
        """Focus the Creativity slider's underlying range input and press
        ArrowRight once to move it one discrete position.

        LOCATOR: ``model-settings-creativity-slider-input``. Focusing the
        underlying ``<input type="range">`` directly (not clicking the
        visual MUI thumb) avoids the thumb `<span>` intercepting pointer
        events — confirmed live during AFS exploration and mirrored from
        the existing discrete-slider interaction pattern
        (``user_profile_settings_page.py::set_speed()``), but via a
        testid-scoped locator instead of a raw aria-label/attribute
        selector.
        """
        logger.info("Increasing Creativity slider by one step")
        self.model_settings_creativity_slider_input.wait_for(state="visible", timeout=timeout)
        self.model_settings_creativity_slider_input.focus()
        self.page.keyboard.press("ArrowRight")

    def is_apply_button_enabled(self, timeout: int = 5000) -> bool:
        """Return True if the Model settings dialog's Apply button is enabled.

        LOCATOR: ``model-settings-apply-button``.
        """
        self.model_settings_apply_button.wait_for(state="visible", timeout=timeout)
        return self.model_settings_apply_button.is_enabled()

    @action("Apply Model settings")
    def click_apply_model_settings(self, timeout: int = 5000):
        """Click Apply and wait for the Model settings dialog to close.

        LOCATOR: ``model-settings-apply-button``.
        """
        logger.info("Applying Model settings")
        self.model_settings_apply_button.click()
        self.model_settings_dialog.wait_for(state="hidden", timeout=timeout)

    @action("Close Model settings dialog via Cancel")
    def close_model_settings_dialog_via_cancel(self, timeout: int = 5000):
        """Click Cancel and wait for the Model settings dialog to close.

        LOCATOR: ``model-settings-cancel-button``. Discards any local
        (unapplied) edits made inside the dialog. Mirrors
        ``AgentDetailPage.close_model_settings_dialog_via_cancel()``.
        """
        logger.info("Closing Model settings dialog via Cancel")
        self.model_settings_cancel_button.click()
        self.model_settings_dialog.wait_for(state="hidden", timeout=timeout)

    # ------------------------------------------------------------------
    # Actions menu (overflow/three-dot menu)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the skill controls overflow menu.

        Uses JavaScript click to bypass any MUI overlay interception.
        Waits for the Delete skill menu item to confirm the menu is open.
        """
        logger.info("Opening skill actions menu")
        self.controls_menu_button.evaluate("el => el.click()")
        self.page.get_by_test_id("skill-delete-menu-item").wait_for(state="visible", timeout=5000)

    def get_pin_toggle_menu_label(self) -> str:
        """Return the pin-toggle menu item's current text ("Pin to top" / "Unpin from top")."""
        return self.pin_toggle_menuitem.text_content() or ""

    @action("Toggle skill pin via detail menu")
    def click_pin_toggle_menu_item(self):
        """Click the pin-toggle menu item and wait for the underlying
        ``POST``/``DELETE .../social/pin/prompt_lib/{project}/skill/{id}``
        response, per the AFS's wait-on-network-response guidance (no fixed sleep).

        Returns:
            The matched Playwright ``Response``.
        """
        skill_id = self.get_skill_id()
        pattern = "/social/pin/prompt_lib/"
        with self.page.expect_response(
            lambda r: pattern in r.url and r.url.rstrip("/").endswith(f"/skill/{skill_id}")
        ) as response_info:
            self.pin_toggle_menuitem.click()
        return response_info.value

    @action("Delete skill via menu")
    def delete_skill_via_menu(self, skill_name: str, timeout: int = 10000):
        """Delete the current skill via the overflow menu.

        Opens the menu, clicks "Delete skill", and handles the confirmation
        dialog (type skill name + confirm delete).

        Args:
            skill_name: The exact skill name to type in the confirmation dialog.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting skill via menu: %r", skill_name)

        self.open_actions_menu()
        self.page.get_by_test_id("skill-delete-menu-item").click()

        # Handle the type-to-confirm dialog (Modal.DeleteEntityModal)
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.type_to_confirm(dialog, skill_name)
        self.page.wait_for_timeout(300)
        Dialog.click_button(dialog, "Delete")

        # Wait for redirect to the skills list page (/skills/all without trailing ID).
        # Regex with $ anchor is required — glob **/skills/all also matches /skills/all/4.
        self.page.wait_for_url(
            re.compile(r".*/skills/all/?$"),
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info("Skill %r deleted via menu", skill_name)

    @action("Export skill base version via menu")
    def export_base_version_via_menu(self, timeout: int = 10000) -> Download:
        """Export the skill's current (base) version via the overflow menu.

        Opens the overflow menu and clicks the VERSION-scoped "Export" item
        (``export-version-menuitem`` — distinct from the SKILL-scoped items
        further down the same menu), waiting for the resulting file download.

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object for the exported ``.md`` file.
        """
        logger.info("Exporting skill base version via menu")
        self.open_actions_menu()

        with self.page.expect_download(timeout=timeout) as download_info:
            self.export_version_menu_item.click()

        download = download_info.value
        logger.info("Skill base version exported — filename: %s", download.suggested_filename)
        return download

    @action("Export current version via menu")
    def export_version_via_menu(self, timeout: int = 10000) -> Download:
        """Export whichever version is currently selected via the overflow menu.

        Thin wrapper around :meth:`export_base_version_via_menu` — that
        method already exports whatever version is currently active (the
        ``export-version-menuitem`` testid is version-scoped, not
        base-specific); this alias just avoids the misleading "base" in the
        call site's name when exporting a non-base version (ELITEA-1738).

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object for the exported ``.md`` file.
        """
        return self.export_base_version_via_menu(timeout=timeout)

    # ------------------------------------------------------------------
    # Fork wizard (ELITEA-2602)
    # ------------------------------------------------------------------

    @action("Open Fork wizard")
    def open_fork_wizard(self, timeout: int = 10000):
        """Open the Fork wizard via the skill controls overflow menu.

        Opens the overflow (three-dot) menu (``open_actions_menu()``) and
        clicks the "Fork" menuitem, then waits for the wizard dialog
        (``agent-import-preview-dialog``) to become visible.

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening Fork wizard via skill controls menu")
        self.open_actions_menu()
        self.fork_menuitem.click()
        self.fork_wizard_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Fork wizard dialog visible")

    @action("Select Fork target project")
    def select_fork_target_project(self, project_id: int, timeout: int = 10000):
        """Open the Fork wizard's Project selector and pick a target project.

        LOCATOR: ``fork_project_select_trigger`` opens the dropdown; the
        option is resolved via the dynamic ``select-option-{project_id}``
        testid (see ``FORK_PROJECT_OPTION`` above).

        Args:
            project_id: Numeric id of the target project (must differ from
                the skill's current project).
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
        swaps once the fork operation succeeds).

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

        Auto-navigates to the newly forked Skill's detail page, inside the
        target project. Parses and returns the new Skill's numeric ID from
        the resulting URL.

        Args:
            timeout: Maximum wait time in milliseconds for the navigation.

        Returns:
            The forked Skill's numeric ID.
        """
        self.fork_complete_got_it_button.click()
        self.page.wait_for_url(re.compile(r".*/skills/all/\d+"), timeout=timeout)
        self.wait_for_network(timeout=5000)

        match = re.search(r"/skills/all/(\d+)", self.page.url)
        if not match:
            raise ValueError(
                f"Could not parse forked Skill ID from URL: {self.page.url}"
            )
        forked_skill_id = int(match.group(1))
        logger.info(
            "Fork complete — navigated to forked skill id=%d (%s)",
            forked_skill_id, self.page.url,
        )
        return forked_skill_id

    # ------------------------------------------------------------------
    # Sidebar project switcher (ELITEA-2602)
    # ------------------------------------------------------------------

    @action("Switch active project")
    def switch_project(self, project_id: int, timeout: int = 10000) -> None:
        """Switch the active project via the sidebar project selector.

        A bare ``page.goto()``/``navigate()`` to another project's skill
        detail route 404s — the currently-selected project scopes the GET
        (confirmed live). Cross-project navigation MUST go through this
        method first. Mirrors ``PipelinesListPage.switch_project()`` (same
        shared component).

        Args:
            project_id: Numeric id of the target project.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Switching active project to id=%d", project_id)
        self.project_selector_trigger.click()
        option = self.page.locator(self.SELECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Switched to project id=%d", project_id)

    # ------------------------------------------------------------------
    # Version management (Save As Version / VERSION selector)
    # ------------------------------------------------------------------

    def get_version_id(self) -> str:
        """Read the current Version ID from the URL's second path segment.

        URL pattern: ``/skills/all/{skillId}/{versionId}`` — only present
        once a non-base version has been created/selected; on the initial
        ``base`` version the URL is just ``/skills/all/{skillId}`` and the
        Version ID equals the Skill ID.

        Returns:
            Version ID as string.
        """
        url = self.page.url
        parts = [p for p in url.split("?")[0].rstrip("/").split("/") if p]
        digit_parts = [p for p in parts if p.isdigit()]
        if len(digit_parts) >= 2:
            return digit_parts[-1]
        if len(digit_parts) == 1:
            # No explicit version segment yet — Version ID equals Skill ID.
            return digit_parts[0]
        raise RuntimeError(f"Cannot determine version ID from URL: {url}")

    def wait_for_version_selector_and_url_id(
        self, version_name: str, version_id: str, timeout: int = 10000
    ) -> None:
        """Wait until the VERSION selector trigger AND the URL's trailing
        version-id path segment both agree with the given ``(version_name,
        version_id)`` pair (ELITEA-2439).

        Mirrors ``AgentDetailPage.wait_for_version_trigger_and_id()`` — the
        two-way convergence check for a caller that just navigated to a
        version-specific copied link in a fresh tab and only needs the
        CLIENT-SIDE render state to catch up post-navigation. Skills have no
        ``copy-version-id``-style testid'd readout (the "Copy version ID"
        footer button carries no ``data-testid`` — AFS Concrete Handles), so
        this polls the URL's own trailing digit segment instead of a second
        testid'd element — the URL segment IS the authoritative version id
        for a non-``base`` version (``get_version_id()`` reads the same
        segment once settled).

        LOCATOR: polls ``skill-version-select`` via ``document.querySelector``
        inside the predicate — ``wait_for_function`` executes in-page JS,
        which cannot reference a Playwright ``Locator`` directly, so the
        testid (also the ``version_selector`` ``LocatorDescriptor`` field
        above) is inlined as a literal ``[data-testid="…"]`` string here
        rather than duplicated as a second selector elsewhere.

        Args:
            version_name: Expected VERSION-selector trigger text, e.g.
                ``"v1-copy-link-test"``.
            version_id: Expected version id, as it appears as the URL's
                trailing digit segment (i.e. :meth:`get_version_id`'s value).
            timeout: Maximum wait time in milliseconds.
        """
        self.page.wait_for_function(
            """([name, expectedId]) => {
                const trigger = document.querySelector(
                    '[data-testid="skill-version-select"]'
                );
                if (!trigger || trigger.innerText.trim() !== name) return false;
                const parts = window.location.pathname.split('/').filter(Boolean);
                return parts[parts.length - 1] === expectedId;
            }""",
            arg=[version_name, version_id],
            timeout=timeout,
        )
        logger.info(
            "VERSION selector/URL id converged on name=%r id=%r",
            version_name, version_id,
        )

    @action("Save current edits as a new version")
    def save_as_version(self, version_name: str, timeout: int = 10000):
        """Click "Save As Version", fill the Name field, and confirm.

        Opens the "Create version" dialog via the "Save As Version" button
        (in the version tab bar, distinct from the overflow menu), types the
        new version name, and clicks the dialog's Save. Waits for the
        ``Version "{version_name}" created`` toast and for the URL to gain a
        new version-id path segment.

        LOCATOR: testid-based throughout (ELITEA-1738 testid rework) — the
        "Save As Version" button, the "Create version" dialog, its Name
        field, and the confirm button all carry ``data-testid`` now (see the
        class-level ``LocatorDescriptor`` fields above).

        Args:
            version_name: Name for the new version (e.g. ``"ver_1"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Saving current edits as new version: %r", version_name)
        previous_version_id = self.get_version_id()

        self.save_as_version_button.click()

        self.create_version_dialog.wait_for(state="visible", timeout=timeout)
        self.create_version_name_input_field.click()
        self.create_version_name_input_field.type(version_name)
        self.page.wait_for_timeout(200)

        self.create_version_save_button.click()

        self.version_toast_message.wait_for(state="visible", timeout=timeout)
        toast_text = self.version_toast_message.text_content()
        assert toast_text == f'Version "{version_name}" created', (
            f"Expected 'Version \"{version_name}\" created' toast, got: {toast_text!r}"
        )
        self.page.wait_for_function(
            "prevId => window.location.pathname.split('/').filter(Boolean).pop() !== prevId",
            arg=previous_version_id,
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info(
            "New version %r created — URL: %s", version_name, self.page.url
        )

    @action("Confirm the 'Create version' dialog, capturing the create-version response")
    def confirm_create_version_capturing_response(self, version_name: str, timeout: int = 10000):
        """Click the "Create version" dialog's Save button and capture the
        underlying create-version network response (ELITEA-2606).

        Companion to :meth:`save_as_version` for callers that need to verify
        the dialog opening (``create_version_dialog``) and the Name field
        (``create_version_name_input_field``) as their OWN case steps first
        — via those already-public locators — before confirming. Call this
        only AFTER the dialog is open and the Name field already holds
        *version_name* (mirrors the second half of :meth:`save_as_version`'s
        body; :meth:`save_as_version` remains the right hook for callers
        that don't need that per-step granularity).

        Captures the ``POST .../elitea_core/skill/prompt_lib/{project}/
        {skillId}`` (singular ``skill`` — the "create version" endpoint,
        distinct from the plural ``skills`` create-skill endpoint) response,
        so the caller can read its JSON body — e.g. ``meta.icon_meta`` — as
        an authoritative server-side assertion point instead of relying
        solely on a DOM ``<img src>`` read.

        Args:
            version_name: The version name already entered in the Name
                field — used only to assert the confirmation toast's exact
                text (same assertion :meth:`save_as_version` makes).
            timeout: Maximum wait time in milliseconds.

        Returns:
            The matched Playwright ``Response`` for the create-version POST.
        """
        previous_version_id = self.get_version_id()

        with self.page.expect_response(
            lambda r: "/elitea_core/skill/prompt_lib/" in r.url
            and r.request.method == "POST"
        ) as response_info:
            self.create_version_save_button.click()

        self.version_toast_message.wait_for(state="visible", timeout=timeout)
        toast_text = self.version_toast_message.text_content()
        assert toast_text == f'Version "{version_name}" created', (
            f"Expected 'Version \"{version_name}\" created' toast, got: {toast_text!r}"
        )
        self.page.wait_for_function(
            "prevId => window.location.pathname.split('/').filter(Boolean).pop() !== prevId",
            arg=previous_version_id,
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info(
            "New version %r created (response captured) — URL: %s, POST status=%s",
            version_name, self.page.url, response_info.value.status,
        )
        return response_info.value

    def get_version_selector_value(self) -> str:
        """Return the currently displayed value of the VERSION selector.

        LOCATOR: ``skill-version-select`` testid (ELITEA-1738 testid rework —
        ``SkillTabBar.jsx`` now passes ``data-testid`` through to
        ``SingleSelect``).

        Returns:
            The version name currently shown in the selector (e.g. ``"ver_1"``).
        """
        return (self.version_selector.text_content() or "").strip()

    @action("Switch to a different skill version")
    def switch_version(self, version_name: str, timeout: int = 10000):
        """Select a different version from the VERSION combobox.

        LOCATOR: ``skill-version-select`` testid for the combobox trigger;
        each dropdown option carries a name-keyed ``version-option-{name}``
        testid (ELITEA-1738 testid rework — set in ``buildVersionOption()``,
        shared by every version-selector consumer, not just this page).

        Confirms the switch by polling the selector's own displayed text
        rather than trusting ``wait_for_network`` alone — a race observed
        during ELITEA-2440 automation: the option ``click()`` and the
        network-idle wait can both resolve before MUI's ``onChange``
        re-render actually lands, so a caller reading the selector text
        immediately afterward can still see the previous version.

        Args:
            version_name: The version name to select (e.g. ``"base"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Switching to version: %r", version_name)
        self.version_selector.click()
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=5000)

        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            current = self.get_version_selector_value()
            if current == version_name:
                logger.info("Switched to version: %r", version_name)
                return
            self.page.wait_for_timeout(200)

        raise RuntimeError(
            f"VERSION selector did not update to {version_name!r} within "
            f"{timeout}ms (still showing {self.get_version_selector_value()!r})"
        )

    def open_version_selector(self):
        """Click the VERSION dropdown trigger to open the options list."""
        self.version_selector.click()

    def is_version_option_visible(self, version_name: str, timeout: int = 5000) -> bool:
        """Check whether a version is present in the open VERSION dropdown.

        LOCATOR: dynamic ``version-option-{version_name}`` testid (see
        ``VERSION_OPTION`` above) — call after :meth:`open_version_selector`.

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

    def is_version_option_pinned(self, version_name: str) -> bool:
        """Check whether a version option in the open VERSION dropdown shows
        the static default-pin icon (i.e. it is the skill's current default
        version).

        LOCATOR: scoped sub-selector chained off the already-testid'd
        ``VERSION_OPTION.format(version_name)`` parent — see
        ``VERSION_OPTION_PIN_ICON`` above. Call after
        :meth:`open_version_selector`.

        Args:
            version_name: Exact version name (e.g. ``"base"``).
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        return option.locator(self.VERSION_OPTION_PIN_ICON).count() > 0

    def _hover_version_option(self, version_name: str, timeout: int = 5000):
        """Scroll/hover a version option's row to reveal its hover-gated
        "set as default" control, and return the option's own locator.

        Call after :meth:`open_version_selector`.
        """
        option = self.page.locator(self.VERSION_OPTION.format(version_name))
        option.wait_for(state="visible", timeout=timeout)
        option.hover()
        self.page.wait_for_timeout(300)  # hover-reveal CSS transition (#show-on-hover)
        return option

    def is_version_option_set_default_control_visible(
        self, version_name: str, timeout: int = 5000
    ) -> bool:
        """Hover the named version's row and check whether its hover-revealed
        "set as default" pin control (``VERSION_OPTION_SET_DEFAULT``, added
        via add-data-testid for ELITEA-2437) becomes visible.

        Call after :meth:`open_version_selector`.

        Args:
            version_name: The non-default version's name (e.g. ``"ver_1"``).
            timeout: Maximum wait time in milliseconds.
        """
        option = self._hover_version_option(version_name, timeout=timeout)
        control = option.locator(self.VERSION_OPTION_SET_DEFAULT.format(version_name))
        try:
            control.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Click set-as-default on a version option")
    def click_version_option_set_default(self, version_name: str, timeout: int = 5000):
        """Hover the named version's row and click its "set as default" pin
        control, opening the "Set as default?" confirmation dialog.

        Call after :meth:`open_version_selector`.

        Args:
            version_name: The non-default version's name to set as default
                (e.g. ``"ver_1"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking set-as-default for version: %r", version_name)
        option = self._hover_version_option(version_name, timeout=timeout)
        control = option.locator(self.VERSION_OPTION_SET_DEFAULT.format(version_name))
        control.wait_for(state="visible", timeout=timeout)
        control.click()

    @action("Confirm set-as-default in the confirmation dialog")
    def confirm_set_default_version(self, timeout: int = 10000):
        """Click the "Set as default?" dialog's confirm button
        (``skill-set-default-version-confirm-button``, added via
        add-data-testid for ELITEA-2437), waiting for the underlying
        ``PATCH .../skill_default_version/...`` response and the
        confirmation toast — mirrors :meth:`save_as_version`'s existing
        network-wait pattern instead of a fixed sleep.

        Call after :meth:`click_version_option_set_default`.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The matched Playwright ``Response`` for the
            ``skill_default_version`` PATCH.
        """
        self.set_default_version_confirm_button.wait_for(state="visible", timeout=timeout)

        with self.page.expect_response(
            lambda r: "/skill_default_version/prompt_lib/" in r.url and r.request.method == "PATCH"
        ) as response_info:
            self.set_default_version_confirm_button.click()

        self.version_toast_message.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=5000)
        logger.info("Confirmed set-as-default — PATCH status=%s", response_info.value.status)
        return response_info.value

    @action("Save skill edits (stay on detail page)")
    def save_edits(self, timeout: int = 15000):
        """Click Save on an EXISTING skill's edit form and wait for the
        update to persist, without navigating away (ELITEA-2431).

        Distinct from :meth:`save_and_wait_for_navigation` (the create-flow
        Save, which navigates from ``/skills/create`` to the newly-created
        skill's detail page). Editing an existing skill uses the SAME
        ``skill-save-button`` testid but a different hook
        (``useSaveSkill.hooks.js``): it ``PUT``s the change and then calls
        ``resetForm()`` + ``toastSuccess('Skill saved')`` — no navigation,
        confirmed source-side. Reusing ``save_and_wait_for_navigation()``
        here would be a no-op false-pass: its "already navigated" check
        (``"/skills/all/" in url and "/create" not in url``) is already
        true *before* the click on a detail page, so it would return
        immediately without ever waiting for the PUT to complete.

        Also asserts the browser stays on the SAME detail URL across the
        Save -- the distinguishing edit-flow behavior the AFS's Step 3
        Verify text specifies (edit-flow ``PUT`` + toast, no navigation,
        vs. the create-flow's ``POST`` + redirect). The 'Skill saved' toast
        alone can't catch a regression that both saves AND navigates: the
        toast is rendered app-wide via a portal (``version_toast_message``
        is not scoped to the detail page), so it would still appear even if
        the click also routed the user away. Comparing ``page.url`` before
        and after is what actually proves "no navigation".

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The matched Playwright ``Response`` for the
            ``PUT .../skill/prompt_lib/{project}/{skillId}`` request.
        """
        skill_id = self.get_skill_id()
        pre_save_url = self.page.url
        pattern = "/skill/prompt_lib/"
        logger.info("Saving edits to skill %s", skill_id)
        with self.page.expect_response(
            lambda r: pattern in r.url
            and r.url.rstrip("/").endswith(f"/{skill_id}")
            and r.request.method == "PUT"
        ) as response_info:
            self.save_button.evaluate("el => el.click()")

        self.version_toast_message.wait_for(state="visible", timeout=timeout)
        toast_text = self.version_toast_message.text_content()
        assert toast_text == "Skill saved", (
            f"Expected 'Skill saved' toast, got: {toast_text!r}"
        )
        self.wait_for_network(timeout=5000)

        post_save_url = self.page.url
        assert post_save_url == pre_save_url, (
            "Edit-flow Save must NOT navigate away from the skill detail "
            f"page -- expected to stay on {pre_save_url!r}, but URL is now "
            f"{post_save_url!r}"
        )

        logger.info("Skill %s edits saved — PUT status=%s", skill_id, response_info.value.status)
        return response_info.value

    def get_version_option_order(self, timeout: int = 5000) -> list[str]:
        """Return the VERSION dropdown's option names, in DOM (visual) order.

        LOCATOR: ``VERSION_OPTION_ANY`` (excludes the nested pin-icon and
        set-default-control testids, which also start with the
        ``version-option-`` prefix, so they're never mistaken for options
        themselves). Reads each matched element's own ``data-testid``
        attribute and strips the ``version-option-`` prefix — mirrors
        ``AgentDetailPage.get_version_option_order()`` (ELITEA-1891). Call
        after :meth:`open_version_selector`.

        Args:
            timeout: Maximum wait time in milliseconds for the first option.

        Returns:
            Version names in the order they're rendered, e.g.
            ``["ver_1", "base"]`` once ``ver_1`` is the default.
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
