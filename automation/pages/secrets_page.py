"""Secrets page object (Settings → Secrets).

URL: /settings/secrets

Covers the page layout (header title, add-button) and the secrets table
(``SecretsTable.jsx``, built on the shared ``grid-table`` components) —
inline row-based create flow (the "+" button inserts an editable row directly
into the table, not a modal/dialog) plus the existing rows' name/value cells.

Locator provenance (ELITEA-2336): all 9 core testids
(``secrets-page-title`` / ``secrets-add-button`` / ``secret-row`` /
``secret-name-input`` / ``secret-value-input`` / ``secret-row-save-button`` /
``secret-row-cancel-button`` / ``secret-name-cell`` / ``secret-value-cell``)
existed only as UNCOMMITTED edits in the EliteaUI working tree at analysis
time (the AFS's "pre-existing" claim was drift — see this case's Run Report);
committed onto ``automation/testids`` as part of this implementation
(``EliteaAI/EliteaUI@c2a5b4c7``). ``secrets-page-title`` / ``secrets-add-button``
wire ``DrawerPageHeader``'s existing ``titleTestId`` / ``slotProps.addButton.testId``
props (same mechanism as ``PersonalTokensPage``). ``secret-name-input`` /
``secret-value-input`` are ``data-testid`` set via ``EditSecretInputGridTable``'s
``inputProps`` object (native ``<input>`` attribute). ``secret-row`` wires
``GridTableRow``'s existing ``data-testid`` prop (same pattern as
``PersonalTokensPage.token_row``). ``secret-row-save-button`` /
``secret-row-cancel-button`` are static ``data-testid``s on the two
``IconButton``s rendered only while a row is in edit mode. ``secret-name-cell``
/ ``secret-value-cell`` are static ``data-testid``s on the view-mode
``Text.EllipsisTypography`` elements.

One NEW testid added by this case (``secrets-pagination-info``, EliteaAI/EliteaUI@c2a5b4c7):
the shared ``GridTablePagination`` component (``src/[fsd]/entities/grid-table/ui/``)
had no testid on its "N - M of T" range Typography anywhere in the app — needed
to assert the AFS's pagination-reset-to-page-1 clarification (case step 3). Added
as an optional ``pageInfoTestId`` caller-supplied prop (same shape as the
component's existing ``nextButtonTestId``), wired at this feature's call site
in ``SecretsTable.jsx`` as ``secrets-pagination-info`` — per
``.agents/testing.md`` "shared components never hardcode feature-scoped
testids".

Locator provenance (ELITEA-2343, eye-icon reveal/mask toggle): the AFS specced
``secret-row-visibility-toggle-button`` as **"testid needed"** —
``SecretsTable.jsx``'s Show/Hide ``IconButton`` (lines 496-509) carried zero
``data-testid`` at analysis time. This implementation session added it,
committed onto ``automation/testids`` as ``EliteaAI/EliteaUI@01de2292`` —
"add data-testid for secret row visibility toggle button".

The icon-state sub-selectors (``VISIBILITY_ICON_VISIBLE_SELECTOR`` /
``VISIBILITY_ICON_HIDDEN_SELECTOR``) originally chained off MUI's own
auto-generated ``data-testid="VisibilityIcon"`` / ``"VisibilityOffIcon"`` on
the icon ``<svg>`` children (a declared improvisation). **Fixed round 2**
(reviewer finding, PR #1224): ``@mui/material``'s ``createSvgIcon.js`` sets
that attribute only ``process.env.NODE_ENV !== 'production'`` — a `vite
build` (every deployed env / promotion gate) strips it to ``undefined``, so
the improvisation was green on localhost and silently unlocatable
everywhere else. Replaced with real, app-authored ``data-testid``s added
directly on the two conditionally-rendered icon components in
``SecretsTable.jsx`` — ``secret-row-visibility-icon-show`` on
``<VisibilityIcon>`` (masked state, click reveals) and
``secret-row-visibility-icon-hide`` on ``<VisibilityOffIcon>`` (revealed
state, click hides), committed onto ``automation/testids`` as
``EliteaAI/EliteaUI@e6260731`` — "add data-testid for secret row
visibility icon show/hide state". This is canon ruling #277's "same-element
conditional pair, both branches referenced" shape: both branches are named
AND both are exercised by this test's own steps (reveal asserts SHOW ->
HIDE; hide asserts HIDE -> SHOW). See
``.agents/memory/qa-engineer/mui_icons_material_auto_testid_on_icon_svg.md``
for the full MUI-internals finding and this case's AFS § Concrete Handles
for the original reasoning.

Locator provenance (ELITEA-2344, hide flow): the AFS specced the hide-
confirmation dialog's body text as **"testid needed"** (``alert-dialog-content``)
on the SHARED, generic ``src/components/AlertDialog.jsx`` component's
``StyledDialogContentText`` — confirmed live and in source to carry zero
``data-testid`` at analysis time (only an ``id="alert-dialog-description"``
ARIA id, not a valid locator basis per this project's testid-only policy).
This implementation session added it directly on the JSX node (same shape as
the pre-existing ``alert-dialog-confirm-button`` a few lines below it),
committed onto ``automation/testids`` as ``EliteaAI/EliteaUI@6a4e4f22`` — "add
data-testid for shared AlertDialog content text". Being generic/shared (not
scoped to secrets — 4+ other call sites confirmed via `git grep`), it becomes
available to every other feature using ``AlertDialog`` the moment it lands.
The confirm button (``alert-dialog-confirm-button``) was already generic and
pre-existing — declared here per the same shared-modal precedent as
``delete_confirm_dialog`` below (each page object that triggers a shared
dialog declares its own ``LocatorDescriptor`` for it).

Locator provenance (ELITEA-2338, delete flow): the AFS correctly specced all
four row-actions testids as **"testid needed"** — ``SecretsTable.jsx``'s
three-dot ``IconButton`` (lines 511-518) and ``SecretActionsMenu.jsx``'s three
``MenuItem``s (lines 34/50/66) carried zero ``data-testid`` at analysis time.
This implementation session added them via ``add-data-testid`` and committed
them onto ``automation/testids`` as ``EliteaAI/EliteaUI@dd47b184`` — "add
data-testid for secret row actions button + menu items (delete flow)" — dated
~2 minutes after this case's AFS commit, i.e. genuinely new work done to
fulfill the AFS's request, not a pre-existing testid the AFS drifted on.
``secret-row-actions-button`` is a static ``data-testid`` on the row's
``IconButton`` wrapping ``DotsMenuIcon`` (``SecretsTable.jsx:512``).
``secret-actions-menu-edit-value`` / ``secret-actions-menu-hide`` /
``secret-actions-menu-delete`` are static ``data-testid``s on
``SecretActionsMenu.jsx``'s three ``MenuItem``s — only one menu instance is
ever open at a time (single ``anchorEl`` state), so no per-row
parameterization is needed. The delete-confirmation dialog reuses the
SHARED ``DeleteEntityModal.jsx`` component, whose testids
(``delete-confirm-dialog`` / ``delete-confirm-name-input`` /
``delete-confirm-button``) already exist app-wide — same repo precedent as
``personal_tokens_page.py``'s own declaration of this shared modal.

Locator provenance (ELITEA-2330/2331/2332/2334/2342, listing layout / sorting /
pagination / search / masked-value format): FOUR new testids, all pure additive
props on pre-existing shared components, committed onto ``automation/testids`` as
``EliteaAI/EliteaUI@249c0186`` — ``secrets-search-input`` (``DrawerPageHeader``'s
already-supported ``slotProps.searchInput.testId``, landing on the native
``<input>`` via ``SimpleSearchBar``'s ``inputProps``) and
``secrets-pagination-prev-button`` / ``-next-button`` / ``-page-size-select``
(``GridTablePagination``'s already-supported ``prevButtonTestId`` /
``nextButtonTestId`` / ``pageSizeSelectTestId``, the same wiring
``artifacts-pagination-*`` and ``notifications-pagination-*`` already use). No DOM
node, hook or state was added and nothing was removed (zero-functional-impact rule).
``secrets-pagination-page-size-select-combobox`` is derived automatically by
``SingleSelect`` from the root testid via ``SelectDisplayProps`` — the root node is
not clickable, the combobox node is. NO new testid was needed for the column
headers (``secret-column-header-{field}``), the sort control
(``secret-sort-icon-name``, both emitted by the shared ``GridTableHeader`` from the
already-wired ``columnTestIdPrefix="secret"``) or the rows-per-page options
(``select-option-{n}``, the shared ``SingleSelectMenuItem``'s pre-existing default).

Locator provenance (ELITEA-2347, edit-value flow / name-field-readonly): zero
new testids needed — every handle this case touches (``secret-actions-menu-
edit-value``, ``secret-value-input``, ``secret-name-input``, ``secret-name-
cell``, ``secret-row-save-button``) already existed on ``automation/testids``
from ELITEA-2336/2338. The Name field's "read-only" behaviour for an
EXISTING row has no element to add a testid to: ``SecretsTable.jsx``'s
``renderNameCell`` guard is literally ``if (isEditing && row.isNew)`` — an
existing row's Name column renders the SAME ``secret-name-cell`` static-text
element it shows in view mode, never a ``secret-name-input``. Confirmed live
this session (AFS § Concrete Handles).
"""

