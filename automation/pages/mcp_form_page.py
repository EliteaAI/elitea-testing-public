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

    # Scoped selector for use inside wait_for_function's page-context JS
    # (a raw DOM query, not a Playwright locator — mirrors BasePage's own
    # evaluate()-based waits, e.g. dismiss_banner_if_present()).
    DETAIL_TITLE_SELECTOR = '[data-testid="toolkit-detail-title"]'

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

    def get_detail_heading_text(self) -> str:
        """Return the toolkit detail page's title heading text.

        The title has no accessible heading role (a plain MUI Typography
        ``<span>``) — located via its own ``toolkit-detail-title`` testid,
        not an ``h1`` (the live product renders no ``<h1>`` on this page;
        confirmed at ELITEA-1922 implementer exploration).
        """
        return self.detail_title.text_content() or ""
