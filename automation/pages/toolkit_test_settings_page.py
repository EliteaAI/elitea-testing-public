"""Toolkit Test Settings panel page object — the right-hand "TEST SETTINGS"
region of the toolkit detail page, plus its paired center chat/output panel.

Handles: /toolkits/all/{id} — a DIFFERENT region of the same page
:class:`ToolkitDetailPage` models (that page covers the Configuration form:
credential-status indicators, Save/Discard on an already-created toolkit).

Deliberately a NEW page object rather than an extension of
``ToolkitDetailPage`` (AFS § Overlap check, ELITEA-1866) — the TEST SETTINGS
panel is a sibling region of the SAME ``/toolkits/all/{id}`` page, not a
variant of the Configuration form, and its testids (``toolkit-test-*``) form
their own distinct, self-consistent namespace. Added for ELITEA-1866 — the
TEST SETTINGS/RUN TOOL surface (``TestTools.jsx`` -> ``TestToolSettings.jsx``)
had zero automation coverage in ``automation/pages/`` before this case.
"""

import logging
import re

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.toolkit_test_settings")


class ToolkitTestSettingsPage(BasePage):
    """Page object for the toolkit-detail page's TEST SETTINGS panel.

    URL: /toolkits/all/{id} (same page as :class:`ToolkitDetailPage` — this
    models the right-hand test-tool panel and its paired center chat/output
    panel, not the Configuration form).
    """

    # ------------------------------------------------------------------
    # TEST SETTINGS panel (right side)
    # ------------------------------------------------------------------

    model_selector_button = LocatorDescriptor(
        testid="model-selector-button",
        description="Test Settings panel's model selector trigger — shared "
        "LLMModelSelector.jsx widget, existing testid already on "
        "automation/testids before this case (confirmed live, ELITEA-1866 "
        "implementer Phase 2 exploration)",
    )

    model_selector_name = LocatorDescriptor(
        testid="model-selector-name",
        description="Currently-selected model's display name inside the "
        "model selector — model-specific text (e.g. 'Anthropic Claude 4.5 "
        "Sonnet'); assert non-empty only, never the exact model name",
    )

    # EL-5947 gated the Test Settings panel behind tool selection:
    #   TestTools.jsx →  if (!selectedTool) return <TestToolsEmptyState/>
    #                    return <TestToolSettings/>          # 'Test Settings' here
    # So a freshly-opened toolkit detail page shows the EMPTY STATE, not the panel.
    # This select is the only route from one to the other; waiting for the panel
    # before selecting a tool can never succeed.
    empty_state_tool_select = LocatorDescriptor(
        testid="toolkit-test-empty-tool-select",
        description="'Select Tool' PopoverSelect on TestToolsEmptyState — shown "
        "INSTEAD of the Test Settings panel until a tool is chosen (EL-5947)",
    )

    tool_select = LocatorDescriptor(
        testid="toolkit-test-tool-select",
        description="Test Settings panel's 'Tool' dropdown combobox "
        "(TestToolSettings.jsx) — choosing an option renders that tool's "
        "parameter schema as live input fields. Only present AFTER a tool has "
        "been selected via :attr:`empty_state_tool_select` (EL-5947).",
    )

    run_tool_button = LocatorDescriptor(
        testid="toolkit-test-run-tool-button",
        description="'RUN TOOL' button (TestToolSettings.jsx's "
        "Button.BaseBtn) — testid added for ELITEA-1866 (previously had "
        "none; TestToolSettings.jsx wired directly, pushed to "
        "automation/testids)",
    )

    # Dropdown-option testid family (shared SingleSelectMenuItem.jsx,
    # already promoted to main) — same template shape as
    # toolkit_creation_page.py's TOOLKIT_TYPE_CARD.
    TOOL_OPTION = '[data-testid="select-option-{}"]'

    # Prefix (any-tool) variant of TOOL_OPTION — matches every currently-
    # rendered dropdown option regardless of tool key. Same
    # `[data-testid^="…"]` prefix-count pattern already established
    # elsewhere (e.g. toolkit_creation_page.py's TOOLKIT_TYPE_CARD_ANY_SELECTOR)
    # — used to prove the Tool dropdown lists all 16 tools (case step 27)
    # without needing a raw `[role="listbox"]` locator.
    TOOL_OPTION_ANY_SELECTOR = '[data-testid^="select-option-"]'

    # Test Settings panel's schema-rendered parameter fields, one per
    # tool-schema property (CommonStringField.jsx / AnyOfPatternField.jsx /
    # CommonBooleanField.jsx). CommonBooleanField.jsx needed its own testid
    # added for this case (ELITEA-1866) — its wrapper wasn't setting
    # data-testid the way the sibling string-field renderers already do;
    # same template, now closed for all field-type renderers this case
    # touches.
    TOOL_PARAM = '[data-testid="toolkit-test-param-{}"]'

    # The wrapper Box above carries the field's testid (CommonStringField.jsx);
    # the actual <input> is a separate node. Added via add-data-testid for
    # ELITEA-1937 (CommonStringField.jsx's inputProps) — same "-input" suffix
    # convention as McpFormPage's toolkit-field-{k}-input (ToolBaseProperty.jsx).
    TOOL_PARAM_INPUT = '[data-testid="toolkit-test-param-{}-input"]'

    # ------------------------------------------------------------------
    # Center chat/output panel (left side) — the SAME generic message-list
    # testid every chat surface in the app renders (ChatMessageList.jsx,
    # `data-testid="chat-message-list"`, already on `main` before this
    # case). The toolkit-detail page renders exactly one instance of it,
    # backing both the pre-run welcome message and the post-RUN-TOOL result
    # message (confirmed live, ELITEA-1866 implementer Phase 2 exploration
    # — no new testid needed here).
    # ------------------------------------------------------------------

    result_message_list = LocatorDescriptor(
        testid="chat-message-list",
        description="Center panel's message list (ChatMessageList.jsx, "
        "shared chat component reused by every chat surface in the app) — "
        "the toolkit-detail page renders exactly one instance of it",
    )

    # Scoped sub-selector for the individual message item(s) inside the
    # testid'd message-list container (`.claude/rules/page-objects.md` §
    # Scoped selectors — UPPER_CASE class constant anchored on a
    # `[data-testid="…"]` root). MUI List renders one
    # `<li class="MuiListItem-root">` per message
    # (`.claude/rules/mui-patterns.md` § Message Locators) — same
    # structural pattern `chat_page.py`'s message list uses, now anchored
    # to a real testid instead of a bare `main ul.MuiList-root` prefix.
    RESULT_MESSAGE_ITEM = '[data-testid="chat-message-list"] li.MuiListItem-root'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Tool selection
    # ------------------------------------------------------------------

    @action("Select a tool in the Test Settings panel")
    def open_empty_state_tool_select(self, timeout: int = 10000) -> None:
        """Open the empty state's 'Select Tool' popover.

        A freshly-opened toolkit detail page renders ``TestToolsEmptyState``, NOT
        the Test Settings panel — EL-5947 gated the panel behind
        ``if (!selectedTool)`` (``TestTools.jsx``). This popover is the only route
        to the panel, so callers must open it and pick a tool BEFORE waiting for
        anything inside the panel.

        Deliberately open-only: the caller chooses the option, because callers
        differ in what they have to match on (a display name from
        ``ToolkitConfig.test_tool_name`` vs a schema key for
        :attr:`TOOL_OPTION`). Once a tool is chosen the panel mounts with its own
        Tool dropdown (:attr:`tool_select`), driven by :meth:`select_tool`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.empty_state_tool_select.wait_for(state="visible", timeout=timeout)
        self.empty_state_tool_select.click()
        logger.info("Opened the Test-Tools empty-state tool select")

    def select_tool_from_empty_state(self, tool_key: str, timeout: int = 10000) -> None:
        """Open the empty state's popover and select *tool_key* by its schema key.

        Convenience wrapper for callers that know the schema key (the
        :attr:`TOOL_OPTION` testid family). Callers holding only a display name
        should use :meth:`open_empty_state_tool_select` and match it themselves.

        Args:
            tool_key: The tool's schema key (e.g. ``"list_files"``).
            timeout: Maximum wait time in milliseconds.
        """
        self.open_empty_state_tool_select(timeout=timeout)
        option = self.page.locator(self.TOOL_OPTION.format(tool_key))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("Selected tool '%s' from the Test-Tools empty state", tool_key)

    def wait_for_panel(self, timeout: int = 10000) -> None:
        """Wait until the Test Settings panel itself has mounted.

        Anchored on :attr:`tool_select` (a testid) rather than the panel's
        ``Test Settings`` heading text: the heading is a raw-text handle, and the
        policy is testid-only (``.agents/testing.md`` § Locator policy).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.tool_select.wait_for(state="visible", timeout=timeout)

    def select_tool(self, tool_key: str, timeout: int = 10000) -> None:
        """Open the Tool dropdown and select *tool_key*.

        Waits for the selected option to become visible before clicking
        (client-side render off the already-fetched schema, no network
        settle required — same rationale as
        :meth:`ToolkitCreationPage.select_toolkit_type`).

        Args:
            tool_key: The tool's schema key (e.g. ``"list_files"``).
            timeout: Maximum wait time in milliseconds.
        """
        self.tool_select.click()
        option = self.page.locator(self.TOOL_OPTION.format(tool_key))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("Selected tool '%s' in Test Settings panel", tool_key)

    def get_tool_options(self):
        """Return the Locator matching every currently-rendered Tool-dropdown option.

        Thin wrapper around :attr:`TOOL_OPTION_ANY_SELECTOR` so callers
        (tests) never construct the dynamic-testid locator inline
        themselves — locators stay behind the page-object boundary
        (``.claude/rules/page-objects.md``). Callers assert on the
        returned Locator directly (e.g. ``expect(...).to_have_count(...)``)
        rather than a pre-computed int, so Playwright's auto-retry
        semantics apply right after the dropdown opens (mirrors
        :meth:`ToolkitCreationPage.get_type_card`'s Locator-returning
        style, not the int-returning ``count_*`` helpers).
        """
        return self.page.locator(self.TOOL_OPTION_ANY_SELECTOR)

    def get_tool_option(self, tool_key: str):
        """Return the Locator for a specific Tool-dropdown option, by schema key.

        Thin wrapper around :attr:`TOOL_OPTION` so callers (tests) never
        construct the dynamic-testid locator inline themselves — locators
        stay behind the page-object boundary
        (``.claude/rules/page-objects.md``). Mirrors
        :meth:`get_param_field` / ``ToolkitCreationPage.get_type_card``.

        Args:
            tool_key: The tool's schema key (e.g. ``"list_files"``).
        """
        return self.page.locator(self.TOOL_OPTION.format(tool_key))

    def get_param_field(self, field_key: str):
        """Return the Locator for a tool-parameter field, by its schema key.

        Thin wrapper around :attr:`TOOL_PARAM` so callers never construct
        the dynamic-testid locator inline themselves — locators stay
        behind the page-object boundary (``.claude/rules/page-objects.md``).

        Args:
            field_key: The field's schema property key (e.g.
                ``"bucket_name"``).
        """
        return self.page.locator(self.TOOL_PARAM.format(field_key))

    def is_param_field_visible(self, field_key: str, timeout: int = 10000) -> bool:
        """Wait for and return whether a tool-parameter field is visible.

        Args:
            field_key: The field's schema property key.
            timeout: Maximum wait time in milliseconds.
        """
        field = self.get_param_field(field_key)
        field.wait_for(state="visible", timeout=timeout)
        return field.is_visible()

    def get_param_input(self, field_key: str):
        """Return the Locator for a tool-parameter field's real ``<input>`` element.

        :attr:`TOOL_PARAM`'s testid lands on ``CommonStringField.jsx``'s wrapper
        ``Box``, not the ``<input>`` itself — mirrors ``McpFormPage``'s own
        wrapper-vs-field split (e.g. ``client_secret_input`` vs
        ``client_secret_input_field``). Thin wrapper around
        :attr:`TOOL_PARAM_INPUT` so callers never construct the dynamic-testid
        locator inline (``.claude/rules/page-objects.md``).

        Args:
            field_key: The field's schema property key (e.g. ``"repoName"``).
        """
        return self.page.locator(self.TOOL_PARAM_INPUT.format(field_key))

    @action("Fill a tool-parameter field")
    def fill_param_field(self, field_key: str, value: str, timeout: int = 10000) -> None:
        """Fill *field_key*'s parameter input with *value*.

        MUI text fields don't fire React's ``onChange`` on Playwright's
        ``fill()`` (``.claude/rules/mui-patterns.md``) — uses ``click()`` +
        ``press_sequentially()`` instead, the same discipline every other
        MUI text-field fill in this suite follows.

        Args:
            field_key: The field's schema property key (e.g. ``"repoName"``).
            value: Text to type into the field.
            timeout: Maximum wait time in milliseconds for the input to
                become visible before typing.
        """
        field_input = self.get_param_input(field_key)
        field_input.wait_for(state="visible", timeout=timeout)
        field_input.click()
        field_input.press_sequentially(value, delay=20)

    # ------------------------------------------------------------------
    # Run tool
    # ------------------------------------------------------------------

    @action("Run the selected tool")
    def run_tool(self, timeout: int = 10000) -> None:
        """Click RUN TOOL.

        Args:
            timeout: Maximum wait time in milliseconds for the button to
                become visible before clicking.
        """
        self.run_tool_button.wait_for(state="visible", timeout=timeout)
        self.run_tool_button.click()
        logger.info("Clicked the run-tool button ('Run Test')")

    def get_welcome_message_text(self, timeout: int = 10000) -> str:
        """Return the center panel's current message-list text.

        Before any tool has run, this is the static welcome message
        ("Welcome! Select a tool from the Test Settings panel and click
        'RUN TOOL' to see the results here.") — confirmed live (ELITEA-1866
        implementer Phase 2 exploration) it renders inside the SAME
        :attr:`result_message_list` container :meth:`wait_for_tool_result`
        reads after a run (the container's content is replaced in place,
        not appended to — confirmed live, message count stays at 1 both
        before and after RUN TOOL).

        NOTE (2026-08-27, elitea-testing-public#1815): the PRE-RUN half of the
        description above is HISTORICAL and no longer holds. #1616 moved the
        pre-run message out of this container — `ToolkitTestResults.jsx:29`
        returns `null` while `messages` is empty, so
        :attr:`result_message_list` does not exist at all before the first run
        and calling this method pre-run now times out instead of returning the
        welcome text. The guidance message itself was NOT removed from the
        product: it was relocated and reworded into the Test Settings column's
        empty state (`ToolkitTestEmptyState.jsx:29,35`), where it carries no
        testid and no testid-bearing container, so it cannot be asserted
        testid-only today — a live coverage gap owned by
        elitea-testing-public#1857. This method is retained deliberately for
        #1857 and remains valid for its POST-run use: the container does exist
        once a run has completed.

        Args:
            timeout: Maximum wait time in milliseconds for the container to
                become visible.
        """
        self.result_message_list.wait_for(state="visible", timeout=timeout)
        text = self.result_message_list.text_content() or ""
        logger.info("Center panel message-list text: %r", text[:120])
        return text

    def get_result_items(self):
        """Return the Locator matching every currently-rendered Run Results item.

        Thin wrapper around :attr:`RESULT_MESSAGE_ITEM` so callers (tests)
        never construct the selector inline (``.claude/rules/page-objects.md``)
        — used to assert absence pre-run (``to_have_count(0)``), and by
        :meth:`wait_for_tool_result` for the post-run read.
        """
        return self.page.locator(self.RESULT_MESSAGE_ITEM)

    @action("Wait for the tool-run result to appear")
    def wait_for_tool_result(self, timeout: int = 15000, tool_key: str | None = None) -> str:
        """Wait for the post-RUN-TOOL result to render and return its text.

        AI/tool responses arrive over WebSocket a few seconds after RUN
        TOOL is clicked (this case's own AFS § Network Behavior: confirmed
        live ~0.2-3s) — polls on the result's `success`/`error` prefix
        (`✅`/`❌`) appearing in the message list, never a fixed
        sleep (`.agents/testing.md` § no-sleeps rule).

        NOTE (2026-08-27, elitea-testing-public#1815): that ~0.2-3s figure
        describes the OLD Test Settings surface and no longer sizes the wait.
        The redesigned Test Toolkit surface runs the tool INSIDE a model turn
        (the result lands as a chat answer, under a thought accordion), so the
        realistic budget is a conversation-turn budget, not a REST round-trip
        — which is why ELITEA-1866's caller passes 60_000 against this
        signature's 15_000 default. Callers on the redesigned surface should
        size their own timeout accordingly rather than take the default.

        The container REPLACES its content in place rather than appending
        (confirmed live: the pre-run welcome message and the post-run
        result both render as the sole child of
        :attr:`result_message_list` — a count-based "wait for N+1
        messages" check would never resolve), so this polls on content via
        Playwright's auto-retrying ``expect(...).to_contain_text()``
        instead of a message-count delta.

        Mid-wait panel-remount recovery (ELITEA-1979 batch-gate flake,
        2026-08-02): under sustained backend load (a long run of prior
        AI/LLM-calling tests immediately before this one), the right-hand
        Test Settings panel has been observed to remount back to
        ``TestToolsEmptyState`` (EL-5947) WHILE a run is in flight — the
        selected tool is lost and :attr:`RESULT_MESSAGE_ITEM` empties out,
        so the plain ``expect(...).to_contain_text()`` above times out on
        an empty list instead of ever seeing the ✅/❌ marker. This is a
        real symptom (not a locator bug): the RUN TOOL click for a
        toolkit-parameterized tool hits the toolkit's underlying API
        server-side, mediated by the SAME single, non-scaled local dev
        backend that just finished serving a batch's worth of heavy
        tests — a shared-resource timing issue, not a product defect. When
        *tool_key* is supplied, a single timeout of the initial wait is
        treated as a possible remount: if :attr:`RESULT_MESSAGE_ITEM` is
        confirmed empty (the remount signature, distinguishing this from
        an unrelated timeout with the result still present at count > 0,
        which re-raises immediately), the tool is re-selected from the
        empty state and RUN TOOL is re-clicked once, then the wait resumes
        for the same *timeout* budget. Exactly one recovery attempt — a
        second remount still fails the test. Callers that don't pass
        *tool_key* keep the original single-wait behavior unchanged (this
        page object is shared by every Test Settings caller, most of which
        never hit this load pattern).

        Args:
            timeout: Maximum wait time in milliseconds (applied to the
                initial wait, and again to the post-recovery wait when a
                remount is recovered from).
            tool_key: The tool's schema key (e.g. ``"list_branches_in_repo"``)
                to re-select if a mid-wait panel remount is detected. Pass
                ``None`` (default) to disable recovery — a timeout always
                raises immediately, matching prior behavior. Recovery only
                re-selects the tool and re-clicks RUN TOOL; it does NOT
                refill parameter fields, so it's suited to parameterless
                tool runs (e.g. ``list_branches_in_repo``, which reuses the
                toolkit's own repo config) — a tool with required params
                would need its own recovery.

        Returns:
            The result message's raw text content (e.g. containing
            ``"✅ list_files (0.176s)"`` followed by
            ``"{'total': 0, 'rows': []}"``).
        """
        result_locator = self.page.locator(self.RESULT_MESSAGE_ITEM).last
        try:
            expect(result_locator).to_contain_text(re.compile(r"[✅❌]"), timeout=timeout)
        except AssertionError:
            if tool_key is None or self.get_result_items().count() > 0:
                # Not the remount signature (either recovery is disabled, or
                # the result item is present but never got its ✅/❌ marker —
                # a real failure) — re-raise untouched.
                raise
            logger.warning(
                "Test Settings panel result list emptied mid-wait (RESULT_MESSAGE_ITEM "
                "count=0) — panel remounted to the empty state under load. Re-selecting "
                "%r and re-clicking RUN TOOL once before giving up.",
                tool_key,
            )
            self.select_tool_from_empty_state(tool_key, timeout=10000)
            self.wait_for_panel(timeout=10000)
            self.run_tool(timeout=10000)
            result_locator = self.page.locator(self.RESULT_MESSAGE_ITEM).last
            expect(result_locator).to_contain_text(re.compile(r"[✅❌]"), timeout=timeout)
        text = result_locator.text_content() or ""
        logger.info("Tool-run result: %r", text[:120])
        return text
