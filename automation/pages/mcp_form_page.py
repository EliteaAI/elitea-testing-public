"""MCP / Remote toolkit create + detail form page object.

URLs:
    - Create: ``/mcps/create`` -> select type -> ``/mcps/create/mcp``
    - Detail: ``/mcps/all/{id}``

``ToolBaseProperty.jsx`` (EliteaUI) is a shared, schema-driven field renderer
used by every toolkit/MCP/application creation form — the dynamic
``toolkit-field-{k}-*`` testids are identical between the create form and the
detail (edit) form for a given schema property key ``k``, so this single page
object covers both surfaces (ELITEA-1922 AFS, confirmed live).
"""

import json
import logging
import re
import time

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.mcp_form")

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 20_000


class McpFormPage(BasePage):
    """Remote MCP / toolkit create form and detail (Form / Raw Json) view.

    URL: ``/mcps/create`` (type picker) -> ``/mcps/create/mcp`` (form),
    or ``/mcps/all/{id}`` (detail, same field testids).
    """

    # ------------------------------------------------------------------
    # Type picker (create only)
    # ------------------------------------------------------------------
    remote_mcp_type_card = LocatorDescriptor(
        testid="toolkit-type-card-mcp",
        description="Remote MCP type-selector card on /mcps/create",
    )
    local_empty_state = LocatorDescriptor(
        testid="mcp-type-picker-local-empty-state",
        description="Local MCP section empty-state message on /mcps/create "
        "('Still no local MCP available. Follow creation guides in our "
        "Documentation.') — added ELITEA-1921, commit 750d72f7 on "
        "automation/testids",
    )

    # ------------------------------------------------------------------
    # Shared schema-driven fields (create + detail)
    # ------------------------------------------------------------------
    name_input = LocatorDescriptor(
        testid="toolkit-form-name-input",
        description="Toolkit Name input",
    )
    description_input = LocatorDescriptor(
        testid="toolkit-form-description-input",
        description="Description input",
    )
    url_input = LocatorDescriptor(
        testid="toolkit-field-url-input",
        description="Url input",
    )
    headers_editor = LocatorDescriptor(
        testid="toolkit-field-headers-editor",
        description="Headers JSON CodeMirror editor — outer wrapper Box",
    )
    headers_editor_content = LocatorDescriptor(
        testid="toolkit-field-headers-editor-content",
        description="Headers JSON CodeMirror editor — editable .cm-content node",
    )
    client_id_input = LocatorDescriptor(
        testid="toolkit-field-client_id-input",
        description="Client Id input",
    )
    client_secret_input = LocatorDescriptor(
        testid="toolkit-field-client_secret-input",
        description="Client Secret input wrapper Box (TextField root, not the native input)",
    )
    client_secret_input_field = LocatorDescriptor(
        testid="toolkit-field-client_secret-input-field",
        description="Client Secret — real <input> element (client_secret_input is the wrapper)",
    )
    scopes_input = LocatorDescriptor(
        testid="toolkit-field-scopes-input",
        description="Scopes input",
    )
    timeout_input = LocatorDescriptor(
        testid="toolkit-field-timeout-input",
        description="Timeout input",
    )
    cache_ttl_input = LocatorDescriptor(
        testid="toolkit-field-cache_ttl-input",
        description="Cache TTL input",
    )
    enable_caching_checkbox = LocatorDescriptor(
        testid="toolkit-field-enable_caching-checkbox",
        description="Enable Caching checkbox — MUI span wrapper (click target)",
    )
    enable_caching_checkbox_field = LocatorDescriptor(
        testid="toolkit-field-enable_caching-checkbox-field",
        description="Enable Caching — real <input> element (.checked lives here)",
    )
    ssl_verify_checkbox = LocatorDescriptor(
        testid="toolkit-field-ssl_verify-checkbox",
        description="Ssl Verify checkbox — MUI span wrapper (click target)",
    )
    ssl_verify_checkbox_field = LocatorDescriptor(
        testid="toolkit-field-ssl_verify-checkbox-field",
        description="Ssl Verify — real <input> element (.checked lives here)",
    )

    # ------------------------------------------------------------------
    # View toggle + Raw Json (create + detail)
    # ------------------------------------------------------------------
    form_view_toggle = LocatorDescriptor(
        testid="toolkit-form-view-toggle",
        description="Switch to Form view",
    )
    raw_json_view_toggle = LocatorDescriptor(
        testid="toolkit-raw-json-view-toggle",
        description="Switch to Raw Json view",
    )
    raw_json_editor_content = LocatorDescriptor(
        testid="toolkit-raw-json-editor-content",
        description="Raw Json CodeMirror editor — editable .cm-content node",
    )

    # ------------------------------------------------------------------
    # Save (create form) + detail page title
    # ------------------------------------------------------------------
    save_button = LocatorDescriptor(
        testid="toolkit-form-save-button",
        description="Save button on the create form",
    )
    detail_save_button = LocatorDescriptor(
        testid="toolkit-detail-save-button",
        description="Save button on the detail (edit) page — added ELITEA-1929, "
        "EliteaUI PR #572",
    )
    detail_discard_button = LocatorDescriptor(
        testid="toolkit-detail-discard-button",
        description="Discard button on the detail (edit) page — added ELITEA-1929, "
        "EliteaUI PR #572",
    )
    detail_title = LocatorDescriptor(
        testid="toolkit-detail-title",
        description="Toolkit detail page name heading (renders 'Edit Toolkit' "
        "placeholder until the tool-detail GET resolves)",
    )

    # ------------------------------------------------------------------
    # Three-dot actions menu + delete-confirm dialog (detail page only) —
    # added ELITEA-1947. controls-menu-button/controls-menu are the SAME
    # generic ControlsDropdown/DotMenu testids already used by
    # CredentialDetailPage (default id="controls" — ToolkitsControls.jsx
    # renders via this same shared component with no id override, so the
    # testid string is identical across Toolkits/MCP/Credentials detail
    # pages, per the AFS Concrete Handles table).
    # ------------------------------------------------------------------
    controls_menu_button = LocatorDescriptor(
        testid="controls-menu-button",
        description="Three-dot actions menu button on the MCP detail page",
    )
    controls_menu = LocatorDescriptor(
        testid="controls-menu",
        description="Three-dot actions menu popup (Export/Fork/Copy link/Pin to top/Delete)",
    )
    delete_menuitem = LocatorDescriptor(
        testid="toolkit-actions-delete-menuitem",
        description="'Delete' menu item inside the three-dot menu — added via "
        "add-data-testid for ELITEA-1947 (DeleteToolkitButton.jsx's "
        "useDeleteToolkitMenu() menuItem had no key before this case)",
    )
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete confirmation dialog (DeleteEntityModal, shared across "
        "~15 entity types) — added via add-data-testid for ELITEA-1947",
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description="Delete dialog's type-to-confirm Name field — resolves to the "
        "MUI TextField wrapper, NOT the real <input> (AFS Concrete Handles); "
        "click + press_sequentially() types into the focused inner input, but "
        "never call .input_value() on this locator (throws)",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete dialog's confirm button — disabled until the typed "
        "name matches the entity name exactly — added via add-data-testid for "
        "ELITEA-1947 (two-part fix: OneClickButton.jsx now forwards data-testid, "
        "DeleteEntityModal.jsx passes it)",
    )

    # Scoped selector for use inside wait_for_function's page-context JS
    # (a raw DOM query, not a Playwright locator — mirrors BasePage's own
    # evaluate()-based waits, e.g. dismiss_banner_if_present()).
    DETAIL_TITLE_SELECTOR = '[data-testid="toolkit-detail-title"]'

    # ------------------------------------------------------------------
    # Tools section (Configuration accordion, "TOOLS" sub-heading) —
    # added ELITEA-1933. Testids added to EliteaUI this session
    # (ToolActionsSelector.jsx / EmptyMcpTools.jsx / ToolActionsItems.jsx /
    # ChipWithCheckIcon.jsx / TestToolSettings.jsx), confirmed live.
    # ------------------------------------------------------------------
    tools_empty_state = LocatorDescriptor(
        testid="toolkit-tools-empty-state",
        description="Tools section empty-state message, shown before any tool is loaded",
    )
    load_tools_button = LocatorDescriptor(
        testid="toolkit-load-tools-button",
        description="'Load Tools' clickable label in the Tools section header",
    )
    test_tool_select = LocatorDescriptor(
        testid="toolkit-test-tool-select",
        description="Test Settings panel's 'Tool' select — choosing an option renders "
        "that tool's parameter schema as live input fields (NOT the Tools-section "
        "pill click, which only toggles selected_tools membership — case-text "
        "clarification filed as issue #595, see ELITEA-1933 AFS)",
    )

    # ------------------------------------------------------------------
    # Load Tools sync-error toast + connection status widget — added
    # ELITEA-1934. `toast-message` is the app-wide shared Toast testid (same
    # pattern as skill_detail_page.version_toast_message /
    # skills_list_page.import_success_toast_message /
    # artifacts_page.success_toast_message — each page object declares its
    # OWN named field rather than cross-importing another page object's).
    # `toolkit-connection-status`/`toolkit-connection-auth-button` are NEW
    # testids added via add-data-testid for this case (McpAuthStatus.jsx —
    # the widget had zero testids before, confirmed via the AFS's 6-level
    # DOM ancestor walk).
    # ------------------------------------------------------------------
    sync_error_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide Toast component's message container (reused for "
        "the 'Failed to sync MCP tools: ...' error toast on a failed Load Tools)",
    )
    connection_status = LocatorDescriptor(
        testid="toolkit-connection-status",
        description="MCP connection status widget (globe icon + 'Connected!'/'Not "
        "Connected' text + Login/Logout button) — carries a `data-connected` "
        "true/false state attribute (state-via-data-attribute, per "
        ".agents/testing.md § Locator policy); text_content() includes the "
        "auth button's own label concatenated with no separator, so prefer "
        ":meth:`is_mcp_connected` for the boolean check and "
        ":meth:`get_connection_auth_button_label` for the button's own text",
    )
    connection_auth_button = LocatorDescriptor(
        testid="toolkit-connection-auth-button",
        description="Login/Logout button inside the connection status widget",
    )

    # Dynamic (runtime-parameterized) testid — one MUI Chip per discovered tool.
    # Class-level template constant per .agents/testing.md § Locator policy;
    # never an inline f-string get_by_test_id in a method body.
    TOOL_CHIP = '[data-testid="toolkit-tool-chip-{}"]'
    TOOL_CHIP_PREFIX = '[data-testid^="toolkit-tool-chip-"]'

    # Shared dropdown-option testid family (SingleSelectMenuItem.jsx), same
    # pattern already used by PipelineDetailPage.SELECT_OPTION — this page
    # object's own copy since it has no shared base with pipeline_detail_page.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    # Test Settings panel's schema-rendered parameter fields — one per
    # tool-schema property, keyed by the JSON-schema property name (e.g.
    # "repoName", "question"). Added ELITEA-1933 review pass (EliteaUI
    # CommonStringField.jsx / AnyOfPatternField.jsx, both consumed only via
    # ToolFormContainer.jsx -> TestToolSettings.jsx, so this testid never
    # collides with the create/detail form's own toolkit-field-* testids,
    # which come from a different component (ToolBaseProperty.jsx)). Dynamic
    # class-level template constant per .agents/testing.md § Locator policy —
    # args_schema properties differ per MCP tool, so no fixed testid exists.
    TEST_PARAM_FIELD = '[data-testid="toolkit-test-param-{}"]'

    # Raw Json editor's own testid, fed into page.evaluate() JS (a raw DOM
    # query string, not a Playwright locator) by get_raw_json_full() — same
    # "class-level selector constant consumed by evaluate()" shape as
    # DETAIL_TITLE_SELECTOR above.
    RAW_JSON_EDITOR_SELECTOR = '[data-testid="toolkit-raw-json-editor-content"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to MCP type picker")
    def navigate_to_create(self) -> None:
        """Navigate to ``/mcps/create`` and wait for the type-picker to load.

        The "Choose the MCP type" copy has no data-testid (shared
        ``GroupedCategory``/``CategoryFilter`` title, out of this case's
        touched-element scope per the testid-only locator policy) — the
        type-picker having loaded is instead proven via the testid-bearing
        :attr:`remote_mcp_type_card` becoming visible.
        """
        self.navigate("/mcps/create")
        self.remote_mcp_type_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Select Remote MCP type")
    def select_remote_mcp_type(self) -> None:
        """Click the Remote MCP type card and wait for the create form to load."""
        self.remote_mcp_type_card.click()
        self.page.wait_for_url("**/mcps/create/mcp", timeout=UI_ELEMENT_TIMEOUT)
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Navigate to MCP detail page")
    def navigate_to_detail(self, toolkit_id: int, project_id: str) -> None:
        """Navigate to ``/mcps/all/{id}`` and wait for the Form view to load."""
        with self.page.expect_response(
            lambda r: f"/tool/prompt_lib/{project_id}/{toolkit_id}" in r.url
            and r.request.method == "GET",
            timeout=UI_ELEMENT_TIMEOUT,
        ):
            self.navigate(f"/mcps/all/{toolkit_id}")
        self._wait_for_detail_data_rendered()

    def wait_for_page_load(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the detail page to be ready — used by :meth:`BasePage.reload_and_wait`.

        Delegates to :meth:`_wait_for_detail_data_rendered` (waits past the
        "Edit Toolkit" placeholder), so ``reload_and_wait()`` confirms real
        toolkit data has re-rendered after a full page reload, not just that
        the network went idle (ELITEA-1929 § Automation Hints).

        Note for future callers: ``BasePage.reload_and_wait()`` dispatches to
        this method via ``hasattr(self, 'wait_for_page_load')`` duck-typing —
        defining it here changes ``reload_and_wait()``'s behavior for *every*
        caller of ``McpFormPage`` (e.g. the create-form flow too), not just
        the detail-page flow this method was added for. No current sibling
        caller is affected since ``_wait_for_detail_data_rendered()`` is safe
        to call from any state, but a future create-form-only caller of
        ``reload_and_wait()`` would also route through here.
        """
        self._wait_for_detail_data_rendered()

    def _wait_for_detail_data_rendered(self) -> None:
        """Wait past the 'Edit Toolkit' placeholder until real toolkit data renders.

        The detail title (``toolkit-detail-title``) shows a static "Edit
        Toolkit" placeholder until the tool-detail GET response is applied
        to component state — the response resolving doesn't guarantee the
        title has re-rendered yet (one more React tick), so poll the title
        text itself rather than trusting the network wait alone.
        """
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.page.wait_for_function(
            """(selector) => {
                const el = document.querySelector(selector);
                return !!el && el.textContent.trim() !== '' && el.textContent.trim() !== 'Edit Toolkit';
            }""",
            arg=self.DETAIL_TITLE_SELECTOR,
            timeout=UI_ELEMENT_TIMEOUT,
        )

    # ------------------------------------------------------------------
    # Three-dot actions menu + delete-confirm dialog — added ELITEA-1947.
    # Mirrors CredentialDetailPage.open_controls_menu() (same shared
    # ControlsDropdown/DotMenu component/testids); the delete-confirm dialog
    # methods are new (CredentialDetailPage doesn't yet drive its own Delete
    # flow through these testids — out of this case's scope).
    # ------------------------------------------------------------------

    @action("Open the three-dot actions menu")
    def open_controls_menu(self) -> None:
        """Click the three-dot menu button and wait for the menu popup to render."""
        self.controls_menu_button.click()
        self.controls_menu.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_controls_menu_text(self) -> str:
        """Return the three-dot menu popup's full text content (all menu item labels)."""
        return self.controls_menu.text_content() or ""

    @action("Click the Delete menu item")
    def click_delete_menu_item(self) -> None:
        """Click 'Delete' inside the three-dot menu and wait for the confirm dialog."""
        self.delete_menuitem.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_delete_confirm_dialog_text(self) -> str:
        """Return the delete confirmation dialog's full text content (title + body)."""
        return self.delete_confirm_dialog.text_content() or ""

    def is_delete_confirm_button_enabled(self) -> bool:
        """Return whether the dialog's Delete button is currently enabled."""
        return self.delete_confirm_button.is_enabled()

    @action("Type the entity name into the delete-confirm dialog")
    def fill_delete_confirm_name(self, name: str) -> None:
        """Type *name* into the delete dialog's type-to-confirm Name field.

        ``delete_confirm_name_input`` resolves to the MUI TextField wrapper,
        not the real ``<input>`` (AFS Concrete Handles) — clicking it focuses
        the inner input via browser click-delegation, then
        ``press_sequentially()`` types into the focused input (MUI needs
        keyboard events for React onChange, per
        ``.claude/rules/mui-patterns.md``). Waits for the Delete button to
        become enabled afterwards — the real signal that the typed value has
        propagated to the dialog's controlled-input comparison — rather than
        a fixed delay.
        """
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(name, delay=20)
        expect(self.delete_confirm_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    @action("Confirm deletion and wait for the DELETE response + redirect")
    def confirm_delete(self, project_id: str, toolkit_id: int, timeout: int = SAVE_RESPONSE_TIMEOUT) -> None:
        """Click the dialog's Delete button; wait for the DELETE 204, then the redirect to the list.

        Waits on the real ``DELETE .../tool/prompt_lib/{project}/{id}``
        network response (AFS § Network Behavior) rather than a fixed
        timeout, then waits for the URL to become ``/mcps/all``.

        This redirect is a ``window.history``-based ``navigate(-1)``
        (``DeleteToolkitButton.jsx``) — it only reliably lands on
        ``/mcps/all`` when the detail page was reached via a REAL
        list-card navigation (see :meth:`McpListPage.open_card_by_name`),
        not the create flow's own post-save redirect (AFS § Known Defects
        Found). This method does not — and cannot — enforce that ordering;
        it's the caller's responsibility to have navigated correctly.

        Args:
            project_id: Project id, used to scope the response URL match.
            toolkit_id: The MCP's numeric id, used to scope the response URL match.
            timeout: Maximum wait time in milliseconds.
        """
        with self.page.expect_response(
            lambda r: f"/tool/prompt_lib/{project_id}/{toolkit_id}" in r.url
            and r.request.method == "DELETE"
            and r.status == 204,
            timeout=timeout,
        ):
            self.delete_confirm_button.click()
        self.page.wait_for_url("**/mcps/all", timeout=timeout)

    # ------------------------------------------------------------------
    # Field fills — MUI text inputs need React-safe keyboard events
    # (fill() does not trigger React onChange — .claude/rules/mui-patterns.md).
    # Uses select_text() + Backspace rather than a bare Ctrl+A: on these
    # pre-populated fields (Timeout/Cache TTL default to "300") a plain
    # Control+a keypress did not reliably select the existing value before
    # typing — the new text landed prepended instead of replacing it
    # (observed live: "600" typed into a "300"-filled Timeout produced
    # "600300"). select_text() + Backspace is the same reliable-clear
    # pattern already used by SkillFormPage.fill_instructions/set_description.
    #
    # Every step below waits on the real DOM/focus/selection state it
    # depends on instead of a fixed delay (no waitForTimeout — see
    # _wait_for_input_value_stable for why "wait until stable" rather than
    # "wait until equal to *text*" is used after typing).
    # ------------------------------------------------------------------

    def _wait_for_selection_applied(self, locator, timeout_ms: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait until *locator*'s full value is selected, or it has nothing to select.

        ``Locator.select_text()`` performs the browser selection
        synchronously, but a MUI controlled-input re-render can reset
        ``selectionStart``/``selectionEnd`` on the next tick — poll the
        real DOM selection state (not a fixed delay) before sending
        Backspace, so Backspace can't race a not-yet-applied selection.
        """
        handle = locator.element_handle()
        self.page.wait_for_function(
            """(el) => el.value.length === 0 ||
               (el.selectionStart === 0 && el.selectionEnd === el.value.length)""",
            arg=handle,
            timeout=timeout_ms,
        )

    def _wait_for_input_value_stable(
        self, locator, stable_duration_ms: int = 150, timeout_ms: int = UI_ELEMENT_TIMEOUT
    ) -> None:
        """Poll *locator*'s value until it stops changing for *stable_duration_ms*.

        Used after typing instead of asserting an exact final value: some
        fields cosmetically reformat on input (e.g. Scopes normalizes
        ``"read,write"`` -> ``"read, write"`` — AFS Axis 2), so the final
        DOM value isn't always known ahead of time. Waiting for the value
        to stop mutating is the real signal that typing + any reformat
        handler have both finished — same "poll until unchanged" pattern
        as ``ChatPage.wait_for_message_content_stable``.
        """
        deadline = time.monotonic() + timeout_ms / 1000.0
        stable_duration = stable_duration_ms / 1000.0
        last_value = None
        stable_since = time.monotonic()
        while time.monotonic() < deadline:
            current_value = locator.input_value()
            if current_value != last_value:
                last_value = current_value
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= stable_duration:
                return
            time.sleep(0.05)
        raise TimeoutError(f"Input value did not stabilise within {timeout_ms}ms (last: {last_value!r})")

    def _fill_text_input(self, locator, text: str) -> None:
        locator.click()
        expect(locator).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)
        locator.select_text()
        self._wait_for_selection_applied(locator)
        self.page.keyboard.press("Backspace")
        expect(locator).to_have_value("", timeout=UI_ELEMENT_TIMEOUT)
        self.page.keyboard.type(text)
        self._wait_for_input_value_stable(locator)

    @action("Fill Toolkit Name")
    def fill_name(self, name: str) -> None:
        self._fill_text_input(self.name_input, name)

    @action("Fill Description")
    def fill_description(self, description: str) -> None:
        self._fill_text_input(self.description_input, description)

    @action("Fill Url")
    def fill_url(self, url: str) -> None:
        self._fill_text_input(self.url_input, url)

    def _wait_for_contenteditable_selection_applied(
        self, locator, timeout_ms: int = UI_ELEMENT_TIMEOUT
    ) -> None:
        """Wait until *locator*'s (contenteditable) text is fully selected, or empty.

        CodeMirror's ``.cm-content`` is a contenteditable node, not an
        ``<input>`` — it has no ``selectionStart``/``selectionEnd``, so the
        real DOM selection state is read via ``window.getSelection()``
        instead. Same purpose as ``_wait_for_selection_applied``: don't send
        Backspace before the browser selection has actually applied.
        """
        handle = locator.element_handle()
        self.page.wait_for_function(
            """(el) => el.textContent.length === 0 ||
               (window.getSelection() &&
                window.getSelection().toString().length === el.textContent.length)""",
            arg=handle,
            timeout=timeout_ms,
        )

    def _wait_for_text_content_stable(
        self, locator, stable_duration_ms: int = 150, timeout_ms: int = UI_ELEMENT_TIMEOUT
    ) -> None:
        """Poll *locator*'s ``text_content()`` until it stops changing.

        CodeMirror equivalent of ``_wait_for_input_value_stable`` — waits
        for the editor's rendered text to converge (typing + any CodeMirror
        formatting/line-wrap re-render) rather than a fixed delay.
        """
        deadline = time.monotonic() + timeout_ms / 1000.0
        stable_duration = stable_duration_ms / 1000.0
        last_text = None
        stable_since = time.monotonic()
        while time.monotonic() < deadline:
            current_text = locator.text_content() or ""
            if current_text != last_text:
                last_text = current_text
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= stable_duration:
                return
            time.sleep(0.05)
        raise TimeoutError(f"Editor text did not stabilise within {timeout_ms}ms (last: {last_text!r})")

    @action("Fill Headers JSON editor")
    def fill_headers_json(self, json_text: str) -> None:
        """Replace the Headers CodeMirror editor content with *json_text*.

        CodeMirror does not respond to ``fill()``. Uses the same
        select-then-Backspace-then-type sequence as
        :meth:`SkillFormPage.fill_instructions` (proven reliable against
        both an empty and a pre-populated editor — plain ``Ctrl+A`` alone
        does not always select existing content first). Each step waits on
        the editor's real focus/selection/content state, not a fixed delay.
        """
        self.headers_editor.click()
        expect(self.headers_editor_content).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)
        self.headers_editor_content.select_text()
        self._wait_for_contenteditable_selection_applied(self.headers_editor_content)
        self.page.keyboard.press("Backspace")
        expect(self.headers_editor_content).to_have_text("", timeout=UI_ELEMENT_TIMEOUT)
        self.page.keyboard.type(json_text)
        self._wait_for_text_content_stable(self.headers_editor_content)

    def get_headers_json_text(self) -> str:
        """Return the current text content of the Headers CodeMirror editor."""
        return self.headers_editor_content.text_content() or ""

    @action("Edit a single line in the Raw Json editor")
    def fill_raw_json_line(self, current_line_text: str, new_line_text: str) -> None:
        """Replace one line of the Raw Json CodeMirror editor with *new_line_text*.

        DECLARED IMPROVISATION (lead-approved, 2026-07-16): the Raw Json
        editor's per-line ``<div>`` nodes are CodeMirror-internal render
        nodes, not app JSX — no testid can be placed on them (analogous to
        the third-party-widget Stop+flag exception, e.g. ReactFlow's
        ``rf__wrapper``, per ``.agents/testing.md`` § Locator policy).
        ``get_by_text()`` scoped inside the testid-anchored
        ``raw_json_editor_content`` parent (itself a
        ``LocatorDescriptor(testid=...)`` field) is the sanctioned pattern
        for this specific canon-gap; do not extend it to any handle that
        COULD carry a testid.

        The Raw Json editor (``toolkit-raw-json-editor-content``) is a
        CodeMirror ``.cm-content`` node rendering one ``<div>`` per JSON
        line — NOT a single contenteditable blob. A whole-document select
        (``Ctrl+A`` / ``Ctrl+Home``+``Ctrl+Shift+End``) followed by delete
        does **not** reliably clear the entire document in this environment
        (confirmed live at ELITEA-1927 implementer exploration: one attempt
        left a stray character behind, producing invalid JSON). The
        reliable approach is per-line: locate the target line's own
        ``<div>`` by its current text (matching :meth:`fill_headers_json`'s
        select-then-type discipline, scoped to a single line), click it,
        select just that line via ``Home``/``Shift+End``, then type the
        full replacement line (including trailing comma/brace) to overwrite
        the selection.

        Args:
            current_line_text: Exact current text of the target line (used
                to locate the line's div via ``get_by_text(..., exact=True)``
                scoped inside the editor).
            new_line_text: Full replacement text for that line.
        """
        line = self.raw_json_editor_content.get_by_text(current_line_text, exact=True)
        line.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self._wait_for_line_selection_applied(line)
        self.page.keyboard.type(new_line_text)
        self._wait_for_text_content_stable(self.raw_json_editor_content)

    def _wait_for_line_selection_applied(self, line_locator, timeout_ms: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait until *line_locator*'s content is selected via ``Home``/``Shift+End``.

        Unlike :meth:`_wait_for_contenteditable_selection_applied` (used for
        whole-editor selection where the editable text has no leading
        indentation), a Raw Json line's ``textContent`` includes leading
        indentation whitespace that ``Home`` does not select (``Home`` moves
        to the first non-whitespace character, confirmed live at ELITEA-1927
        implementer exploration — e.g. a 22-char indented line yields a
        20-char selection). Comparing against the *trimmed* text length is
        the correct equality check here.
        """
        handle = line_locator.element_handle()
        self.page.wait_for_function(
            """(el) => {
                const trimmedLen = el.textContent.trim().length;
                const sel = window.getSelection();
                return trimmedLen === 0 || (sel && sel.toString().length === trimmedLen);
            }""",
            arg=handle,
            timeout=timeout_ms,
        )

    @action("Fill Client Id")
    def fill_client_id(self, client_id: str) -> None:
        self._fill_text_input(self.client_id_input, client_id)

    @action("Fill Client Secret")
    def fill_client_secret(self, secret: str) -> None:
        self._fill_text_input(self.client_secret_input_field, secret)

    def get_client_secret_value(self) -> str:
        """Return the raw DOM value of the (visually masked) Client Secret input."""
        return self.client_secret_input_field.input_value()

    @action("Fill Scopes")
    def fill_scopes(self, scopes: str) -> None:
        self._fill_text_input(self.scopes_input, scopes)

    def get_scopes_value(self) -> str:
        return self.scopes_input.input_value()

    @action("Fill Timeout")
    def fill_timeout(self, timeout_value: str) -> None:
        self._fill_text_input(self.timeout_input, timeout_value)

    @action("Fill Cache TTL")
    def fill_cache_ttl(self, cache_ttl_value: str) -> None:
        self._fill_text_input(self.cache_ttl_input, cache_ttl_value)

    # ------------------------------------------------------------------
    # Checkboxes — the *_checkbox testid is the MUI <span> click target;
    # the *_checkbox_field testid is the real <input> that carries .checked.
    # ------------------------------------------------------------------

    def is_enable_caching_checked(self) -> bool:
        return self.enable_caching_checkbox_field.is_checked()

    def is_ssl_verify_checked(self) -> bool:
        return self.ssl_verify_checkbox_field.is_checked()

    @action("Toggle Enable Caching checkbox")
    def click_enable_caching_checkbox(self) -> None:
        """Click the Enable Caching checkbox and wait for its checked state to flip.

        Same wait-on-real-``<input>``-state approach as
        :meth:`click_ssl_verify_checkbox` (the ``enable_caching_checkbox``
        testid is only the MUI ``<span>`` click target).
        """
        was_checked = self.enable_caching_checkbox_field.is_checked()
        self.enable_caching_checkbox.click()
        if was_checked:
            expect(self.enable_caching_checkbox_field).not_to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
        else:
            expect(self.enable_caching_checkbox_field).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    @action("Toggle Ssl Verify checkbox")
    def click_ssl_verify_checkbox(self) -> None:
        """Click the Ssl Verify checkbox and wait for its checked state to flip.

        Waits on the real ``<input>``'s ``.checked`` state (the
        ``ssl_verify_checkbox`` testid is only the MUI ``<span>`` click
        target) instead of a fixed delay, so a slow React re-render can't
        race the caller's next assertion.
        """
        was_checked = self.ssl_verify_checkbox_field.is_checked()
        self.ssl_verify_checkbox.click()
        if was_checked:
            expect(self.ssl_verify_checkbox_field).not_to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
        else:
            expect(self.ssl_verify_checkbox_field).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    # ------------------------------------------------------------------
    # Save + view toggle
    # ------------------------------------------------------------------

    def is_save_button_disabled(self) -> bool:
        """Return whether the create form's Save button is currently disabled.

        Save's enabled/disabled toggle is dirty-based, not required-field-
        completeness-based (flips to enabled the instant ANY field is
        touched) — added for ELITEA-1921, see CLARIFICATION #633. Callers
        should assert the pristine-form (disabled) and both-required-
        fields-filled (enabled) states only; an intermediate single-field
        assertion is a documented flake trap (ELITEA-1921 AFS Test Steps
        step 7 note).
        """
        return self.save_button.is_disabled()

    @action("Click Save and wait for the toolkit to be created")
    def save_and_wait_for_created(self, project_id: str, timeout: int = SAVE_RESPONSE_TIMEOUT) -> dict:
        """Click Save, wait for the create POST's 201 response, return its JSON body.

        Waits on the network response itself (not a fixed timeout or URL
        poll) — the Save button's onClick fires an async event-emitter
        chain with a ``setTimeout(..., 0)`` inside, so a UI-state poll is
        not a reliable signal (ELITEA-1922 AFS § Automation Hints).

        Args:
            project_id: Project id, used to scope the response URL match.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the ``201 Created`` response (contains ``id``).
        """
        with self.page.expect_response(
            lambda r: f"/tools/prompt_lib/{project_id}" in r.url
            and r.request.method == "POST"
            and r.status == 201,
            timeout=timeout,
        ) as response_info:
            self.save_button.click()
        body = response_info.value.json()
        self.page.wait_for_url("**/mcps/all/**", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_detail_data_rendered()
        return body

    @action("Click Save on the detail page and wait for the toolkit to be updated")
    def save_and_wait_for_updated(
        self, project_id: str, toolkit_id: int, timeout: int = SAVE_RESPONSE_TIMEOUT
    ) -> dict:
        """Click Save on the detail (edit) page, wait for the update PUT's 200, return its JSON body.

        Mirrors :meth:`save_and_wait_for_created` for the detail page's own
        Save button (``toolkit-detail-save-button``, added ELITEA-1929) —
        waits on the real ``PUT .../tool/prompt_lib/{project}/{id}`` network
        response instead of a fixed timeout or UI-state poll (ELITEA-1929 AFS
        § Automation Hints).
        """
        with self.page.expect_response(
            lambda r: f"/tool/prompt_lib/{project_id}/{toolkit_id}" in r.url
            and r.request.method == "PUT"
            and r.status == 200,
            timeout=timeout,
        ) as response_info:
            self.detail_save_button.click()
        return response_info.value.json()

    @action("Switch to Raw Json view")
    def switch_to_raw_json_view(self) -> None:
        self.raw_json_view_toggle.click()
        self.raw_json_editor_content.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Switch to Form view")
    def switch_to_form_view(self) -> None:
        self.form_view_toggle.click()
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_raw_json(self) -> dict:
        """Read and parse the Raw Json view's current content as JSON."""
        text = self.raw_json_editor_content.text_content() or ""
        return json.loads(text)

    def get_raw_json_full(self) -> dict:
        """Read and parse the Raw Json view's FULL content, working around CodeMirror virtualization.

        :meth:`get_raw_json` reads ``raw_json_editor_content.text_content()`` in a
        single call, which silently truncates on a payload this large — CodeMirror
        only keeps a viewport-sized window of ``.cm-line`` nodes in the DOM at a
        time (confirmed live at ELITEA-1933 implementer exploration: a 3-tool
        ``available_mcp_tools`` payload truncates mid-schema at ~30 of ~85 lines
        with NO error — the read either raises ``json.JSONDecodeError`` or, worse,
        happens to end on a coincidentally-valid partial JSON that silently passes
        an assertion against the wrong data).

        Declared as a NEW method rather than a modification of
        :meth:`get_raw_json` per the additive-only shared-caller-file rule
        (test-automation-workflow skill § Hard Rules → 3): three existing specs
        (``test_mcp_create_remote.py``, ``test_mcp_edit_raw_json_description.py``,
        ``test_mcp_edit_toggle_enable_caching.py``) call ``get_raw_json()`` today
        against small (<30-line) payloads where the truncation never triggers —
        changing that method's body would have been an unproven behavior change
        for those callers, so this case gets its own method instead. All three
        callers re-ran green, unmodified, against this same commit (see PR
        description).

        Approach: the CodeMirror ``.cm-content`` node itself never overflows (its
        own ``scrollHeight`` always equals its ``clientHeight`` — it grows to fit
        the full document), so scrolling it directly is a no-op. The actual
        scrollable ancestor (a MUI Grid column wrapping the whole Configuration
        panel) is what CodeMirror's internal viewport-visibility tracking keys
        off — found by walking up from the editor for the first ancestor with
        real overflow (``scrollHeight > clientHeight``), rather than hardcoding a
        MUI-generated ``css-*`` class name (confirmed live: the class hash is not
        a stable selector).

        Scrolls that ancestor in ``clientHeight``-sized steps from 0 to its
        ``scrollHeight``; after each step, reads every currently-rendered
        ``.cm-line`` node's ``offsetTop`` (stable within the CM6 document — a
        given line keeps the same absolute offset no matter which scroll
        position revealed it) paired with its text. Aggregating by ``offsetTop``
        across all steps both de-duplicates lines seen more than once (adjacent
        scroll windows overlap) and reconstructs correct document order (final
        sort by that same key). A single scroll-to-bottom-then-read does NOT
        work: CodeMirror replaces its rendered line set on each scroll rather
        than extending it (confirmed live — scrolling straight to the bottom
        surfaces only the last ~53 lines, never the first ~30).

        Returns:
            The full Raw Json payload, parsed.
        """
        ancestor_meta = self.page.evaluate(
            """(selector) => {
                const el = document.querySelector(selector);
                let node = el;
                while (node && node !== document.body) {
                    const cs = getComputedStyle(node);
                    if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll')
                            && node.scrollHeight > node.clientHeight) {
                        return {scrollHeight: node.scrollHeight, clientHeight: node.clientHeight};
                    }
                    node = node.parentElement;
                }
                return null;
            }""",
            self.RAW_JSON_EDITOR_SELECTOR,
        )
        if ancestor_meta is None:
            # No scrollable ancestor — the whole document already fits in one
            # render (small payload), so a single text_content() read is
            # complete and correct (same read get_raw_json() performs).
            return self.get_raw_json()

        collected: dict[int, str] = {}
        # Half the viewport height per step (not clientHeight - a fixed small
        # margin) — CodeMirror's render window varies with viewport size
        # (confirmed live: a headless run's narrower viewport left a gap between
        # scroll steps that a fixed "-40" margin didn't cover, producing invalid
        # JSON), so a proportional 50% overlap is used instead to stay safe
        # across viewport sizes.
        step = max(ancestor_meta["clientHeight"] // 2, 50)
        scroll_height = ancestor_meta["scrollHeight"]
        positions = list(range(0, scroll_height, step)) + [scroll_height]
        for pos in positions:
            # Async evaluate: set scrollTop, then await two animation frames
            # before reading .cm-line — CodeMirror's viewport-visibility
            # recompute is itself rAF-scheduled off the scroll event, so a
            # synchronous set-then-read in one tick (the first version of this
            # method) sometimes read the PREVIOUS scroll position's rendered
            # lines, leaving a gap between steps that broke the reconstructed
            # JSON (confirmed live: passed when driven by separate slow
            # subprocess calls during manual exploration, failed under pytest's
            # faster back-to-back calls). Two rAFs is a condition-based wait on
            # the browser's own render pipeline, not an arbitrary sleep.
            pairs = self.page.evaluate(
                """async ([selector, scrollTop]) => {
                    const el = document.querySelector(selector);
                    let node = el;
                    while (node && node !== document.body) {
                        const cs = getComputedStyle(node);
                        if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll')
                                && node.scrollHeight > node.clientHeight) {
                            node.scrollTop = scrollTop;
                            break;
                        }
                        node = node.parentElement;
                    }
                    await new Promise(resolve => requestAnimationFrame(
                        () => requestAnimationFrame(resolve)
                    ));
                    return Array.from(el.querySelectorAll('.cm-line')).map(
                        line => [line.offsetTop, line.textContent]
                    );
                }""",
                [self.RAW_JSON_EDITOR_SELECTOR, pos],
            )
            for top, text in pairs:
                collected[top] = text

        full_text = "\n".join(collected[top] for top in sorted(collected))
        return json.loads(full_text)

    def get_detail_heading_text(self) -> str:
        """Return the toolkit detail page's title heading text.

        The title has no accessible heading role (a plain MUI Typography
        ``<span>``) — located via its own ``toolkit-detail-title`` testid,
        not an ``h1`` (the live product renders no ``<h1>`` on this page;
        confirmed at ELITEA-1922 implementer exploration).
        """
        return self.detail_title.text_content() or ""

    def get_toolkit_id_from_url(self) -> int:
        """Extract the numeric MCP/toolkit id from the current detail-page URL.

        URL shape: ``/mcps/all/{numeric_id}`` or
        ``/mcps/all/{numeric_id}?viewMode=owner&name=...`` — mirrors
        ``CredentialDetailPage.get_credential_id_from_url()`` (same regex
        mechanism, different entity path).
        """
        match = re.search(r"/mcps/all/(\d+)", self.page.url)
        assert match, f"Expected a numeric MCP id in the URL, got: {self.page.url}"
        return int(match.group(1))

    # ------------------------------------------------------------------
    # Tools section — Load Tools, discovered tool pills — added ELITEA-1933
    # ------------------------------------------------------------------

    def get_tools_empty_state_text(self) -> str:
        """Return the Tools section's empty-state message text (shown before Load Tools)."""
        return self.tools_empty_state.text_content() or ""

    @action("Click Load Tools and wait for tools discovery to resolve")
    def click_load_tools(self, project_id: str, timeout: int = SAVE_RESPONSE_TIMEOUT) -> dict:
        """Click "Load Tools" and wait for the tools-discovery POST to resolve.

        Waits on the real ``POST .../mcp_sync_tools/prompt_lib/{project}
        ?await_response=true`` response (the actual tools-discovery call) rather
        than the transient "Successfully fetched N tools" toast (auto-dismisses,
        unreliable timing) or a fixed timeout (AFS § Automation Hints /
        Network Behavior).

        Args:
            project_id: Project id, used to scope the response URL match.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the ``200`` ``mcp_sync_tools`` response.
        """
        with self.page.expect_response(
            lambda r: f"/mcp_sync_tools/prompt_lib/{project_id}" in r.url
            and "await_response=true" in r.url
            and r.request.method == "POST"
            and r.status == 200,
            timeout=timeout,
        ) as response_info:
            self.load_tools_button.click()
        return response_info.value.json()

    def get_discovered_tool_names(self) -> list[str]:
        """Return the tool names of every discovered-tool pill in the Tools section.

        Reads each pill's dynamic ``toolkit-tool-chip-{tool_name}`` testid (see
        :attr:`TOOL_CHIP_PREFIX`) rather than its visible label — the label is a
        cosmetically reformatted display string (e.g. ``read_wiki_structure`` ->
        "Read wiki structure"), while the testid suffix carries the tool's raw
        ``value`` (the same identifier used in Raw Json's ``available_mcp_tools``/
        ``selected_tools``), so this is the stable cross-check handle.
        """
        prefix = "toolkit-tool-chip-"
        chips = self.page.locator(self.TOOL_CHIP_PREFIX)
        testids = [chips.nth(i).get_attribute("data-testid") or "" for i in range(chips.count())]
        return [t[len(prefix):] for t in testids if t.startswith(prefix)]

    def is_tool_chip_selected(self, tool_name: str) -> bool:
        """Return whether the discovered-tool pill for *tool_name* shows the checkmark (is selected).

        Reads the ``data-selected`` state attribute (UI-team ruling — testid is
        stable identity, state lives in a separate ``data-*`` attribute, never
        baked into the testid itself), not the checkmark icon's presence via a
        CSS/SVG selector.
        """
        chip = self.page.locator(self.TOOL_CHIP.format(tool_name))
        return chip.get_attribute("data-selected") == "true"

    @action("Toggle a discovered tool's selection")
    def toggle_tool_selected(self, tool_name: str) -> None:
        """Click the discovered-tool pill for *tool_name*, toggling its ``selected_tools`` membership.

        Named ``toggle_tool_selected`` rather than a "click shows details"-style
        name — the case text's step 8 ("clicking a tool shows details/schema") is
        the AFS's case-text clarification (issue #595): a Tools-section pill click
        only toggles selection, it never opens a schema panel. Use
        :meth:`select_test_tool` for the schema-on-select behavior.
        """
        was_selected = self.is_tool_chip_selected(tool_name)
        self.page.locator(self.TOOL_CHIP.format(tool_name)).click()
        expected = "false" if was_selected else "true"
        expect(self.page.locator(self.TOOL_CHIP.format(tool_name))).to_have_attribute(
            "data-selected", expected, timeout=UI_ELEMENT_TIMEOUT
        )

    @action("Select a tool in the Test Settings panel")
    def select_test_tool(self, tool_name: str) -> None:
        """Open the Test Settings "Tool" dropdown and select *tool_name*.

        This is the affordance that actually renders the tool's parameter schema
        as live input fields — NOT the Tools-section pill click (AFS step 9 /
        issue #595 case-text clarification).
        """
        self.test_tool_select.click()
        option = self.page.locator(self.SELECT_OPTION.format(tool_name))
        option.click(timeout=UI_ELEMENT_TIMEOUT)

    def is_test_param_field_visible(self, field_key: str, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Wait for and return whether the Test Settings panel's *field_key* parameter field is visible.

        *field_key* is the JSON-schema property name (e.g. ``"repoName"``,
        ``"question"``) rendered after :meth:`select_test_tool` — see
        :attr:`TEST_PARAM_FIELD`.
        """
        field = self.page.locator(self.TEST_PARAM_FIELD.format(field_key))
        field.wait_for(state="visible", timeout=timeout)
        return field.is_visible()

    # ------------------------------------------------------------------
    # Connection status widget — added ELITEA-1934
    # ------------------------------------------------------------------

    def is_mcp_connected(self) -> bool:
        """Return whether the connection status widget reports 'Connected!' (data-connected="true").

        Reads the ``data-connected`` state attribute (UI-team ruling — testid is
        stable identity, state lives in a separate ``data-*`` attribute, never
        baked into the testid itself — same pattern as
        :meth:`is_tool_chip_selected`), not the "Connected!"/"Not Connected"
        text (which the widget's own testid captures concatenated with the
        auth button's label, e.g. ``"Not ConnectedLogin"``, confirmed live).
        """
        return self.connection_status.get_attribute("data-connected") == "true"

    def get_connection_auth_button_label(self) -> str:
        """Return the connection status widget's Login/Logout button label.

        ``"Login"`` when disconnected, ``"Logout"`` when connected — located via
        its own ``toolkit-connection-auth-button`` testid rather than parsed out
        of the wider widget's concatenated text content.
        """
        return self.connection_auth_button.text_content() or ""
