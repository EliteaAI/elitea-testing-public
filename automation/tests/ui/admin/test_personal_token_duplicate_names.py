"""UI test — Duplicate token names are allowed.

Creates TWO real personal tokens sharing one name and deletes both in a
mandatory cleanup loop regardless of outcome.

The shared name is uuid4-suffixed rather than the case's literal
"duplicate-test": the case's intent is "two tokens sharing one name", and since
this very case proves duplicates are permitted, a literal name would silently
match any leftover from an earlier failed run and make the row-count assertions
fail a correct product.

⚠️ `get_row_by_name()` deliberately resolves TWO rows here — the one place on
this surface where the repo's usual row-by-name idiom is not one-to-one. Every
single-row operation indexes (`.first` / `.nth()`); a bare call would raise
Playwright's strict-mode error. Deletion stays unambiguous: the type-to-confirm
field matches the NAME (so either row accepts the same typed text) while the
DELETE targets the clicked row's own uuid.

Test case: ELITEA-2288
AFS: test-specs/settings-personal-tokens/l3_duplicate-token-names-allowed_ELITEA-2288.md
"""

import logging
import re
import uuid

import allure
import pytest
from pages.create_personal_token_page import CreatePersonalTokenPage
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
# The value cell renders `'...' + token.slice(-4)` (TokensTable.jsx renderCell).
MASKED_VALUE_PATTERN = re.compile(r"^\.\.\..{4}$")


class TestPersonalTokenDuplicateNames:
    """ELITEA-2288 — Duplicate token names are allowed."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2288_duplicate-token-names-are-allowed.md",
        "onetest-ai Test Case link",
    )
    def test_duplicate_token_names_are_allowed(self, page):
        """A second create with an identical name raises no validation error,
        keeps Generate enabled and returns 200; both rows render under the same
        name with distinct masked values, each traceable to the full token the
        system issued for it."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = collect_console_errors(page)
        dup_name = f"duplicate-test-{uuid.uuid4().hex[:8]}"

        try:
            with allure.step("Step 1 — Navigate to Settings -> Personal Tokens"):
                tokens_page.navigate()
                expect(tokens_page.page_title).to_have_text("Personal Tokens")
                rows_before = tokens_page.token_row.count()
                assert rows_before > 0, "Expected a populated tokens table before the creates"
                # Guard: the generated name must not already exist, or every
                # later count is off by one.
                expect(tokens_page.get_row_by_name(dup_name)).to_have_count(0)

            with allure.step(f"Step 2 — Create a token named {dup_name!r}"):
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                create_page.fill_name(dup_name)
                first_response = create_page.click_generate()
                assert first_response.status == 200, (
                    f"Expected 200 from the first token-create POST, "
                    f"got {first_response.status}"
                )
                token_1 = create_page.get_dialog_token_value_text()
                assert token_1, "Expected a non-empty token value in the first success dialog"
                expect(create_page.dialog_token_name).to_have_text(dup_name)
                create_page.close_dialog()
                expect(tokens_page.get_row_by_name(dup_name)).to_have_count(
                    1, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step("Step 3 — Create a SECOND token with the same name"):
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                create_page.fill_name(dup_name)
                # A uniqueness regression would most likely land as client-side
                # validation — which the POST-status assertion alone could never
                # see, because the request would never be sent.
                expect(create_page.name_error).to_have_count(0)
                expect(create_page.generate_button).to_be_enabled()
                second_response = create_page.click_generate()
                assert second_response.status == 200, (
                    f"Expected 200 from the second token-create POST with a duplicate "
                    f"name, got {second_response.status}"
                )
                token_2 = create_page.get_dialog_token_value_text()
                assert token_2, "Expected a non-empty token value in the second success dialog"
                create_page.close_dialog()

            with allure.step("Step 4 — Verify both tokens appear in the table without error"):
                rows = tokens_page.get_row_by_name(dup_name)
                expect(rows).to_have_count(2, timeout=ROW_WAIT_TIMEOUT)
                # Non-vacuity: two rows were ADDED (duplicates being legal, a
                # leftover would otherwise satisfy "count == 2" with one create).
                expect(tokens_page.token_row).to_have_count(
                    rows_before + 2, timeout=ROW_WAIT_TIMEOUT
                )
                expect(tokens_page.get_row_name_cell(rows)).to_have_text([dup_name, dup_name])
                # "without error": the UI's only error channel here is the toast
                # (the sole toast this flow can raise is the Copy confirmation,
                # which this test never triggers).
                expect(create_page.toast_message).to_have_count(0)

            with allure.step("Step 5 — Verify each token has a distinct masked value"):
                masked_values = [
                    (tokens_page.get_row_value_cell(rows.nth(index)).text_content() or "").strip()
                    for index in range(2)
                ]
                for masked in masked_values:
                    assert MASKED_VALUE_PATTERN.match(masked), (
                        f"Expected a masked value of the form '...abcd', got {masked!r}"
                    )
                assert masked_values[0] != masked_values[1], (
                    f"Expected the two duplicate-named tokens to render distinct masked "
                    f"values, both read {masked_values[0]!r}"
                )
                # Tie each rendered row back to a token the system actually
                # issued — this is what makes an (astronomically rare) 4-char
                # tail collision diagnosable instead of a mystery failure.
                assert token_1 != token_2, (
                    "Expected the two creates to issue distinct token strings"
                )
                assert set(masked_values) == {"..." + token_1[-4:], "..." + token_2[-4:]}, (
                    f"Expected the rendered masked values {masked_values!r} to be the "
                    f"last-4 masks of the two issued tokens"
                )

            with allure.step("Step 6 — Verify no console errors across the flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Cleanup (not an AFS case step) — mandatory, unwrapped: BOTH rows.
            # The typed name matches either row; the DELETE targets the clicked
            # row's own uuid, so deleting `.first` repeatedly drains the pair.
            remaining = tokens_page.get_row_by_name(dup_name).count()
            while remaining > 0:
                tokens_page.get_row_action_icon(
                    tokens_page.get_row_by_name(dup_name).first,
                    "token-action-delete-button",
                ).click()
                tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
                tokens_page.fill_delete_confirm_name(dup_name)
                tokens_page.confirm_delete()
                # The table unmounts during the post-delete refetch — wait for
                # it to come back before re-counting.
                tokens_page.token_row.first.wait_for(
                    state="visible", timeout=ROW_WAIT_TIMEOUT
                )
                expect(tokens_page.get_row_by_name(dup_name)).to_have_count(
                    remaining - 1, timeout=ROW_WAIT_TIMEOUT
                )
                remaining -= 1
