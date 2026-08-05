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

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.personal_tokens")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by the token-list fetch (`useTokenListQuery`) — used to wait
# for the initiating GET to resolve before asserting on the rendered table.
TOKEN_LIST_URL_SUBSTRING = "/auth/token/"


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

    # Scoped sub-selectors — count/prefix assertions within a parent testid,
    # per .agents/testing.md § Locator policy (UPPER_CASE class constants).
    COLUMN_HEADER_PREFIX_SELECTOR = '[data-testid^="personal-token-column-header-"]'
    TOKEN_ACTION_PREFIX_SELECTOR = '[data-testid^="token-action-"]'
    # Named-testid template — scoped lookup of a single action icon within an
    # already-testid-scoped row (the ``{}`` parameter is the exact testid, not
    # data-derived; kept as a class-level template per the same "pattern stays
    # in the inventory" rationale as a runtime-parameterized testid).
    TOKEN_ACTION_ICON_SELECTOR = '[data-testid="{}"]'

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
