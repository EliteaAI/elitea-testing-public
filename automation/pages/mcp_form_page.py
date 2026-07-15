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

from playwright.sync_api import Page

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
    # ------------------------------------------------------------------

    def _fill_text_input(self, locator, text: str) -> None:
        locator.click()
        self.page.wait_for_timeout(150)
        locator.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(text)
        self.page.wait_for_timeout(200)

    @action("Fill Toolkit Name")
    def fill_name(self, name: str) -> None:
        self._fill_text_input(self.name_input, name)

    @action("Fill Description")
    def fill_description(self, description: str) -> None:
        self._fill_text_input(self.description_input, description)

    @action("Fill Url")
    def fill_url(self, url: str) -> None:
        self._fill_text_input(self.url_input, url)

    @action("Fill Headers JSON editor")
    def fill_headers_json(self, json_text: str) -> None:
        """Replace the Headers CodeMirror editor content with *json_text*.

        CodeMirror does not respond to ``fill()``. Uses the same
        select-then-Backspace-then-type sequence as
        :meth:`SkillFormPage.fill_instructions` (proven reliable against
        both an empty and a pre-populated editor — plain ``Ctrl+A`` alone
        does not always select existing content first).
        """
        self.headers_editor.click()
        self.page.wait_for_timeout(200)
        self.headers_editor_content.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(json_text)
        self.page.wait_for_timeout(300)

    def get_headers_json_text(self) -> str:
        """Return the current text content of the Headers CodeMirror editor."""
        return self.headers_editor_content.text_content() or ""

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

    @action("Toggle Ssl Verify checkbox")
    def click_ssl_verify_checkbox(self) -> None:
        self.ssl_verify_checkbox.click()
        self.page.wait_for_timeout(200)

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

    @action("Switch to Raw Json view")
    def switch_to_raw_json_view(self) -> None:
        self.raw_json_view_toggle.click()
        self.raw_json_editor_content.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.page.wait_for_timeout(300)

    @action("Switch to Form view")
    def switch_to_form_view(self) -> None:
        self.form_view_toggle.click()
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.page.wait_for_timeout(300)

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
