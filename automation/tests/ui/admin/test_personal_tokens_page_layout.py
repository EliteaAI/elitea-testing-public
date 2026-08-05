"""UI test — Personal Tokens page loads with correct layout and components.

Read-only verification against the logged-in user's existing project token
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes a token. If the active project's tokens
are ever bulk-deleted, this test will correctly go RED for a genuinely
missing precondition — the page renders an `EmptyStatePage` instead of the
table when the token list is empty (see AFS § Preconditions).

Test case: ELITEA-2277
AFS: test-specs/settings-personal-tokens/l3_personal-tokens-page-layout-and-components_ELITEA-2277.md
"""

import logging

import allure
import pytest
from pages.personal_tokens_page import PersonalTokensPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

EXPECTED_COLUMN_COUNT = 4
EXPECTED_ACTION_ICON_COUNT = 4
EXPECTED_ACTION_ICON_TESTIDS = (
    "token-action-preview-button",
    "token-action-vscode-button",
    "token-action-jetbrains-button",
    "token-action-delete-button",
)


class TestPersonalTokensPageLayout:
    """ELITEA-2277 — Personal Tokens page loads with correct layout and components."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2277_personal-tokens-page-layout-and-components.md",
        "onetest-ai Test Case link",
    )
    def test_personal_tokens_page_layout_and_components(self, page):
        """Page header, search input, add button, 4-column table, and every
        row's 4 action icons all render as specified; no console errors."""
        tokens_page = PersonalTokensPage(page)
        console_errors = tokens_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Personal Tokens: token rows become "
                "visible (confirms the page loaded past the loading spinner AND the "
                "empty-state precondition did not trigger)"
            ):
                tokens_page.navigate()
                row_count = tokens_page.token_row.count()
                assert row_count > 0, (
                    f"Expected the tokens table to render at least one row, got {row_count}"
                )

            with allure.step('Step 2 — Verify the page header shows "Personal Tokens"'):
                assert tokens_page.page_title.text_content() == "Personal Tokens", (
                    f"Expected page header text 'Personal Tokens', got "
                    f"{tokens_page.page_title.text_content()!r}"
                )

            with allure.step(
                'Step 3 — Verify a "Search tokens..." input is present in the top right'
            ):
                assert tokens_page.search_input.is_visible(), (
                    "Expected the token search input to be visible"
                )
                placeholder = tokens_page.search_input.get_attribute("placeholder")
                assert placeholder == "Search tokens...", (
                    f"Expected search input placeholder 'Search tokens...', got {placeholder!r}"
                )

            with allure.step('Step 4 — Verify a "+" add-token button is present and enabled'):
                assert tokens_page.add_button.is_visible(), (
                    "Expected the add-token button to be visible"
                )
                assert tokens_page.add_button.is_enabled(), (
                    "Expected the add-token button to be enabled"
                )

            with allure.step(
                "Step 5 — Verify the tokens table has exactly four columns: Token name, "
                "Token value, Expiration, Actions"
            ):
                assert tokens_page.column_header_name.text_content() == "Token name", (
                    f"Expected 1st column header 'Token name', got "
                    f"{tokens_page.column_header_name.text_content()!r}"
                )
                assert tokens_page.column_header_token.text_content() == "Token value", (
                    f"Expected 2nd column header 'Token value', got "
                    f"{tokens_page.column_header_token.text_content()!r}"
                )
                assert tokens_page.column_header_expires.text_content() == "Expiration", (
                    f"Expected 3rd column header 'Expiration', got "
                    f"{tokens_page.column_header_expires.text_content()!r}"
                )
                assert tokens_page.column_header_actions.text_content() == "Actions", (
                    f"Expected 4th column header 'Actions', got "
                    f"{tokens_page.column_header_actions.text_content()!r}"
                )
                header_count = tokens_page.get_column_header_count()
                assert header_count == EXPECTED_COLUMN_COUNT, (
                    f"Expected exactly {EXPECTED_COLUMN_COUNT} column headers, "
                    f"got {header_count}"
                )

            with allure.step(
                "Step 6 — For the first token row: verify Actions column shows exactly "
                "four icons (eye, VSCode, JetBrains, trash), and no console error was "
                "raised by the page load"
            ):
                icon_count = tokens_page.get_first_row_action_icon_count()
                assert icon_count == EXPECTED_ACTION_ICON_COUNT, (
                    f"Expected exactly {EXPECTED_ACTION_ICON_COUNT} action icons on the "
                    f"first row, got {icon_count}"
                )
                for testid in EXPECTED_ACTION_ICON_TESTIDS:
                    icon = tokens_page.get_first_row_action_icon(testid)
                    assert icon.is_visible(), f"Expected action icon {testid!r} to be visible"

                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
