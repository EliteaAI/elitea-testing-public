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
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.mcp_form")

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 20_000

# Placeholder labels the detail title shows BEFORE the tool-detail GET is
# applied to component state. EliteaUI keeps one fallbackLabel per entity
# type in src/[fsd]/shared/lib/constants/breadcrumb.constants.js:
#   toolkits -> "Edit Toolkit"   (line 15)
#   mcps     -> "Edit MCP"       (line 47)
# Both must be excluded, or the wait below returns immediately on the MCP
# detail page and callers read the placeholder as if it were the name
# (found at ELITEA-1923/1924: only "Edit Toolkit" was listed, so the wait
# was a no-op for every /mcps/all/{id} caller).
DETAIL_TITLE_PLACEHOLDERS = ("Edit Toolkit", "Edit MCP")


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
    category_filter_tab = LocatorDescriptor(
        testid="category-filter-tab",
        description=(
            "'Local'/'Remote' category filter tab above the type-card "
            "grid (CategoryFilter.jsx) — 2 instances rendered page-wide; "
            "disambiguate via .filter(has_text=...), same multi-instance "
            "idiom as ChatPage.PLUS_MENU_ITEM_SUFFIX (ELITEA-2085)."
        ),
    )
    local_empty_state = LocatorDescriptor(
        testid="mcp-type-picker-local-empty-state",
        description="Local MCP section empty-state message on /mcps/create "
        "('Still no local MCP available. Follow creation guides in our "
        "Documentation.') — added ELITEA-1921, commit 750d72f7 on "
        "automation/testids",
    )

    # Type-picker elements added for ELITEA-1949 (EliteaAI/EliteaUI@f4ce7128 +
    # EliteaAI/EliteaUI@989db4f0 on automation/testids). The heading and the
    # filter chips render through the SHARED CategoryFilter.jsx, so the testids
    # are supplied as `titleTestId` / `chipTestIdPrefix` props from the
    # standalone `/mcps/create` call site only (CreateToolkit.jsx) — the in-chat
    # MCP canvas (ToolkitEditor.jsx) deliberately keeps the generic
    # `category-filter-tab` chips that `select_remote_category_tab()` binds to.
    type_picker_heading = LocatorDescriptor(
        testid="mcp-type-picker-heading",
        description="'Choose the MCP type' heading on /mcps/create",
    )
    local_documentation_link = LocatorDescriptor(
        testid="mcp-type-picker-local-documentation-link",
        description="'Documentation' external link inside the Local MCP "
        "empty-state message on /mcps/create",
    )
    no_results_title = LocatorDescriptor(
        testid="catalog-no-results-title",
        description="Type-picker catalog empty-result title ('No MCPs found')",
    )
    no_results_description = LocatorDescriptor(
        testid="catalog-no-results-description",
        description="Type-picker catalog empty-result description "
        "('Try adjusting your search terms')",
    )

    # Per-chip type filters on /mcps/create. Selection state is a `data-*`
    # attribute on the SAME testid'd element (never a state-switched testid) —
    # `.agents/testing.md` § Locator policy, PR #581 ruling.
    TYPE_FILTER_CHIP = '[data-testid="mcp-type-picker-filter-chip-{}"]'
    TYPE_FILTER_CHIP_SELECTED = (
        '[data-testid="mcp-type-picker-filter-chip-{}"][data-selected="true"]'
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
    # Secret/Password "secret view toggler" rendered beside every SECRET schema
    # field — added ELITEA-1932. Both testids are emitted generically by the
    # shared SecretField.jsx (line 342), which passes
    # testIdPrefix={`${fieldTestId}-toggle`} down to Toggle.jsx, so the pair
    # exists for free on every secret field (same grammar
    # CredentialCreatePage.FIELD_SECRET_TOGGLE already uses for credentials).
    # Active mode is read from `aria-pressed`, never from a class.
    client_secret_toggle_secret = LocatorDescriptor(
        testid="toolkit-field-client_secret-input-toggle-secret",
        description="'Secret' button of the Client Secret secret-view toggler",
    )
    client_secret_toggle_password = LocatorDescriptor(
        testid="toolkit-field-client_secret-input-toggle-password",
        description="'Password' button of the Client Secret secret-view toggler",
    )
    # In Secret mode the native <input> is UNMOUNTED and replaced by a
    # SingleSelect over the project's secret vault (and vice versa), so exactly
    # one of client_secret_input_field / client_secret_combobox exists at a time.
    client_secret_combobox = LocatorDescriptor(
        testid="toolkit-field-client_secret-input-combobox",
        description="Client Secret vault SingleSelect — present only in Secret mode",
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
    # Detail-page configuration section — added ELITEA-1923/1924.
    #
    # On the DETAIL page (unlike the create form) the schema-driven
    # configuration fields are COLLAPSED behind a "show more" control: no
    # `toolkit-field-*` element exists in the DOM at all until it is clicked
    # (verified live 2026-08-24 — polled 15s on a freshly-created MCP, zero
    # toolkit-field-* testids present). Any detail-page assertion on url /
    # client_id / timeout / ... must expand the section first.
    # ------------------------------------------------------------------
    configuration_show_more = LocatorDescriptor(
        testid="toolkit-configuration-show-more",
        description="'Show more' toggle that expands the collapsed "
        "schema-driven configuration fields on the toolkit/MCP detail page",
    )

    # ------------------------------------------------------------------
    # Inline validation helper text (create form) — added ELITEA-1923/1924.
    #
    # Two DIFFERENT renderers are involved, which is why the two testids do
    # not share a prefix:
    #   * every schema-driven field (url, client_id, timeout, ...) renders
    #     through ToolBaseProperty.jsx, which already emits
    #     helperTextTestId={`toolkit-field-${k}-input-helper-text`};
    #   * Toolkit Name renders through NameDescriptionInput.jsx, which did
    #     NOT pass helperTextTestId at all — added for ELITEA-1924
    #     (EliteaAI/EliteaUI@35440c78 on automation/testids).
    #
    # Both nodes are UNMOUNTED (not hidden) once the field becomes valid, so
    # assert their absence with to_have_count(0), never not_to_be_visible().
    # ------------------------------------------------------------------
    name_helper_text = LocatorDescriptor(
        testid="toolkit-form-name-input-helper-text",
        description="Inline validation message under the Toolkit Name field "
        "('Field is required')",
    )
    url_helper_text = LocatorDescriptor(
        testid="toolkit-field-url-input-helper-text",
        description="Inline validation message under the Url field "
        "('Field is required')",
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
    # Discard raises a confirmation modal before reverting anything (see
    # McpFormPage.click_discard) — testids added for ELITEA-1928,
    # EliteaAI/EliteaUI@a51c9318 on automation/testids.
    discard_confirm_modal = LocatorDescriptor(
        testid="toolkit-detail-discard-confirm-modal",
        description="Discard-changes confirmation modal on the detail (edit) page "
        "— the testid lands on the MUI Dialog root, so text_content() includes "
        "the title and both button labels",
    )
    discard_confirm_button = LocatorDescriptor(
        testid="toolkit-detail-discard-confirm-button",
        description="'Discard' confirm button inside the discard-changes modal",
    )
    detail_title = LocatorDescriptor(
        testid="toolkit-detail-title",
        description="Toolkit detail page name heading (renders 'Edit Toolkit' "
        "placeholder until the tool-detail GET resolves)",
    )

    # ------------------------------------------------------------------
    # Breadcrumb trail (detail page only) — added ELITEA-1961.
    #
    # `/mcps/all/:id` declares a breadcrumb trail (`breadcrumb.constants.js`)
    # and `EditToolkit.jsx` renders
    # `hasBreadcrumbTrail ? <Breadcrumbs/> : (<BackButton/> + title)`, so the
    # BackButton branch is unreachable on this route no matter how the user
    # arrived. `back_button` below is therefore bound for an ABSENCE
    # assertion only, which keeps that finding test-enforced instead of
    # documentation-only (CLARIFICATION #1731; .agents/testing.md § Locator
    # policy, #511 extension). `AgentDetailPage` and `SkillDetailPage` already
    # declare the same shared app-shell testid on their own classes — a third
    # declaration is the established shape here, not a duplication.
    # ------------------------------------------------------------------
    breadcrumbs_nav = LocatorDescriptor(
        testid="breadcrumbs",
        description="Breadcrumb <nav> on the MCP detail page (absent on the MCP list page)",
    )
    breadcrumb_parent_link = LocatorDescriptor(
        testid="breadcrumb-item",
        description="Parent crumb link ('MCPs') inside the breadcrumb trail — "
        "exactly one of these renders on the MCP detail page",
    )
    back_button = LocatorDescriptor(
        testid="back-button",
        description="Shared app-shell back arrow — NEVER rendered on /mcps/all/:id; "
        "bound for the absence assertion of ELITEA-1961 / #1731",
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
    # Remaining three-dot menu items — testids added via add-data-testid for
    # ELITEA-1946/1959 (EliteaAI/EliteaUI, ToolkitsControls.jsx): DotMenu.jsx
    # wires `testId: item.key`, so Export rendered NO testid at all (its hook
    # supplies no key) and Copy link rendered the label-derived
    # `Copy link-menuitem` (space included). Both are now named at the
    # ToolkitsControls call site, the same shape SkillControls.jsx /
    # CredentialsControls.jsx already use for their pin item.
    export_menuitem = LocatorDescriptor(
        testid="toolkit-actions-export-menuitem",
        description="'Export' menu item inside the three-dot menu — permanently "
        "disabled on this surface (aria-disabled=\"true\"); MUI renders disabled "
        "MenuItems as <li aria-disabled>, which is_enabled() does NOT read as "
        "disabled — assert the attribute",
    )
    fork_menuitem = LocatorDescriptor(
        testid="toolkit-actions-fork-menuitem",
        description="'Fork' menu item inside the three-dot menu — disabled on "
        "this surface (ToolkitsControls passes disabled: true); read "
        "aria-disabled, not is_enabled()",
    )
    copy_link_menuitem = LocatorDescriptor(
        testid="copy-link-toolkit-menuitem",
        description="'Copy link' menu item inside the three-dot menu — copies the "
        "MCP's project-scoped deep link and raises the "
        "'The link has been copied to the clipboard.' toast",
    )
    pin_toggle_menuitem = LocatorDescriptor(
        testid="pin-toggle-toolkit-menuitem",
        description="Pin toggle menu item inside the three-dot menu — STABLE "
        "identity; its pinned state is read from the LABEL ('Pin to top' / "
        "'Unpin from top'), never from a state-flavoured testid "
        "(.agents/testing.md § Locator policy)",
    )
    # Neutrally-named handle for the shared Toast.jsx node. The pre-existing
    # `sync_error_toast_message` field below points at the SAME
    # `toast-message` testid but is named for ELITEA-1934's Load-Tools error
    # toast; it is left byte-identical for its existing callers (additive-only
    # rule) and this alias is used wherever the toast is a success message.
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Shared Toast.jsx message node — auto-dismisses within a few "
        "seconds, so wait for it in the SAME synchronous chain as the click "
        "that raises it",
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

    # Secret-vault dropdown options (ELITEA-1932). Dynamic testid -> class-level
    # template constant per .agents/testing.md § Locator policy; the option's
    # testid embeds the stored reference itself, e.g.
    # select-option-{{secret.auth_token}}.
    SECRET_SAVED_OPTION = '[data-testid="select-option-{{{{secret.{}}}}}"]'
    SECRET_SAVED_OPTION_PREFIX = '[data-testid^="select-option-{{secret."]'
    SECRET_GROUP_HEADER_SAVED = '[data-testid="select-group-header-Saved Secrets"]'

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
        "clarification filed as issue #595, see ELITEA-1933 AFS). Only present "
        "AFTER a tool has been chosen; before that the panel does not mount at "
        "all — see :attr:`empty_state_tool_select` (EliteaUI EL-5947).",
    )

    # EL-5947 gated the Test Settings panel behind tool selection:
    #   TestTools.jsx →  if (!selectedTool) return <TestToolsEmptyState/>
    #                    return <TestToolSettings/>       # 'Tool' select lives here
    # So a freshly-opened toolkit/MCP detail page shows the EMPTY STATE, and this
    # select is the only route from it to the panel. Same testid the artifact-
    # toolkit page object uses (toolkit_test_settings_page.py) — one shared
    # TestToolsEmptyState component serves both surfaces.
    empty_state_tool_select = LocatorDescriptor(
        testid="toolkit-test-empty-tool-select",
        description="'Select Tool' PopoverSelect on TestToolsEmptyState — shown "
        "INSTEAD of the Test Settings panel until a tool is chosen (EL-5947)",
    )

    # ------------------------------------------------------------------
    # Detail action bar (/mcps/all/{id} header row) — added ELITEA-1940.
    # EL-6277 (EliteaAI/EliteaUI@cb030b7d) moved the Test surface out of the
    # detail page into its own route and relocated the "view run history"
    # control here, so both entry points now live in this one action bar
    # (`ToolkitForm.jsx:525` renders it when `isDetailsActionBar`).
    # ------------------------------------------------------------------
    action_bar = LocatorDescriptor(
        testid="toolkit-action-bar",
        description="Detail-page action bar container (ToolkitForm.jsx:525) — "
        "hosts the Test button, the Run History button and the Form/Raw Json "
        "view toggle. Mounts ASYNCHRONOUSLY after a client-side navigation "
        "back to the detail page (test-specs/mcp/_surface.md § Sequencing "
        "gotchas), so callers must wait on it rather than query immediately.",
    )
    test_button = LocatorDescriptor(
        testid="toolkit-test-button",
        description="'Test' button in the detail action bar (aria-label "
        "'Test MCP') — navigates to the /mcps/all/{id}/test route (EL-6277). "
        "DISABLED while the form is dirty (`isTestDisabled={dirty}`), so a "
        "flow that clicked Load Tools must Save first and wait for this "
        "button to re-enable.",
    )
    run_history_button = LocatorDescriptor(
        testid="pipeline-history-tab",
        description="'Run History' button in the detail action bar "
        "(ViewRunHistoryButton.jsx, aria-label 'view run history') — "
        "navigates to /toolkits/all/{id}/history?isMCP=true. The "
        "`pipeline-` prefix is the shared component's DEFAULT testid "
        "(ViewRunHistoryButton.jsx:16), correct on this surface too and "
        "already relied on by PipelineDetailPage — do not rename "
        "(test-specs/mcp/_surface.md § Run History, clarification #1727).",
    )

    # ------------------------------------------------------------------
    # Connection-status indicator + sync-error toast — added ELITEA-1934.
    # ------------------------------------------------------------------
    connection_status = LocatorDescriptor(
        testid="toolkit-connection-status",
        description="Connection status indicator ('Not Connected'/'Connected!') "
        "next to the Login/Logout button (McpAuthStatus.jsx) — added via "
        "add-data-testid for ELITEA-1934 (the Typography had no testid before; "
        "text itself is the observable, not a state attribute, per "
        ".agents/testing.md § Locator policy — one stable testid, the rendered "
        "text is what the case asserts)",
    )
    connection_status_icon = LocatorDescriptor(
        testid="toolkit-connection-status-icon",
        description="State icon (OnlineIcon svg) rendered next to the "
        "connection-status text inside McpAuthStatus.jsx's status container — "
        "added via add-data-testid for ELITEA-1936 (EliteaAI/EliteaUI@55dc4f66, "
        "on automation/testids, human cherry-pick to main pending). The svg had "
        "no testid, and chaining a raw `svg` selector off connection_status is "
        "forbidden by .agents/testing.md § Locator policy.",
    )

    login_button = LocatorDescriptor(
        testid="toolkit-connection-login-button",
        description="Login/Logout button next to the connection-status indicator "
        "(McpAuthStatus.jsx) — added via add-data-testid for ELITEA-2085. ONE stable "
        "testid regardless of Login/Logout state (label/onClick toggle with "
        "hasLoggedInToMcp, testid stays fixed per .agents/testing.md § Locator policy).",
    )
    sync_error_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide Toast component's message container (ToastProvider.jsx "
        "-> Toast.jsx, confirmed live to be the SAME shared component as "
        "SkillDetailPage.version_toast_message / ArtifactsPage.success_toast_message "
        "— reused here for the 'Failed to sync MCP tools: ...' error toast the "
        "mcp_sync_tools failure fires, ELITEA-1934). No new testid needed.",
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

    # Key under which the product stores its own per-server MCP connection
    # record in sessionStorage (McpAuthHelpers / useMcpTokenChange). Read-only
    # observation handle for ELITEA-1936 step 7 — NOT a locator and NOT a
    # substitution: the test never writes it, it only reads what the product
    # wrote after a real connection round-trip.
    MCP_TOKENS_SESSION_STORAGE_KEY = "elitea_mcp_tokens_v1"

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to MCP type picker")
    def navigate_to_create(self) -> None:
        """Navigate to ``/mcps/create`` and wait for the type-picker to load.

        The "Choose the MCP type" copy now carries
        :attr:`type_picker_heading` (``mcp-type-picker-heading``, added for
        ELITEA-1949). The load wait still keys off the testid-bearing
        :attr:`remote_mcp_type_card`, which mounts LAST (up to ~3.5s after the
        navigation) and is therefore the stronger readiness signal.
        """
        self.navigate("/mcps/create")
        self.remote_mcp_type_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Select Remote MCP type")
    def select_remote_mcp_type(self) -> None:
        """Click the Remote MCP type card and wait for the create form to load."""
        self.remote_mcp_type_card.click()
        self.page.wait_for_url("**/mcps/create/mcp", timeout=UI_ELEMENT_TIMEOUT)
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Select Remote category tab")
    def select_remote_category_tab(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the 'Remote' category filter tab (in-chat MCP canvas, ELITEA-2085).

        Two ``category-filter-tab`` instances render side by side
        ("Local"/"Remote") — disambiguated by exact text match, same
        idiom already used for ``ChatPage``'s dynamic-suffix testids.
        Does NOT call :meth:`select_remote_mcp_type` afterward — that
        method's own ``wait_for_url`` assumes the standalone
        ``/mcps/create`` page navigation, which never happens inside the
        embedded chat canvas.
        """
        tab = self.category_filter_tab.filter(has_text=re.compile("^Remote$"))
        tab.wait_for(state="visible", timeout=timeout)
        tab.click()

    def type_filter_chip(self, chip_slug: str):
        """Return the ``/mcps/create`` type-filter chip locator for *chip_slug*.

        *chip_slug* is the slugified category label the product itself emits
        (``local`` / ``remote``). Mirrors ``McpListPage.type_filter_chip()``
        (ELITEA-1942) in shape; the pattern lives at class level so the testid
        inventory stays greppable (``.agents/testing.md`` § Locator policy —
        dynamic testids).
        """
        return self.page.locator(self.TYPE_FILTER_CHIP.format(chip_slug))

    def selected_type_filter_chip(self, chip_slug: str):
        """Return the *selected-state* locator for a type-filter chip.

        Selection is asserted via the chip's own ``data-selected`` attribute,
        never via its emotion CSS class hash or computed background colour.
        """
        return self.page.locator(self.TYPE_FILTER_CHIP_SELECTED.format(chip_slug))

    @action("Click an MCP type filter chip")
    def click_type_filter(self, chip_slug: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the ``local``/``remote`` type-filter chip on ``/mcps/create``.

        Filtering here is pure client-side re-grouping — there is NO network
        request to wait on (unlike the dashboard type filter, ELITEA-1942), so
        callers wait on the DOM outcome themselves.
        """
        chip = self.type_filter_chip(chip_slug)
        chip.wait_for(state="visible", timeout=timeout)
        chip.click()

    def is_type_filter_selected(self, chip_slug: str) -> bool:
        """Return whether the given type-filter chip is currently selected."""
        return self.type_filter_chip(chip_slug).get_attribute("data-selected") == "true"

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

        The detail title (``toolkit-detail-title``) shows a static
        entity-specific placeholder ("Edit Toolkit" on /toolkits, "Edit MCP"
        on /mcps — see :data:`DETAIL_TITLE_PLACEHOLDERS`) until the
        tool-detail GET response is applied to component state. The response
        resolving doesn't guarantee the title has re-rendered yet (one more
        React tick), so poll the title text itself rather than trusting the
        network wait alone.
        """
        self.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.page.wait_for_function(
            """({selector, placeholders}) => {
                const el = document.querySelector(selector);
                if (!el) return false;
                const text = el.textContent.trim();
                return text !== '' && !placeholders.includes(text);
            }""",
            arg={
                "selector": self.DETAIL_TITLE_SELECTOR,
                "placeholders": list(DETAIL_TITLE_PLACEHOLDERS),
            },
            timeout=UI_ELEMENT_TIMEOUT,
        )

    # ------------------------------------------------------------------
    # Breadcrumb navigation (detail page) — added ELITEA-1961.
    # ------------------------------------------------------------------

    def get_breadcrumb_text(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the breadcrumb trail's full text, e.g. ``MCPs/<toolkit name>``.

        MUI renders the separator as its own node, so ``text_content()``
        concatenates the crumbs into ``MCPs/<name>`` with no separating
        whitespace.
        """
        self.breadcrumbs_nav.wait_for(state="visible", timeout=timeout)
        return (self.breadcrumbs_nav.text_content() or "").strip()

    @action("Click the parent breadcrumb link")
    def click_breadcrumb_parent(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the parent crumb ("MCPs") and wait for the list route.

        This is the product's own in-page navigation control — deliberately
        NOT ``page.go_back()``, which is a different flow with a different
        contract (ELITEA-1961 AFS § Automation Hints). The navigation is
        client-side, so no reload is awaited; callers that need to prove that
        should watch for the absence of a ``load`` event.
        """
        self.breadcrumb_parent_link.first.wait_for(state="visible", timeout=timeout)
        self.breadcrumb_parent_link.first.click()
        self.page.wait_for_url("**/mcps/all", timeout=timeout)
        self.wait_for_network()

    # ------------------------------------------------------------------
    # Detail action-bar navigation — added ELITEA-1940.
    # ------------------------------------------------------------------

    @action("Open the Test route from the detail action bar")
    def open_test_route(self, toolkit_id: int, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the action bar's **Test** button and wait for the Test route.

        EL-6277 made the Test surface its own route
        (``/mcps/all/{id}/test``) instead of a right-hand region of the
        detail page. The button is ``disabled`` while the form is dirty
        (``ToolkitForm.jsx``: ``isTestDisabled={dirty}``) — clicking Load
        Tools dirties it — so this waits for the button to be ENABLED
        before clicking rather than clicking into a dead element and
        timing out later on a panel that never mounted.

        Args:
            toolkit_id: The MCP's numeric id, used to match the target URL.
            timeout: Maximum wait time in milliseconds.
        """
        self.test_button.wait_for(state="visible", timeout=timeout)
        expect(self.test_button).to_be_enabled(timeout=timeout)
        self.test_button.click()
        self.page.wait_for_url(re.compile(rf"/mcps/all/{toolkit_id}/test"), timeout=timeout)
        logger.info("Opened the Test route for MCP id=%s", toolkit_id)

    def is_test_button_disabled(self, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Return whether the action bar's Test button is currently disabled.

        Args:
            timeout: Maximum wait time in milliseconds for the button to render.

        Returns:
            True while the detail form is dirty (``isTestDisabled={dirty}``).
        """
        self.test_button.wait_for(state="visible", timeout=timeout)
        return self.test_button.is_disabled()

    @action("Open Run History from the detail action bar")
    def open_run_history(self, toolkit_id: int, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click **Run History** and wait for the run-history route to load.

        MCPs deliberately reuse the toolkit route with an ``isMCP`` query
        flag (``useToolkitDetailNavigation.hooks.js``), so the destination
        is ``/toolkits/all/{id}/history?isMCP=true`` — a full page, not a
        drawer (clarification #1727).

        The action bar mounts asynchronously after a client-side
        navigation back to the detail page (test-specs/mcp/_surface.md
        § Sequencing gotchas — an immediate click raised "does not match
        any elements" live), hence the explicit visibility wait.

        Args:
            toolkit_id: The MCP's numeric id, used to match the target URL.
            timeout: Maximum wait time in milliseconds.
        """
        self.run_history_button.wait_for(state="visible", timeout=timeout)
        self.run_history_button.click()
        self.page.wait_for_url(
            re.compile(rf"/toolkits/all/{toolkit_id}/history"), timeout=timeout
        )
        logger.info("Opened Run History for MCP id=%s", toolkit_id)

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

    def wait_for_controls_menu_closed(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the three-dot menu popup to leave the DOM.

        ``DotMenu`` unmounts the popup rather than hiding it, but the unmount
        runs behind MUI's close TRANSITION — an assertion fired in the same
        tick as the click that closed it still sees ``count() == 1``
        (observed live, ELITEA-1959 implementation). This is a framework
        condition wait, not a sleep.
        """
        self.controls_menu.wait_for(state="detached", timeout=timeout)

    @action("Close the three-dot actions menu with Escape")
    def close_controls_menu_with_escape(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Press Escape and wait for the menu popup to UNMOUNT.

        ``DotMenu`` removes the popup from the DOM rather than hiding it, so
        the wait (and any caller assertion) must be on ``detached`` /
        ``count() == 0``, not on ``not_to_be_visible()``.
        """
        self.page.keyboard.press("Escape")
        self.wait_for_controls_menu_closed(timeout=timeout)

    @action("Click the Copy link menu item")
    def click_copy_link_menu_item(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Click 'Copy link' and return the confirmation toast's text.

        The toast auto-dismisses within a few seconds, so the wait happens in
        the same synchronous chain as the click (same shape as
        :meth:`wait_for_sync_error_toast`). Clicking the item also closes the
        menu — ``DotMenu.jsx``'s ``withClose`` fires on every item click.
        """
        self.copy_link_menuitem.click()
        self.toast_message.wait_for(state="visible", timeout=timeout)
        return self.toast_message.text_content() or ""

    def get_pin_toggle_menu_label(self) -> str:
        """Return the pin-toggle menu item's current text ('Pin to top' / 'Unpin from top')."""
        return self.pin_toggle_menuitem.text_content() or ""

    @action("Click the Pin/Unpin menu item")
    def click_pin_toggle_menu_item(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the pin-toggle menu item and wait for the pin API round trip.

        Mirrors ``CredentialDetailPage.click_pin_toggle_menu_item()`` verbatim
        (the two surfaces share the widget) — waits on the real
        ``POST``/``DELETE .../social/pin/prompt_lib/{project}/toolkit/{id}``
        response instead of a fixed sleep.

        Returns:
            The matched Playwright ``Response`` (201 on pin, 204 on unpin).
        """
        toolkit_id = self.get_toolkit_id_from_url()
        pattern = "/social/pin/prompt_lib/"
        with self.page.expect_response(
            lambda r: pattern in r.url and r.url.rstrip("/").endswith(f"/toolkit/{toolkit_id}"),
            timeout=timeout,
        ) as response_info:
            self.pin_toggle_menuitem.click()
        return response_info.value

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
        # Resolve the element handle BEFORE the click: the moment a selection
        # lands, CodeMirror's selectionMatch extension decorates every OTHER
        # occurrence of the selected text with `cm-selectionMatch` <span>s, so
        # re-resolving the same get_by_text() locator afterwards raises a
        # strict-mode violation (confirmed live at ELITEA-1935 implementation on
        # a document that also carries `available_mcp_tools`, where a tool name
        # appears both in `selected_tools` and as a `"value"` entry). The handle
        # captured here still points at the original `.cm-line` div.
        line_handle = self.raw_json_editor_content.get_by_text(
            current_line_text, exact=True
        ).element_handle()
        line_handle.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self._wait_for_line_selection_applied_handle(line_handle)
        self.page.keyboard.type(new_line_text)
        self._wait_for_text_content_stable(self.raw_json_editor_content)

    @action("Delete a single line from the Raw Json editor")
    def delete_raw_json_line(self, current_line_text: str) -> None:
        """Delete the content of one line of the Raw Json CodeMirror editor.

        DECLARED IMPROVISATION — inherits :meth:`fill_raw_json_line`'s
        lead-approved #579 exception verbatim: the Raw Json editor's per-line
        ``<div>`` nodes are CodeMirror-internal render nodes, not app JSX, so
        no testid can be placed on them (analogous to the third-party-widget
        Stop+flag exception, e.g. ReactFlow's ``rf__wrapper``, per
        ``.agents/testing.md`` § Locator policy). ``get_by_text()`` scoped
        inside the testid-anchored ``raw_json_editor_content`` parent (itself a
        ``LocatorDescriptor(testid=...)`` field) is the sanctioned pattern for
        this specific canon-gap; do not extend it to any handle that COULD
        carry a testid.

        Additive sibling of :meth:`fill_raw_json_line` rather than a new mode
        of it (additive-only shared-caller rule — ``fill_raw_json_line`` has
        merged callers): same select-then-act discipline, ending in a
        ``Backspace`` instead of a ``type``. ``keyboard.type("")`` is a no-op,
        so the existing method cannot express a deletion.

        CodeMirror's ``Home`` is *smart-home* — it moves to the first
        non-whitespace character — so this clears the line's CONTENT and leaves
        its leading indentation behind. That whitespace-only line is still
        valid JSON and the server normalises it away on save (confirmed live,
        ELITEA-1935 analysis).

        Args:
            current_line_text: Exact current text of the target line (used to
                locate the line's div via ``get_by_text(..., exact=True)``
                scoped inside the editor).
        """
        # Handle resolved before the click for the same selectionMatch reason
        # documented in :meth:`fill_raw_json_line`.
        line_handle = self.raw_json_editor_content.get_by_text(
            current_line_text, exact=True
        ).element_handle()
        line_handle.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self._wait_for_line_selection_applied_handle(line_handle)
        self.page.keyboard.press("Backspace")
        self._wait_for_text_content_stable(self.raw_json_editor_content)

    def scroll_raw_json_to_top(self) -> None:
        """Scroll the Raw Json editor's scrollable ancestor back to the top.

        :meth:`get_raw_json_full` defeats CodeMirror virtualization by scrolling
        the editor's scrollable ancestor to the BOTTOM and leaves it there. Any
        per-line edit afterwards (:meth:`fill_raw_json_line` /
        :meth:`delete_raw_json_line`) then fails with ``Locator.click: Timeout``,
        because the target line has been virtualized out of the DOM (confirmed
        live, ELITEA-1935 analysis — one of the three documented traps in
        ``test-specs/mcp/_surface.md``). Call this between a full read and a
        subsequent per-line edit.

        Reuses :meth:`get_raw_json_full`'s scrollable-ancestor walk (first
        ancestor with real overflow) rather than a MUI ``css-*`` class name,
        which is not a stable selector. The selector fed to ``querySelector``
        is the class-level :attr:`RAW_JSON_EDITOR_SELECTOR` testid constant.
        """
        self.page.evaluate(
            """(selector) => {
                const el = document.querySelector(selector);
                let node = el;
                while (node && node !== document.body) {
                    const cs = getComputedStyle(node);
                    if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll')
                            && node.scrollHeight > node.clientHeight) {
                        node.scrollTop = 0;
                        return true;
                    }
                    node = node.parentElement;
                }
                return false;
            }""",
            self.RAW_JSON_EDITOR_SELECTOR,
        )

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
        self._wait_for_line_selection_applied_handle(
            line_locator.element_handle(), timeout_ms=timeout_ms
        )

    def _wait_for_line_selection_applied_handle(self, line_handle, timeout_ms: int = UI_ELEMENT_TIMEOUT) -> None:
        """Handle-based variant of :meth:`_wait_for_line_selection_applied`.

        Takes an already-resolved ``ElementHandle`` instead of a locator, so the
        caller can capture the target line BEFORE the click that triggers
        CodeMirror's ambiguity-creating selectionMatch decorations (see
        :meth:`fill_raw_json_line`).
        """
        self.page.wait_for_function(
            """(el) => {
                const trimmedLen = el.textContent.trim().length;
                const sel = window.getSelection();
                return trimmedLen === 0 || (sel && sel.toString().length === trimmedLen);
            }""",
            arg=line_handle,
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

    @action("Switch the Client Secret field to Secret mode")
    def switch_client_secret_to_secret_mode(self) -> None:
        """Click the Client Secret toggler's "Secret" button and wait for the swap.

        Secret mode replaces the native ``<input type="password">`` with the
        vault ``SingleSelect`` (``SecretField.jsx``), so the wait is on the
        combobox mounting — not on the button's own ``aria-pressed``, which
        flips before the field re-renders.
        """
        self.client_secret_toggle_secret.click()
        self.client_secret_combobox.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def saved_secret_option(self, secret_name: str):
        """Return the vault-dropdown option locator for saved secret *secret_name*."""
        return self.page.locator(self.SECRET_SAVED_OPTION.format(secret_name))

    def saved_secret_options(self):
        """Return every SAVED-SECRETS option currently rendered in the dropdown."""
        return self.page.locator(self.SECRET_SAVED_OPTION_PREFIX)

    def saved_secrets_group_header(self):
        """Return the dropdown's "SAVED SECRETS" group header."""
        return self.page.locator(self.SECRET_GROUP_HEADER_SAVED)

    @action("Open the Client Secret vault dropdown")
    def open_client_secret_vault_dropdown(self) -> None:
        """Open the Secret-mode vault dropdown and wait for its first saved option.

        The vault query (``useSecretsListQuery``) is skipped while the field is
        in Password mode, so the options only start loading once Secret mode is
        active and the select is opened — wait on a rendered OPTION, not on
        network idle (same discipline as
        ``CredentialCreatePage.open_secret_dropdown``).
        """
        self.client_secret_combobox.click()
        self.saved_secret_options().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Select a saved secret in the Client Secret vault dropdown")
    def select_client_secret_saved_secret(self, secret_name: str) -> None:
        """Pick saved secret *secret_name* and wait for the dropdown to close."""
        option = self.saved_secret_option(secret_name)
        option.click()
        option.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)

    def get_client_secret_display_text(self) -> str:
        """Return the Secret-mode combobox's displayed secret NAME.

        The combobox shows the human-readable secret name (``auth_token``); the
        stored reference (``{{secret.auth_token}}``) is only visible in the Raw
        Json view / the save response.
        """
        return self.client_secret_combobox.text_content() or ""

    @action("Blur the Headers JSON editor")
    def blur_headers_editor(self) -> None:
        """Move focus out of the Headers editor so its value commits to the form.

        The CodeMirror-backed Headers field propagates on **blur**, not on
        keystroke: with focus still inside the editor after typing valid JSON,
        ``toolkit-detail-save-button`` stays disabled (verified live at
        ELITEA-1931). Blurring also re-formats the JSON to its pretty-printed
        form, which is why this is a separate, additive method rather than a
        change to :meth:`fill_headers_json` — that method's merged caller
        (``test_mcp_create_remote.py``) reads the editor text immediately after
        filling and must keep seeing the verbatim, unformatted input.
        """
        self.headers_editor_content.blur()
        self._wait_for_text_content_stable(self.headers_editor_content)

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

    @action("Expand the detail page's configuration section")
    def expand_configuration_section(self) -> None:
        """Expand the detail page's collapsed schema-driven configuration fields.

        No-op when the section is already expanded (the "show more" control
        unmounts once clicked), so this is safe to call unconditionally.

        Needed because the detail page renders NO ``toolkit-field-*`` element
        until the section is expanded — the create form renders them inline,
        the detail page does not (found at ELITEA-1923/1924).
        """
        # "Already expanded?" is decided on the FIELDS, never on the toggle:
        # `toolkit-configuration-show-more` mounts asynchronously and is
        # measurably absent for ~1s after a detail-page load even once
        # `toolkit-detail-title` has resolved to the real name (polled live at
        # ELITEA-1930, 10x500ms). A non-waiting `count() == 0` read on the
        # toggle therefore silently no-op'd, and every following
        # `toolkit-field-*` read then timed out with a misleading
        # "element not found". Keying off `url_input` is exact in both
        # directions: it is already present on the create form and on an
        # already-expanded section (return immediately, no cost), and absent
        # exactly when the section still needs expanding.
        if self.url_input.count() > 0:
            return
        self.configuration_show_more.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.configuration_show_more.click()
        self.url_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    @action("Click Discard and wait for the confirmation modal")
    def click_discard(self) -> None:
        """Click the detail page's Discard button and wait for its confirm modal.

        Discard is a two-step gesture: the first click only opens a
        ``Warning / Are you sure you want to discard changes?`` modal — the form
        still holds the edited values and both action buttons stay enabled until
        :meth:`confirm_discard` is called (verified live at ELITEA-1928). Same
        shape as ``CredentialDetailPage.click_discard``.
        """
        self.detail_discard_button.click()
        self.discard_confirm_modal.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_discard_confirm_message(self) -> str:
        """Return the discard-confirm modal's text.

        The testid sits on the MUI ``Dialog`` root, so this includes the
        "Warning" title and the "Cancel"/"Discard" button labels — assert with
        ``in``, not ``==``.
        """
        return self.discard_confirm_modal.text_content() or ""

    @action("Confirm Discard in the confirmation modal")
    def confirm_discard(self) -> None:
        """Confirm the discard and wait for the modal to unmount.

        The modal is removed from the DOM (not hidden) when it closes, so the
        wait is on ``detached`` — same as ``credential-discard-confirm-modal``.
        """
        self.discard_confirm_button.click()
        self.discard_confirm_modal.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)

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
    def select_test_tool(self, tool_name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Select *tool_name*, from whichever Tool select is currently rendered.

        This is the affordance that actually renders the tool's parameter schema
        as live input fields — NOT the Tools-section pill click (AFS step 9 /
        issue #595 case-text clarification).

        EL-5947 made the surface two-state: before any tool is chosen the panel
        does not mount and only :attr:`empty_state_tool_select` exists; once one
        is chosen the panel's own :attr:`test_tool_select` takes over. Both open
        the same option list, so this dispatches on whichever is present rather
        than assuming the panel — clicking the panel select on a fresh page
        waits out its timeout on an element that cannot appear yet.
        """
        try:
            self.test_tool_select.wait_for(state="visible", timeout=2000)
            trigger = self.test_tool_select
        except Exception:
            logger.info(
                "Test Settings panel not mounted yet (EL-5947 empty state) — "
                "selecting %r via the empty-state Tool select",
                tool_name,
            )
            self.empty_state_tool_select.wait_for(state="visible", timeout=timeout)
            trigger = self.empty_state_tool_select

        trigger.click()
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
    # Connection-status indicator + sync-error toast — added ELITEA-1934.
    # ------------------------------------------------------------------

    def get_connection_status_text(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the connection-status indicator's current text ('Not Connected'/'Connected!')."""
        self.connection_status.wait_for(state="visible", timeout=timeout)
        return self.connection_status.text_content() or ""

    @action("Click the connection Login button")
    def click_connection_login(self) -> None:
        """Click the connection-status Login button and wait for the flow to settle.

        For a Remote MCP whose server needs no OAuth (the DeepWiki fixture),
        ``onLogin`` -> ``useMcpAuthCheck.runAuthCheck`` emits an in-page socket
        ``test_mcp_connection`` event — a protocol-level ``tools/list``
        round-trip. There is NO external window, NO redirect and NO credential
        prompt; only a server that genuinely demands OAuth opens
        ``McpAuthModal`` (McpAuthStatus.jsx, confirmed live ELITEA-1936).

        Waits only for the button to leave its in-flight state (label back off
        ``Logging in...``). The transient label itself is deliberately NOT
        asserted anywhere — the DeepWiki round-trip completed faster than a
        500 ms poll during analysis, so asserting it would be a guaranteed
        flake.
        """
        self.login_button.click()
        expect(self.login_button).not_to_have_text(
            "Logging in...", timeout=SAVE_RESPONSE_TIMEOUT
        )

    def get_mcp_connection_record(self, server_url: str) -> dict | None:
        """Return the product's own sessionStorage connection record for *server_url*.

        READ-ONLY OBSERVATION, not a substitution: this reads state the PRODUCT
        wrote (``McpAuthHelpers.setConnectionVerified(url)`` after a successful
        socket round-trip). Nothing is injected, stubbed or forced — the
        ``.evaluate()`` call performs a ``sessionStorage.getItem`` and a
        ``JSON.parse``, and the case's own observable (the status text) is
        asserted independently in the DOM. Provenance discipline per
        ``.agents/testing.md`` § Fidelity policy.

        The record is keyed by SERVER URL (not by toolkit id), so it is shared
        by every toolkit pointing at the same MCP server within one browser
        context.

        Args:
            server_url: The MCP server URL the toolkit points at.

        Returns:
            The per-server record dict (``access_token`` / ``connection_verified``
            / ``issued_at`` / ``expires_at``), or ``None`` when the product has
            written no record for that URL.
        """
        raw = self.page.evaluate(
            "(key) => window.sessionStorage.getItem(key)",
            self.MCP_TOKENS_SESSION_STORAGE_KEY,
        )
        if not raw:
            return None
        return json.loads(raw).get(server_url)

    @action("Wait for the Load-Tools sync-error toast and return its text")
    def wait_for_sync_error_toast(self, timeout: int = 5000) -> str:
        """Wait for the sync-error toast to appear and return its text.

        Must be called IMMEDIATELY after :meth:`click_load_tools` resolves, in
        the same synchronous chain — the toast auto-dismisses within a few
        seconds (confirmed live, AFS ELITEA-1934 step 7), so inserting a
        separate step in between risks missing it entirely.
        """
        self.sync_error_toast_message.wait_for(state="visible", timeout=timeout)
        text = self.sync_error_toast_message.text_content() or ""
        logger.info("Sync-error toast text: %r", text)
        return text
