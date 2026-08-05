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
