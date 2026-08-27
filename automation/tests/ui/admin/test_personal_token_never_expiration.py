"""UI test — Token can be created without an expiration date ("Never").

Creates one real personal token with the `Never` expiration unit and deletes it
in a mandatory cleanup step regardless of outcome. A leaked `Never` token never
expires, so cleanup matters more here than in any sibling case; the five
persistent live tokens are never touched.

The `never` expiration state had no test coverage at all before this case: the
merged ELITEA-2280 test asserts the form's `Days`/`30` DEFAULTS are unchanged,
which is the opposite of this case, and nothing anywhere creates a token with
the `Never` unit.

Test case: ELITEA-2283
AFS: test-specs/settings-personal-tokens/l3_token-created-without-expiration-never_ELITEA-2283.md
"""

import logging
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
EXPECTED_EXPIRATION_LABEL = "Never"


class TestPersonalTokenNeverExpiration:
    """ELITEA-2283 — Token can be created without an expiration date."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2283_token-can-be-created-without-an-expiration-date.md",
        "onetest-ai Test Case link",
    )
    def test_token_created_without_expiration_shows_never(self, page):
        """Selecting the `Never` expiration unit UNMOUNTS the numeric value
        input, the create POST comes back with `expires: null`, and the new
        row's Expiration cell renders the `never` state with the literal label
        "Never" — not a blank cell and not the `expired` error state."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = collect_console_errors(page)
        token_name = f"autotest-token-{uuid.uuid4().hex[:8]}"

        try:
            with allure.step(
                'Step 1 — Navigate to Settings -> Personal Tokens and click "+"'
            ):
                tokens_page.navigate()
                rows_before = tokens_page.token_row.count()
                assert rows_before > 0, "Expected a populated tokens table before the create"
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                expect(create_page.page_title).to_have_text("New Token")

            with allure.step('Step 2 — Enter a token name and select "Never"'):
                create_page.fill_name(token_name)
                assert create_page.name_input.input_value() == token_name, (
                    f"Expected the Name input to show {token_name!r}, "
                    f"got {create_page.name_input.input_value()!r}"
                )
                create_page.select_expiration_measure("never")
                expect(create_page.expiration_measure_combobox).to_have_text("Never")
                # The form's own expression of "no expiration date": the numeric
                # value input is UNMOUNTED, not merely hidden or disabled.
                expect(create_page.expiration_value_input).to_have_count(0)
                expect(create_page.generate_button).to_be_enabled()

            with allure.step(
                'Step 3 — Click "Generate"; verify the create POST returns 200 with '
                "`expires: null`, then close the success dialog"
            ):
                response = create_page.click_generate()
                assert response.status == 200, (
                    f"Expected 200 from the token-create POST, got {response.status}"
                )
                body = response.json()
                assert body.get("expires") is None, (
                    f"Expected 'expires' to be null for a Never token, "
                    f"got {body.get('expires')!r}"
                )
                expect(create_page.dialog_title).to_have_text("New token generated!")
                expect(create_page.dialog_token_name).to_have_text(token_name)
                create_page.close_dialog()

            with allure.step("Step 4 — Verify the token appears in the table"):
                row = tokens_page.get_row_by_name(token_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(tokens_page.get_row_name_cell(row)).to_have_text(token_name)
                # Non-vacuity: a row was ADDED, not merely matched (the table
                # unmounts during the post-create refetch, and duplicate names
                # are legal on this surface).
                expect(tokens_page.token_row).to_have_count(
                    rows_before + 1, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                'Step 5 — Verify the Expiration column shows "Never" — not a blank '
                "cell and not the expired/error state"
            ):
                never_status = tokens_page.get_row_expiration_status(row, state="never")
                expect(never_status).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(never_status).to_have_text(EXPECTED_EXPIRATION_LABEL)
                expect(
                    tokens_page.get_row_expiration_status(row, state="expired")
                ).to_have_count(0)

            with allure.step("Step 6 — Verify no console errors across the flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Cleanup (not an AFS case step) — mandatory, unwrapped: a leaked
            # `Never` token would pollute shared live data permanently.
            cleanup_row = tokens_page.get_row_by_name(token_name)
            if cleanup_row.count() > 0:
                tokens_page.get_row_action_icon(
                    cleanup_row.first, "token-action-delete-button"
                ).click()
                tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
                tokens_page.fill_delete_confirm_name(token_name)
                tokens_page.confirm_delete()
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
