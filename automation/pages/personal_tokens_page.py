"""Personal Tokens page object (Settings → Personal Tokens).

URL: /settings/tokens

Covers the page layout (header title, search input, add-token button) and the
tokens table (``TokensTable.jsx``, built on the shared ``grid-table``
components) — column headers and each token row's four action icons
(preview/VSCode/JetBrains/delete).

Locator provenance (ELITEA-2277, testid needed for the whole surface — zero
pre-existing testids in the personal-tokes component tree):
``personal-tokens-page-title`` / ``personal-tokens-search-input`` /
``personal-tokens-add-button`` are new caller-supplied testid props threaded
through the shared ``DrawerPageHeader`` (``titleTestId`` prop,
``slotProps.searchInput.testId`` forwarded onto the already-testid-aware
``SimpleSearchBar``, ``slotProps.addButton.testId`` on the add IconButton) —
per ``.agents/testing.md`` "shared components never hardcode feature-scoped
testids", the values are supplied at the ``PersonalTokens.jsx`` call site, not
hardcoded in ``DrawerPageHeader``. ``personal-token-column-header-*`` wires
``GridTableHeader``'s existing ``columnTestIdPrefix`` prop (already accepted,
``TokensTable.jsx`` just didn't pass it). ``token-row`` wires ``GridTableRow``'s
existing ``data-testid`` prop (same "wire an existing prop" pattern as
``NotificationCenterPage.notification_row``). ``token-action-preview-button`` /
``token-action-vscode-button`` / ``token-action-jetbrains-button`` are new
static ``data-testid``s on the three per-row icon elements in
``TokenActionsCell``. ``token-action-delete-button`` wires the shared
``DeleteEntityButton``'s existing ``testId`` prop.
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.personal_tokens")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by the token-list fetch (`useTokenListQuery`) — used to wait
# for the initiating GET to resolve before asserting on the rendered table.
TOKEN_LIST_URL_SUBSTRING = "/auth/token/"

# Route the add-button navigates to (ELITEA-2280) — a dedicated page, NOT an
# inline dialog (confirmed live). Shared with create_personal_token_page.py.
CREATE_PERSONAL_TOKEN_PATH = "/settings/create-personal-token"


class PersonalTokensPage(BasePage):
    """Settings → Personal Tokens page (page layout + tokens table)."""

    page_title = LocatorDescriptor(
        testid="personal-tokens-page-title",
        description='Page header title — exact text "Personal Tokens"',
    )
    search_input = LocatorDescriptor(
        testid="personal-tokens-search-input",
        description='Token search input — placeholder "Search tokens..."',
    )
    add_button = LocatorDescriptor(
        testid="personal-tokens-add-button",
        description="Add-token (+) button, top-right of the header",
    )
    token_row = LocatorDescriptor(
        testid="token-row",
        description="Token table row (repeatable, one per visible row)",
    )
    column_header_name = LocatorDescriptor(
        testid="personal-token-column-header-name",
        description='Table column header — "Token name"',
    )
    column_header_token = LocatorDescriptor(
        testid="personal-token-column-header-token",
        description='Table column header — "Token value"',
    )
    column_header_expires = LocatorDescriptor(
        testid="personal-token-column-header-expires",
        description='Table column header — "Expiration"',
    )
    column_header_actions = LocatorDescriptor(
        testid="personal-token-column-header-actions",
        description='Table column header — "Actions"',
    )
    row_name_cell = LocatorDescriptor(
        testid="token-name-cell",
        description="Token name cell (repeatable, one per visible row) — resolves "
        "every row's name cell in DOM order, so the rendered sort order can be "
        "asserted with an auto-retrying to_have_text(list) assertion.",
    )
    table_empty_message = LocatorDescriptor(
        testid="personal-tokens-table-empty-message",
        description='Grid-table empty message ("No tokens") shown when a search '
        "matches nothing. NOTE: this is the *no-match* branch of the populated "
        "page — the page header, search box and rows container stay mounted. It is "
        "NOT the zero-tokens-exist EmptyStatePage (empty-state-title, "
        '"No tokens yet"), which replaces the whole page.',
    )

    # Delete-confirmation modal (shared DeleteEntityModal.jsx, ELITEA-2280
    # cleanup flow) — testids already exist app-wide (repo precedent: each
    # page object that triggers this shared modal declares its own
    # LocatorDescriptor for it, e.g. mcp_form_page.py / chat_page.py /
    # artifacts_page.py — no new testid work here).
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal container (shared DeleteEntityModal).",
    )
    delete_confirm_name_input = LocatorDescriptor(
        testid="delete-confirm-name-input",
        description="Delete dialog's type-to-confirm Name field — resolves to the "
        "MUI TextField wrapper, NOT the real <input> (same shape as "
        "mcp_form_page.py's field); click + press_sequentially() types into "
        "the focused inner input.",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete dialog's confirm button — disabled until the typed "
        "name matches the entity name exactly.",
    )

    # Scoped sub-selectors — count/prefix assertions within a parent testid,
    # per .agents/testing.md § Locator policy (UPPER_CASE class constants).
    COLUMN_HEADER_PREFIX_SELECTOR = '[data-testid^="personal-token-column-header-"]'
    TOKEN_ACTION_PREFIX_SELECTOR = '[data-testid^="token-action-"]'
    # Named-testid template — scoped lookup of a single action icon within an
    # already-testid-scoped row (the ``{}`` parameter is the exact testid, not
    # data-derived; kept as a class-level template per the same "pattern stays
    # in the inventory" rationale as a runtime-parameterized testid).
    TOKEN_ACTION_ICON_SELECTOR = '[data-testid="{}"]'
    # Row cell-content selectors (ELITEA-2280) — static per-row testids,
    # scoped by chaining off an already-testid-scoped row locator (same
    # sanctioned pattern as TOKEN_ACTION_ICON_SELECTOR / get_first_row_action_icon).
    TOKEN_NAME_CELL_SELECTOR = '[data-testid="token-name-cell"]'
    TOKEN_VALUE_CELL_SELECTOR = '[data-testid="token-value-cell"]'
    # State via data-* attribute on a stable testid (not a state-switched
    # testid) — per .agents/testing.md "Testid = stable identity" ruling.
    # The ``{}`` parameter is the exact ``data-expiration-state`` value
    # (active|warning|never|expired), not test-generated data.
    TOKEN_EXPIRATION_STATUS_SELECTOR = '[data-testid="token-expiration-status"][data-expiration-state="{}"]'
    # State-AGNOSTIC sibling of the above (ELITEA-2279): the state-filtered
    # selector can only answer "is this row in state X?", never "what state is
    # this row in?" — which is what an expiration *sort* assertion needs.
    TOKEN_EXPIRATION_STATUS_ANY_SELECTOR = '[data-testid="token-expiration-status"]'
    # Sort controls — emitted by GridTableHeader's columnTestIdPrefix for
    # sortable columns ONLY (ELITEA-2279). The prefix form counts them; the
    # named form addresses one column (the ``{}`` parameter is the column
    # field name from TOKENS_COLUMNS, not test-generated data).
    SORT_ICON_PREFIX_SELECTOR = '[data-testid^="personal-token-sort-icon-"]'
    SORT_ICON_SELECTOR = '[data-testid="personal-token-sort-icon-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_token_list_response(self, response) -> bool:
        """True for the token-list GET (`useTokenListQuery`)."""
        return (
            TOKEN_LIST_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def navigate(self) -> None:
        """Navigate to /settings/tokens and wait for the first token row to
        become visible.

        Waiting on the row (not just DOM visibility of the page shell)
        matters here: the page renders a loading spinner, then either the
        populated table or an `EmptyStatePage` ("No tokens yet") depending on
        whether the project has any tokens — this confirms the populated
        path was reached, per the AFS's precondition proof (step 1).
        """
        with self.page.expect_response(
            self._is_token_list_response, timeout=NAVIGATION_TIMEOUT
        ):
            super().navigate("/settings/tokens")
        self.token_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_column_header_count(self) -> int:
        """Return the number of rendered table column-header elements
        (matched by the shared ``personal-token-column-header-`` prefix)."""
        return self.page.locator(self.COLUMN_HEADER_PREFIX_SELECTOR).count()

    def get_first_row_action_icon_count(self) -> int:
        """Return the number of action-icon elements in the FIRST token row's
        Actions cell (matched by the shared ``token-action-`` prefix, scoped
        to that row — sanctioned chaining off an already-testid-scoped
        element, per .agents/testing.md § Locator policy)."""
        first_row = self.token_row.first
        return first_row.locator(self.TOKEN_ACTION_PREFIX_SELECTOR).count()

    def get_first_row_action_icon(self, testid: str):
        """Return the Locator for a single named action icon within the
        FIRST token row, scoped to that row (same chaining rationale as
        :meth:`get_first_row_action_icon_count`)."""
        first_row = self.token_row.first
        return first_row.locator(self.TOKEN_ACTION_ICON_SELECTOR.format(testid))

    def click_add_button(self) -> None:
        """Click the add-token ("+") button and wait for the resulting
        navigation to the "New Token" create-flow page.

        The add-button does NOT open an inline dialog — confirmed live
        (ELITEA-2280 AFS) — it navigates to a separate route,
        ``/settings/create-personal-token``. This waits for that URL change
        rather than any in-page dialog.
        """
        self.add_button.click()
        self.page.wait_for_url(
            f"**{CREATE_PERSONAL_TOKEN_PATH}", timeout=NAVIGATION_TIMEOUT
        )

    def get_row_by_name(self, name: str):
        """Return the token row Locator filtered by exact row text match on
        *name* (sanctioned chaining off the already-testid-scoped
        :attr:`token_row`, same pattern as :meth:`get_first_row_action_icon`)."""
        return self.token_row.filter(has_text=name)

    def get_row_name_cell(self, row):
        """Return the name-cell Locator scoped within *row* (a Locator
        returned by :meth:`get_row_by_name`)."""
        return row.locator(self.TOKEN_NAME_CELL_SELECTOR)

    def get_row_value_cell(self, row):
        """Return the masked-value-cell Locator scoped within *row*."""
        return row.locator(self.TOKEN_VALUE_CELL_SELECTOR)

    def get_row_expiration_status(self, row, state: str = "active"):
        """Return the expiration-status Locator scoped within *row*, filtered
        to the given ``data-expiration-state`` value (state via data-*
        attribute on a stable testid, not a state-switched testid — see
        :attr:`TOKEN_EXPIRATION_STATUS_SELECTOR`)."""
        return row.locator(self.TOKEN_EXPIRATION_STATUS_SELECTOR.format(state))

    def get_row_action_icon(self, row, testid: str):
        """Return the Locator for a single named action icon within an
        arbitrary *row* (not necessarily the first row) — generalizes
        :meth:`get_first_row_action_icon` for a row located by
        :meth:`get_row_by_name`."""
        return row.locator(self.TOKEN_ACTION_ICON_SELECTOR.format(testid))

    def get_column_header(self, field: str):
        """Return the column-header Locator for *field* (one of the four
        ``TOKENS_COLUMNS`` fields: ``name`` / ``token`` / ``expires`` /
        ``actions``)."""
        headers = {
            "name": self.column_header_name,
            "token": self.column_header_token,
            "expires": self.column_header_expires,
            "actions": self.column_header_actions,
        }
        try:
            return headers[field]
        except KeyError as exc:
            raise ValueError(
                f"Unknown column field {field!r}; expected one of {sorted(headers)}"
            ) from exc

    def click_column_header(self, field: str) -> None:
        """Click the *field* column header to toggle its sort.

        The whole header cell carries the ``onClick`` (``GridTableHeader.jsx``),
        so the header itself is the control — there is no separate button.
        Sorting is CLIENT-SIDE (the list is already in the RTK-Query cache), so
        no request fires: callers wait on the reordered DOM, never on a
        response.
        """
        self.get_column_header(field).click()

    def get_sort_icon_count(self) -> int:
        """Return the number of rendered sort controls across all columns
        (matched by the shared ``personal-token-sort-icon-`` prefix)."""
        return self.page.locator(self.SORT_ICON_PREFIX_SELECTOR).count()

    def get_sort_icon(self, field: str):
        """Return the sort-control Locator for *field*'s column header.

        Only sortable columns render one, so this is also the handle for the
        ABSENCE assertion on the non-sortable columns.
        """
        return self.page.locator(self.SORT_ICON_SELECTOR.format(field))

    def get_row_names(self) -> list[str]:
        """Return every visible row's token name, in rendered DOM order."""
        return [
            (cell.text_content() or "").strip()
            for cell in self.row_name_cell.all()
        ]

    def get_row_expiration_states(self) -> list[str]:
        """Return every visible row's ``data-expiration-state`` value
        (``active``/``warning``/``never``/``expired``), in rendered DOM order.

        Uses the state-agnostic selector — see
        :attr:`TOKEN_EXPIRATION_STATUS_ANY_SELECTOR`.
        """
        return [
            row.locator(self.TOKEN_EXPIRATION_STATUS_ANY_SELECTOR).get_attribute(
                "data-expiration-state"
            )
            for row in self.token_row.all()
        ]

    def get_first_row_expiration_status(self, state: str):
        """Return the FIRST row's expiration-status Locator filtered to
        *state* — the anchor an expiration-sort assertion waits on
        (``to_have_count`` auto-retries until the re-render lands)."""
        return self.get_row_expiration_status(self.token_row.first, state=state)

    def type_search(self, text: str) -> None:
        """Type *text* into the token search box one character at a time.

        ``SimpleSearchBar`` filters from the native ``onChange`` — per
        keystroke, no Enter, no submit control, no debounce — so
        ``press_sequentially`` is what actually exercises the "real time"
        claim. Never press Enter here.
        """
        self.search_input.click()
        self.search_input.press_sequentially(text, delay=30)

    def clear_search(self) -> None:
        """Clear the token search box via select-all + Backspace.

        ``SimpleSearchBar`` is a plain MUI ``InputBase`` with no ``useAutoBlur``
        wrapper, so ``ControlOrMeta+a`` is reliable here — unlike the
        create-token Name field, whose refocus cycle races the shortcut
        (surface digest § Name-field client-side validation).
        """
        self.search_input.click()
        self.search_input.press("ControlOrMeta+a")
        self.search_input.press("Backspace")

    def get_search_value(self) -> str:
        """Return the current value of the token search box.

        The testid resolves to the native ``<input>`` (wired through
        ``SimpleSearchBar``'s ``inputProps``), so ``input_value()`` works
        directly — unlike the delete dialog's MUI-wrapper field on this page.
        """
        return self.search_input.input_value()

    def fill_delete_confirm_name(self, name: str) -> None:
        """Type *name* into the delete-confirmation dialog's type-to-confirm
        Name field and wait for the Delete button to become enabled.

        Same click + press_sequentially shape as ``mcp_form_page.py``'s
        ``fill_delete_confirm_name`` — MUI needs keyboard events for React
        onChange (``.claude/rules/mui-patterns.md``), and waiting on the
        button's enabled state is the real signal the typed value propagated,
        rather than a fixed delay.
        """
        self.delete_confirm_name_input.click()
        self.delete_confirm_name_input.press_sequentially(name, delay=20)
        expect(self.delete_confirm_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    def confirm_delete(self) -> None:
        """Click the delete-confirmation dialog's Delete button."""
        self.delete_confirm_button.click()
