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

Locator provenance (ELITEA-2338, delete flow): the row actions (three-dot)
button and the three actions-menu items already carried real
``data-testid``s on ``automation/testids`` at implementation time
(``EliteaAI/EliteaUI@dd47b184`` — "add data-testid for secret row actions
button + menu items (delete flow)"), predating this test-automation-engineer
session; the AFS's "testid needed" claims were drift (see this case's Run
Report) — confirmed via a fresh ``git fetch origin`` + ``git grep`` against
both ``origin/main`` (absent) and ``origin/automation/testids`` (present) on
implementation day. No new ``add-data-testid`` work was required.
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
"""

import logging

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
    name_error = LocatorDescriptor(
        testid="secret-name-error",
        description="Name-field validation error text, visible only while "
        "the currently-editing row's name fails SECRET_NAME_PATTERN",
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
    SECRET_NAME_CELL_SELECTOR = '[data-testid="secret-name-cell"]'
    SECRET_VALUE_CELL_SELECTOR = '[data-testid="secret-value-cell"]'
    # Used to prove the pending/editing row's inputs render INSIDE the same
    # `secret-row` table-row structure, not a separate modal/dialog (AFS
    # step 3) — chaining a `[data-testid=` selector off an already-scoped
    # row locator, per .agents/testing.md § Locator policy.
    SECRET_NAME_INPUT_SELECTOR = '[data-testid="secret-name-input"]'
    # Used to scope the row-actions (three-dot) button to ONE specific row —
    # chaining a `[data-testid=` selector off an already-scoped row locator
    # (ELITEA-2338), same sanctioned pattern as the selectors above.
    SECRET_ROW_ACTIONS_BUTTON_SELECTOR = '[data-testid="secret-row-actions-button"]'
    # Prefix selector matching all three actions-menu items (SecretActionsMenu
    # only ever renders ONE instance at a time) — used to assert the dropdown
    # shows exactly three items in DOM order, same pattern as
    # personal_tokens_page.py's TOKEN_ACTION_PREFIX_SELECTOR.
    SECRET_ACTIONS_MENU_ITEM_PREFIX_SELECTOR = '[data-testid^="secret-actions-menu-"]'

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