import logging
import re

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.secrets")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substrings shared by the secrets-list fetch (`useSecretsListQuery`) and the
# create mutation (`useSecretAddingMutation`) — both hit
# `/secrets/secrets/default/{project_id}` (GET for list, POST for create).
SECRETS_LIST_URL_SUBSTRING = "/secrets/secrets/default/"
# Delete mutation endpoint — SINGULAR "secret" (not "secrets"), so it never
# collides with SECRETS_LIST_URL_SUBSTRING above:
# `/secrets/secret/default/{project_id}/{name}` (DELETE).
SECRET_DELETE_URL_SUBSTRING = "/secrets/secret/default/"
# Hide mutation endpoint — distinct URL shape from both of the above: no
# singular/plural "secret(s)" segment at all, just `/secrets/hide/...`.
# `/secrets/hide/default/{project_id}/{name}` (POST).
SECRET_HIDE_URL_SUBSTRING = "/secrets/hide/default/"


class SecretsPage(BasePage):
    """Settings → Secrets page (page layout + inline-create table)."""

    page_title = LocatorDescriptor(
        testid="secrets-page-title",
        description='Page header title — exact text "Secrets"',
    )
    add_button = LocatorDescriptor(
        testid="secrets-add-button",
        description='"+" (add) button, top-right of the header — inserts an '
        "inline editable row, NOT a modal/dialog",
    )
    secret_row = LocatorDescriptor(
        testid="secret-row",
        description="Secret table row (repeatable, one per visible row — new "
        "and existing rows share this testid)",
    )
    name_input = LocatorDescriptor(
        testid="secret-name-input",
        description="Name input of the row currently in edit mode (auto-focused "
        "for a new row)",
    )
    value_input = LocatorDescriptor(
        testid="secret-value-input",
        description="Value input of the row currently in edit mode",
    )
    save_button = LocatorDescriptor(
        testid="secret-row-save-button",
        description="Checkmark (✓) icon — persists the row currently in edit mode",
    )
    cancel_button = LocatorDescriptor(
        testid="secret-row-cancel-button",
        description="X (✗) icon — discards the row currently in edit mode, "
        "client-side only",
    )
    pagination_info = LocatorDescriptor(
        testid="secrets-pagination-info",
        description='Pagination range text — "N - M of T"',
    )
    # ---- ELITEA-2330/2332/2334: header search + pagination controls ----
    # All four testids added by this batch (EliteaAI/EliteaUI@249c0186 on
    # `automation/testids`) as pure additive props on pre-existing shared
    # components — `DrawerPageHeader`'s `slotProps.searchInput.testId` and
    # `GridTablePagination`'s `prevButtonTestId` / `nextButtonTestId` /
    # `pageSizeSelectTestId`. No DOM node, hook or state was added.
    search_input = LocatorDescriptor(
        testid="secrets-search-input",
        description="Header search field — the NATIVE <input> (SimpleSearchBar "
        'forwards data-testid through inputProps), placeholder "Search". '
        "Filters client-side per keystroke; no Enter, no submit, no debounce.",
    )
    prev_page_button = LocatorDescriptor(
        testid="secrets-pagination-prev-button",
        description='Pagination "previous page" arrow — disabled on the first page',
    )
    next_page_button = LocatorDescriptor(
        testid="secrets-pagination-next-button",
        description='Pagination "next page" arrow — disabled on the last page',
    )
    page_size_select = LocatorDescriptor(
        testid="secrets-pagination-page-size-select",
        description="Rows-per-page select ROOT (MUI Select). Read its text here; "
        "CLICK page_size_select_combobox instead — the root is not the clickable "
        "node (same split as notification_center_page.py).",
    )
    page_size_select_combobox = LocatorDescriptor(
        testid="secrets-pagination-page-size-select-combobox",
        description="Rows-per-page select's clickable display node — SingleSelect "
        "derives this testid from the root's via SelectDisplayProps.",
    )
    name_cell = LocatorDescriptor(
        testid="secret-name-cell",
        description="Name cell — repeats once per rendered row; use with "
        "expect(...).to_have_text([...]) to assert the whole rendered order.",
    )
    value_cell = LocatorDescriptor(
        testid="secret-value-cell",
        description="Masked-value cell — repeats once per rendered row; renders the "
        'literal reference template "{{secret.<name>}}" until the row-level eye '
        "toggle reveals the plaintext (ELITEA-2343, a different case).",
    )

    name_error = LocatorDescriptor(
        testid="secret-name-error",
        description="Name-field validation error text, visible only while "
        "the currently-editing row's name fails SECRET_NAME_PATTERN",
    )
    visibility_toggle_button = LocatorDescriptor(
        testid="secret-row-visibility-toggle-button",
        description="Show/Hide (eye icon) toggle IconButton on a saved secret "
        "row — reveals the plaintext value (server round-trip) / re-masks it "
        "(client-side only). Matches every visible row's button page-wide; "
        "use get_row_visibility_toggle_button(row) to scope to one row.",
    )
    row_actions_button = LocatorDescriptor(
        testid="secret-row-actions-button",
        description="Three-dot ('more actions') IconButton on a saved secret "
        "row — opens the SecretActionsMenu dropdown (Edit value / Hide / "
        "Delete). Matches every visible row's button page-wide; use "
        "get_row_actions_button(row) to scope to one specific row.",
    )
    actions_menu_edit_value = LocatorDescriptor(
        testid="secret-actions-menu-edit-value",
        description='"Edit value" menu item — SecretActionsMenu, single '
        "shared instance (only one menu ever open at a time).",
    )
    actions_menu_hide = LocatorDescriptor(
        testid="secret-actions-menu-hide",
        description='"Hide" menu item — SecretActionsMenu, renders only '
        "when the row is not a pending/new row.",
    )
    actions_menu_delete = LocatorDescriptor(
        testid="secret-actions-menu-delete",
        description='"Delete" menu item — SecretActionsMenu, opens the '
        "shared delete-confirmation modal on click.",
    )

    # Hide-confirmation dialog (shared AlertDialog.jsx) — testids already
    # exist (ELITEA-2344 added alert_dialog_content; alert_dialog_confirm_button
    # was already generic/pre-existing). Same shared-dialog-declared-per-page-
    # object precedent as delete_confirm_dialog below.
    alert_dialog_content = LocatorDescriptor(
        testid="alert-dialog-content",
        description="Hide-confirmation dialog body text (shared AlertDialog "
        "component, generic — not secrets-specific).",
    )
    alert_dialog_confirm_button = LocatorDescriptor(
        testid="alert-dialog-confirm-button",
        description="Hide-confirmation dialog's confirm button (shared "
        "AlertDialog component, generic — text is 'Hide' for this flow).",
    )

    # Delete-confirmation modal (shared DeleteEntityModal.jsx) — testids
    # already exist app-wide; repo precedent is each page object that
    # triggers this shared modal declares its own LocatorDescriptor for it
    # (e.g. personal_tokens_page.py / mcp_form_page.py / chat_page.py /
    # artifacts_page.py).
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal container (shared DeleteEntityModal).",
    )
    delete_confirm_message = LocatorDescriptor(
        testid="delete-confirm-message",
        description="Delete-confirmation modal body text — exact copy "
        '"Are you sure to delete the <name>? Enter the name to complete '
        'the action."',
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description="Delete dialog's type-to-confirm Name field — empty on "
        "open, requires the exact secret name before the Delete button "
        "enables.",
    )
    delete_confirm_cancel_button = LocatorDescriptor(
        testid="delete-confirm-cancel-button",
        description="Delete dialog's Cancel button — closes without deleting.",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete dialog's confirm button — disabled until the "
        "typed name matches the target secret's name exactly.",
    )

    # Scoped sub-selectors (class-level UPPER_CASE constants, per
    # .agents/testing.md § Locator policy) — chained off an already-testid-scoped
    # row locator (`secret_row.filter(has_text=name)`), same sanctioned pattern
    # as personal_tokens_page.py's TOKEN_NAME_CELL_SELECTOR.
    # Table column headers (ELITEA-1969 step 5). `SecretsTable.jsx` passes
    # `GridTableHeader`'s `columnTestIdPrefix="secret"`, which renders
    # `secret-column-header-{column.field}` — the field ids are `name`,
    # `secretValue` and `actions` (NOT the visible labels "Name" / "Value" /
    # "Actions"). Dynamic testid via a class-level template constant, per
    # .agents/testing.md § Locator policy.
    SECRET_COLUMN_HEADER_SELECTOR = '[data-testid="secret-column-header-{}"]'
    # Prefix form, for the "exactly three columns, no fourth" count assertion.
    SECRET_COLUMN_HEADER_PREFIX_SELECTOR = '[data-testid^="secret-column-header-"]'
    # Sort control, emitted by the shared `GridTableHeader` from the SAME
    # `columnTestIdPrefix="secret"` that produces the column headers, and ONLY
    # for a column whose config sets `sortable: true` — so `name` has one and
    # `secretValue` / `actions` do not (asserted both ways by ELITEA-2331).
    SECRET_SORT_ICON_SELECTOR = '[data-testid="secret-sort-icon-{}"]'
    # Rows-per-page option (ELITEA-2332). Pre-existing GENERIC testid: the shared
    # `SingleSelectMenuItem` defaults to `data-testid={option.testId ??
    # `select-option-${option.value}`}`, and only one select menu is ever mounted
    # at a time on this page (0 such nodes in the DOM when closed, confirmed
    # live), so no scoping is required.
    PAGE_SIZE_OPTION_SELECTOR = '[data-testid="select-option-{}"]'

    SECRET_NAME_CELL_SELECTOR = '[data-testid="secret-name-cell"]'
    SECRET_VALUE_CELL_SELECTOR = '[data-testid="secret-value-cell"]'
    # Used to prove the pending/editing row's inputs render INSIDE the same
    # `secret-row` table-row structure, not a separate modal/dialog (AFS
    # step 3) — chaining a `[data-testid=` selector off an already-scoped
    # row locator, per .agents/testing.md § Locator policy.
    SECRET_NAME_INPUT_SELECTOR = '[data-testid="secret-name-input"]'
    # Used to scope the Value input to ONE specific row — needed for the
    # edit-value flow (ELITEA-2347), where multiple rows could theoretically
    # coexist on the page even though only one is ever actually in edit mode;
    # chaining a `[data-testid=` selector off an already-scoped row locator,
    # same sanctioned pattern as SECRET_NAME_INPUT_SELECTOR above.
    SECRET_VALUE_INPUT_SELECTOR = '[data-testid="secret-value-input"]'
    # Used to scope the row-actions (three-dot) button to ONE specific row —
    # chaining a `[data-testid=` selector off an already-scoped row locator
    # (ELITEA-2338), same sanctioned pattern as the selectors above.
    SECRET_ROW_ACTIONS_BUTTON_SELECTOR = '[data-testid="secret-row-actions-button"]'
    # Prefix selector matching all three actions-menu items (SecretActionsMenu
    # only ever renders ONE instance at a time) — used to assert the dropdown
    # shows exactly three items in DOM order, same pattern as
    # personal_tokens_page.py's TOKEN_ACTION_PREFIX_SELECTOR.
    SECRET_ACTIONS_MENU_ITEM_PREFIX_SELECTOR = '[data-testid^="secret-actions-menu-"]'
    # Scopes the visibility-toggle button to ONE specific row — chaining a
    # `[data-testid=` selector off an already-scoped row locator (ELITEA-2343),
    # same sanctioned pattern as SECRET_ROW_ACTIONS_BUTTON_SELECTOR above.
    SECRET_ROW_VISIBILITY_TOGGLE_BUTTON_SELECTOR = (
        '[data-testid="secret-row-visibility-toggle-button"]'
    )
    # Icon-state sub-selectors, chained off the visibility-toggle button
    # (ELITEA-2343). Real, app-authored `data-testid`s added directly on the
    # two conditionally-rendered icon components in SecretsTable.jsx
    # (canon ruling #277 "same-element conditional pair, both branches
    # referenced" shape — this test asserts both: reveal asserts SHOW ->
    # HIDE, hide asserts HIDE -> SHOW). Fixed round 2 (reviewer finding,
    # PR #1224): the original version of these selectors chained off MUI's
    # own auto-generated `data-testid={ExportName}` on the icon <svg>
    # (`createSvgIcon.js`), which is stripped to `undefined` on
    # `NODE_ENV==='production'` (i.e. every `vite build` / deployed env) —
    # green on localhost only, silently unlocatable everywhere else. See
    # `.agents/memory/qa-engineer/mui_icons_material_auto_testid_on_icon_svg.md`.
    VISIBILITY_ICON_VISIBLE_SELECTOR = '[data-testid="secret-row-visibility-icon-show"]'
    VISIBILITY_ICON_HIDDEN_SELECTOR = '[data-testid="secret-row-visibility-icon-hide"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_secrets_list_response(self, response) -> bool:
        """True for the secrets-list GET (`useSecretsListQuery`)."""
        return (
            SECRETS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def navigate(self) -> None:
        """Navigate to /settings/secrets and wait for the first secret row to
        become visible.

        Waiting on the row (not just DOM visibility of the page shell)
        confirms the populated path was reached, per the AFS's precondition
        proof (step 1) — the project already has 100+ secrets live.
        """
        with self.page.expect_response(
            self._is_secrets_list_response, timeout=NAVIGATION_TIMEOUT
        ):
            super().navigate("/settings/secrets")
        self.secret_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def click_add_button(self) -> None:
        """Click the "+" (add) button and wait for it to become disabled —
        confirmed live: `DrawerPageHeader`'s `addButton.disabled` prop is
        `true` while any row is in edit mode (AFS step 2)."""
        self.add_button.click()
        expect(self.add_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

    def fill_new_row(self, name: str, value: str) -> None:
        """Type *name* and *value* into the currently-editing row's inputs
        (MUI fields need keyboard events for React onChange, per
        .claude/rules/mui-patterns.md)."""
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=20)
        self.value_input.click()
        self.value_input.press_sequentially(value, delay=20)

    def type_name(self, name: str) -> None:
        """Type *name* into the currently-editing row's name input without
        asserting the save button's resulting enabled/disabled state (unlike
        fill_new_row(), which fills both name+value and is meant for the
        happy path — not valid for negative/invalid-name cases where the
        save button is EXPECTED to be disabled)."""
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=20)

    def clear_and_type_name(self, name: str) -> None:
        """Replace the name input's current content with *name*.

        Uses Home + Shift+End to select the full line, then types over the
        selection — Control+a is unreliable here (confirmed live during
        ELITEA-2337 AFS exploration: a Control+a press directly after typing
        left the field showing the old and new text concatenated instead of
        replacing it), same technique and same root cause already documented
        on the sibling Personal Tokens page's own
        clear_and_type_name() (ELITEA-2286).
        """
        self.name_input.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self.name_input.press_sequentially(name, delay=20)

    def click_save_button(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the checkmark (✓) icon; wait for the secret-create POST to
        resolve, then for the add button to re-enable (row exited edit mode).

        Returns the Playwright ``Response`` for the create POST (side-channel
        proof the secret was actually persisted, per AFS step 5).
        """

        def _is_create_response(response) -> bool:
            return (
                SECRETS_LIST_URL_SUBSTRING in response.url
                and response.request.method == "POST"
            )

        with self.page.expect_response(_is_create_response, timeout=timeout) as resp_info:
            self.save_button.click()
        response = resp_info.value
        expect(self.add_button).to_be_enabled(timeout=timeout)
        return response

    def click_cancel_button(self) -> None:
        """Click the X (✗) icon and wait for the add button to re-enable
        (row discarded, exited edit mode)."""
        self.cancel_button.click()
        expect(self.add_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    def get_editing_row_name_input(self):
        """Return the name-input Locator scoped WITHIN the first (page-1-top)
        `secret_row` element — proves the currently-editing row's input
        lives inside the same table-row structure as every other row, not a
        separate modal/dialog (AFS step 3; only one row is ever in edit mode
        at a time, enforced by the add-button-disabled guard)."""
        return self.secret_row.first.locator(self.SECRET_NAME_INPUT_SELECTOR)

    def get_row_by_name(self, name: str):
        """Return the secret row Locator filtered by exact row text match on
        *name* (sanctioned chaining off the already-testid-scoped
        :attr:`secret_row`, same pattern as personal_tokens_page.py's
        ``get_row_by_name``)."""
        return self.secret_row.filter(has_text=name)

    def get_row_name_cell(self, row):
        """Return the name-cell Locator scoped within *row*."""
        return row.locator(self.SECRET_NAME_CELL_SELECTOR)

    def get_row_value_cell(self, row):
        """Return the masked-value-cell Locator scoped within *row*."""
        return row.locator(self.SECRET_VALUE_CELL_SELECTOR)

    def get_row_value_input(self, row):
        """Return the Value input Locator scoped within *row* — the row's
        Value column while it is in edit mode (create-row OR edit-value
        flow, ELITEA-2347 step 4). Scoped chaining off an already-testid-
        scoped row locator, same sanctioned pattern as
        :meth:`get_row_name_input`."""
        return row.locator(self.SECRET_VALUE_INPUT_SELECTOR)

    def get_row_name_input(self, row):
        """Return the Name input Locator scoped within *row* — expected to
        be ABSENT (count 0) when editing an EXISTING row's value (ELITEA-2347
        step 5): ``renderNameCell``'s guard is ``if (isEditing && row.isNew)``,
        so only a brand-new (``isNew``) row ever renders this input; an
        existing row's Name column stays the same static-text cell
        (``secret-name-cell``) shown in view mode."""
        return row.locator(self.SECRET_NAME_INPUT_SELECTOR)

    def column_header(self, field: str):
        """Return the table column-header locator for *field*.

        Args:
            field: the column's ``field`` id as defined in ``SecretsTable.jsx``
                — ``"name"`` | ``"secretValue"`` | ``"actions"``.
        """
        return self.page.locator(self.SECRET_COLUMN_HEADER_SELECTOR.format(field))

    def column_headers(self):
        """Return every rendered column header — used for the bi-directional
        "exactly these columns, no extras" assertion (ELITEA-1969 step 5)."""
        return self.page.locator(self.SECRET_COLUMN_HEADER_PREFIX_SELECTOR)

    def get_pagination_text(self) -> str:
        """Return the pagination range text, e.g. "1 - 10 of 104"."""
        return (self.pagination_info.text_content() or "").strip()

    def reload_and_wait(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Reload the page and wait for the secrets-list GET (server-side
        re-fetch) to resolve, then for the first row to become visible.

        Used to prove server-side non-existence after a cancel (AFS step 9) —
        a DOM-only absence check doesn't rule out a race where the POST fired
        anyway; a fresh server round-trip does.
        """
        with self.page.expect_response(
            self._is_secrets_list_response, timeout=timeout
        ):
            self.page.reload(wait_until="domcontentloaded")
        self.secret_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_row_actions_button(self, row):
        """Return the three-dot ('more actions') button Locator scoped
        within *row* (a Locator returned by :meth:`get_row_by_name`)."""
        return row.locator(self.SECRET_ROW_ACTIONS_BUTTON_SELECTOR)

    def open_row_actions_menu(self, row) -> None:
        """Open *row*'s three-dot (more actions) menu and wait for the
        SecretActionsMenu dropdown, confirmed by the Delete menu item
        becoming visible (AFS step 3).

        DECLARED IMPROVISATION (per .agents/role-overrides.md § Declared-
        improvisation protocol — no sanctioned canon pattern covers this).
        Neither a real Playwright ``.click()`` (incl. ``force=True``) NOR a
        native ``el.click()`` (the standard ``.claude/rules/mui-patterns.md``
        § "MUI Overlay Interception" fallback) reliably opens this specific
        MUI Menu — confirmed live, implementation day, deterministic across
        many trials in this project's actual `pytest.ini`-launched Chromium
        (headed AND headless, before AND after a full EliteaUI dev-server
        restart to rule out stale Vite HMR state): the button visibly
        receives the click (pressed/hover state, `disabled=False`, a React
        fiber with `onClick` wired), zero console/page errors fire, yet the
        Menu never mounts. Only invoking the button's React `onClick` prop
        DIRECTLY (bypassing the DOM click-event pipeline entirely, via
        `element.__reactProps$*`) reliably opens it — same technique
        succeeded on every trial, incl. on a page that had never been
        interacted with before. Root cause not conclusively identified
        (see this case's Run Report); flagged as a project finding for the
        lead, not filed as a product defect (Playwright's own simulated
        click — which mirrors trusted CDP-level browser input — also fails,
        so this is not confirmed to affect a real end-user's mouse click).
        """
        btn = self.get_row_actions_button(row)
        self.page.evaluate(
            "(el) => { "
            "const key = Object.keys(el).find(k => k.startsWith('__reactProps')); "
            "if (!key) throw new Error('No React props found on row-actions button'); "
            "el[key].onClick({ currentTarget: el, target: el, preventDefault(){}, stopPropagation(){} }); "
            "}",
            btn.element_handle(),
        )
        expect(self.actions_menu_delete).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    def get_actions_menu_item_texts(self) -> list[str]:
        """Return the visible actions-menu items' exact text content, in DOM
        order — used to assert the dropdown shows exactly 'Edit value',
        'Hide', 'Delete' in that order (AFS step 4). Only one menu instance
        is ever open at a time, so this is unambiguous page-wide."""
        items = self.page.locator(self.SECRET_ACTIONS_MENU_ITEM_PREFIX_SELECTOR)
        return items.all_text_contents()

    def click_edit_value_menu_item(self, row, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the 'Edit value' actions-menu item to enter edit mode for
        *row*; wait for the edit-open GET
        (``/secrets/secret/default/{project_id}/{name}``) to resolve AND for
        *row*'s Value input to become visible (ELITEA-2347 step 3).

        Returns the Playwright ``Response`` for the edit-open GET —
        side-channel proof this fires (same endpoint/method the row-level
        eye-icon reveal uses, ELITEA-2343). Its plaintext result is fetched
        then discarded, never displayed: confirmed in source
        (``SecretsTable.jsx``'s wrapped ``handleEditClick``) and live (the
        Value input renders EMPTY, not pre-filled — see
        :meth:`get_row_value_input`).
        """

        def _is_edit_open_response(response) -> bool:
            return (
                SECRET_DELETE_URL_SUBSTRING in response.url
                and response.request.method == "GET"
            )

        with self.page.expect_response(
            _is_edit_open_response, timeout=timeout
        ) as resp_info:
            self.actions_menu_edit_value.click()
        expect(self.get_row_value_input(row)).to_be_visible(timeout=timeout)
        return resp_info.value

    def fill_edit_value(self, row, new_value: str) -> None:
        """Type *new_value* into *row*'s Value input (edit-value mode) —
        MUI needs keyboard events for React onChange, per
        .claude/rules/mui-patterns.md (ELITEA-2347 step 6)."""
        value_input = self.get_row_value_input(row)
        value_input.click()
        value_input.press_sequentially(new_value, delay=20)

    def save_edit_value(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the checkmark (✓) icon to persist an edit-value change;
        wait for the PUT ``.../secret/default/{project_id}/{name}`` to
        resolve (ELITEA-2347 step 6).

        Returns a ``(Response, dict | None)`` tuple: the Playwright
        ``Response`` (side-channel proof of server-side persistence) and
        the request's parsed JSON body.

        DECLARED IMPROVISATION — reads the body via a temporary
        ``page.route()`` interceptor (reading ``route.request.post_data_json``
        inside the handler, then ``route.continue_()``) rather than
        ``response.request.post_data_json`` / ``Page.expect_request``.
        Confirmed live this session (headed AND headless, this project's
        actual Chromium 149): both of the latter reliably return ``None``
        for this endpoint's PUT even though ``content-length: 34`` proves a
        body was sent — a CDP-level limitation for this fetch-dispatched
        request where Playwright's post-hoc ``postData`` read arrives too
        late for the buffer, not specific to this project's product code.
        Interception reads the body BEFORE the request leaves the browser,
        which is unaffected. No sanctioned canon pattern covers Playwright
        request-body capture in this project yet — flagged for the lead per
        `.agents/role-overrides.md` § Declared-improvisation protocol.
        """

        def _is_edit_save_response(response) -> bool:
            return (
                SECRET_DELETE_URL_SUBSTRING in response.url
                and response.request.method == "PUT"
            )

        captured: dict = {}
        route_pattern = "**/secrets/secret/default/**"

        def _capture_put_body(route):
            if route.request.method == "PUT":
                captured["post_data_json"] = route.request.post_data_json
            route.continue_()

        self.page.route(route_pattern, _capture_put_body)
        try:
            with self.page.expect_response(
                _is_edit_save_response, timeout=timeout
            ) as resp_info:
                self.save_button.click()
        finally:
            self.page.unroute(route_pattern, _capture_put_body)
        return resp_info.value, captured.get("post_data_json")

    def click_hide_menu_item(self) -> None:
        """Click the 'Hide' actions-menu item and wait for the shared
        AlertDialog confirmation dialog's body text to appear (AFS step 4)."""
        self.actions_menu_hide.click()
        expect(self.alert_dialog_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    def get_hide_confirm_text(self) -> str:
        """Return the hide-confirmation dialog's body text content (AFS step 5)."""
        return (self.alert_dialog_content.text_content() or "").strip()

    def confirm_hide(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the hide-confirmation dialog's confirm ('Hide') button; wait
        for the hide POST to resolve AND for the subsequent list-GET refetch,
        concurrently (both fire from the same click).

        Returns the Playwright ``Response`` for the hide POST (side-channel
        proof of server-side persistence, per AFS step 6 — no success toast
        text was confirmed for this flow, so this is the stable proof)."""

        def _is_hide_response(response) -> bool:
            return (
                SECRET_HIDE_URL_SUBSTRING in response.url
                and response.request.method == "POST"
            )

        with (
            self.page.expect_response(_is_hide_response, timeout=timeout) as hide_info,
            self.page.expect_response(
                self._is_secrets_list_response, timeout=timeout
            ),
        ):
            self.alert_dialog_confirm_button.click()
        return hide_info.value

    def click_delete_menu_item(self) -> None:
        """Click the 'Delete' actions-menu item and wait for the shared
        delete-confirmation modal (DeleteEntityModal) to appear (AFS step 5)."""
        self.actions_menu_delete.click()
        expect(self.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    def fill_delete_confirm_name(self, name: str) -> None:
        """Type *name* into the delete-confirmation dialog's type-to-confirm
        Name field and wait for the Delete button to become enabled.

        MUI needs keyboard events for React onChange
        (``.claude/rules/mui-patterns.md``); waiting on the button's enabled
        state is the real signal the typed value propagated, rather than a
        fixed delay.
        """
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(name, delay=20)
        expect(self.delete_confirm_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    def confirm_delete(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the delete-confirmation dialog's Delete button; wait for
        the DELETE request to resolve AND for the subsequent list-GET
        refetch, concurrently (both fire from the same click).

        Returns the Playwright ``Response`` for the DELETE (side-channel
        proof of server-side persistence, per AFS step 6 — the confirmation
        toast has no testid and is not a substitute for this).
        """

        def _is_delete_response(response) -> bool:
            return (
                SECRET_DELETE_URL_SUBSTRING in response.url
                and response.request.method == "DELETE"
            )

        with (
            self.page.expect_response(_is_delete_response, timeout=timeout) as delete_info,
            self.page.expect_response(
                self._is_secrets_list_response, timeout=timeout
            ),
        ):
            self.delete_confirm_button.click()
        return delete_info.value

    def get_row_visibility_toggle_button(self, row):
        """Return the Show/Hide (eye icon) toggle button Locator scoped
        within *row* (a Locator returned by :meth:`get_row_by_name`)."""
        return row.locator(self.SECRET_ROW_VISIBILITY_TOGGLE_BUTTON_SELECTOR)

    def expect_visibility_icon_masked_state(self, row, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Assert *row*'s toggle button currently renders the masked/closed-eye
        state (MUI's `VisibilityIcon`, AFS steps 3/9)."""
        toggle_button = self.get_row_visibility_toggle_button(row)
        expect(toggle_button.locator(self.VISIBILITY_ICON_VISIBLE_SELECTOR)).to_be_visible(
            timeout=timeout
        )

    def expect_visibility_icon_revealed_state(self, row, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Assert *row*'s toggle button currently renders the revealed/crossed-eye
        state (MUI's `VisibilityOffIcon`, AFS step 6)."""
        toggle_button = self.get_row_visibility_toggle_button(row)
        expect(toggle_button.locator(self.VISIBILITY_ICON_HIDDEN_SELECTOR)).to_be_visible(
            timeout=timeout
        )

    def reveal_secret_value(self, row, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click *row*'s Show/Hide toggle to REVEAL the plaintext value; wait
        for the reveal GET (`useLazySecretShowQuery`) to resolve.

        Returns the Playwright ``Response`` — side-channel proof this is a
        real server round-trip, not a client-side unmask (AFS step 4). Shares
        the exact URL substring with the delete endpoint (differing only by
        HTTP method), so the predicate filters on GET explicitly.
        """

        def _is_reveal_response(response) -> bool:
            return (
                SECRET_DELETE_URL_SUBSTRING in response.url
                and response.request.method == "GET"
            )

        toggle_button = self.get_row_visibility_toggle_button(row)
        with self.page.expect_response(_is_reveal_response, timeout=timeout) as resp_info:
            toggle_button.click()
        return resp_info.value

    def hide_secret_value(self, row) -> None:
        """Click *row*'s crossed-out eye toggle to re-mask the value —
        purely client-side (AFS step 7); fires no network request. Callers
        that need to prove the no-request contract should wrap this call with
        :meth:`capture_requests_matching` themselves (see the test)."""
        toggle_button = self.get_row_visibility_toggle_button(row)
        toggle_button.click()

    # ------------------------------------------------------------------
    # ELITEA-2330 / 2331 / 2332 / 2334 / 2342 — listing layout, sorting,
    # pagination, search and the masked-value reference format.
    # All additive: no existing method body is touched.
    # ------------------------------------------------------------------

    def sort_icon(self, field: str):
        """Return the sort-control locator for *field*.

        Args:
            field: the column's ``field`` id from ``SecretsTable.jsx`` —
                ``"name"`` | ``"secretValue"`` | ``"actions"``. Only ``name`` is
                ``sortable: true``, so the other two resolve to zero elements
                (asserted as such by ELITEA-2331).
        """
        return self.page.locator(self.SECRET_SORT_ICON_SELECTOR.format(field))

    def click_column_header(self, field: str) -> None:
        """Click the *field* column header to toggle its sort direction.

        Sorting is client-side over the FULL dataset — no network request
        fires, so callers assert the re-render with an auto-retrying
        ``expect`` on the rendered cells, never a wait on a response.
        """
        self.column_header(field).click()

    def get_row_names(self) -> list[str]:
        """Return the rendered rows' secret names, in rendered order."""
        return [(text or "").strip() for text in self.name_cell.all_text_contents()]

    def get_row_values(self) -> list[str]:
        """Return the rendered rows' masked Value-cell texts, in rendered order."""
        return [(text or "").strip() for text in self.value_cell.all_text_contents()]

    def get_pagination_total(self, timeout: int = UI_ELEMENT_TIMEOUT) -> int:
        """Return the total row count parsed out of the ``"N - M of T"`` range label.

        The label is the product's own arithmetic, so every expectation built on
        it stays correct as the project's secret count changes — unlike a
        hardcoded total, which would break on the next secret anyone creates.
        """
        self.pagination_info.wait_for(state="visible", timeout=timeout)
        text = self.get_pagination_text()
        match = re.search(r"of\s+(\d+)\s*$", text)
        if not match:
            raise AssertionError(
                f"Could not parse a total out of the pagination label {text!r} "
                '(expected the "N - M of T" shape)'
            )
        return int(match.group(1))

    def click_next_page(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Advance to the next page and wait for the range label to change.

        Pure client-side state (``usePagination``) — the wait is on the rendered
        label, never on a network response (none fires).
        """
        before = self.get_pagination_text()
        self.next_page_button.click()
        expect(self.pagination_info).not_to_have_text(before, timeout=timeout)

    def select_page_size(self, page_size: int, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Open the rows-per-page select, choose *page_size*, and wait for the
        table to re-render at the new size.

        ``handlePageSizeChange`` also resets the page to the first one — callers
        that care assert that separately (ELITEA-2332 step 6).
        """
        self.page_size_select_combobox.wait_for(state="visible", timeout=timeout)
        self.page_size_select_combobox.click()
        option = self.page.locator(self.PAGE_SIZE_OPTION_SELECTOR.format(page_size))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        expect(self.page_size_select).to_have_text(str(page_size), timeout=timeout)
        logger.info("Selected rows-per-page = %s", page_size)

    def collect_all_row_names(self, max_pages: int = 20) -> list[str]:
        """Return EVERY secret name in the current (unfiltered) list, by walking
        the pagination at the largest available page size.

        Needed because the project holds far more secrets than one page shows:
        a filter assertion computed from page 1 alone would call a broken filter
        correct. Safety-capped at *max_pages* trips so a pagination regression
        fails loudly instead of looping forever.
        """
        self.select_page_size(100)
        names: list[str] = []
        for _ in range(max_pages):
            names.extend(self.get_row_names())
            if self.next_page_button.is_disabled():
                break
            self.click_next_page()
        else:
            raise AssertionError(
                f"Pagination did not reach the last page within {max_pages} pages — "
                "suspect a pagination regression"
            )
        return names

    def type_search(self, term: str) -> None:
        """Replace the search field's content with *term*, typing it one
        character at a time.

        ``press_sequentially`` (not ``fill``) so every keystroke fires React's
        ``onChange`` — which is what the per-keystroke filter contract under
        test actually reacts to (`.claude/rules/mui-patterns.md`).
        """
        self.search_input.click()
        self.search_input.fill("")
        self.search_input.press_sequentially(term, delay=20)

    def clear_search(self) -> None:
        """Clear the search field (fires ``onChange`` with an empty value).

        ``fill("")`` is reliable on this control — it is a plain MUI
        ``InputBase`` with no ``useAutoBlur``, unlike the create-row Name input
        whose ``Control+a`` unreliability is documented on
        :meth:`clear_and_type_name`.
        """
        self.search_input.click()
        self.search_input.fill("")

    def get_search_value(self) -> str:
        """Return the search field's current value."""
        return self.search_input.input_value()
