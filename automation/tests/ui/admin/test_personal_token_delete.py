"""UI test — Delete a personal token and verify it is removed from the table.

The token this case deletes is CREATED BY THE TEST through the real UI create
flow. The case text says "locate an existing token", and the honest reading is
"a token that exists at that moment": the five persistent live tokens are shared
data, two of them (`Marian`, `New`) are irrecoverably `Expired` and the merged
`test_expired_token_shows_expired_icon_and_label` (ELITEA-2284) reads its
`expired` branch off them — deleting any of them destroys another test's
fixture. Nothing about the system under test is substituted: the token is
created, deleted and re-read through the product's own UI and API.

⚠️ The post-delete refetch window (surface digest): `TokensTable.jsx` unmounts
the WHOLE table while the refetch is in flight, so `token-row` count is 0 for a
moment and `expect(deleted_row).to_have_count(0)` passes VACUOUSLY there — it
would pass against a delete that never happened. The total-count assertion
(`rows_before - 1`) runs FIRST for exactly that reason: it cannot be satisfied
while the table is unmounted.

Test case: ELITEA-2281
AFS: test-specs/settings-personal-tokens/l3_delete-personal-token-removed-from-table_ELITEA-2281.md
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
EXPECTED_PAGE_TITLE = "Personal Tokens"
EXPECTED_DIALOG_TITLE = "Delete confirmation"
EXPECTED_CANCEL_TEXT = "Cancel"


class TestPersonalTokenDelete:
    """ELITEA-2281 — Delete a personal token and verify it is removed from the table."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2281_delete-a-personal-token-and-verify-it-is-removed-from-the-ta.md",
        "onetest-ai Test Case link",
    )
    def test_delete_personal_token_removed_from_table(self, page):
        """The row's trash icon opens the shared delete-confirmation dialog,
        whose Delete button stays disabled until the token's exact name is
        typed; confirming fires `DELETE /auth/token/{uuid}` -> 204, the row
        leaves a settled table, and the deletion survives a page reload (proven
        against the reload's own GET payload, not just a second DOM read)."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = collect_console_errors(page)
        token_name = f"autotest-token-{uuid.uuid4().hex[:8]}"

        try:
            with allure.step(
                "Setup (not a case step) — create the token this case deletes via "
                "the real UI create flow"
            ):
                tokens_page.navigate()
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                create_page.fill_name(token_name)
                create_response = create_page.click_generate()
                assert create_response.status == 200, (
                    f"Expected 200 from the token-create POST, got {create_response.status}"
                )
                create_page.close_dialog()
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    1, timeout=ROW_WAIT_TIMEOUT
                )
                rows_before = tokens_page.token_row.count()
                assert rows_before > 0, "Expected a populated tokens table after the create"

            with allure.step("Step 1 — Navigate to Settings -> Personal Tokens"):
                tokens_page.navigate()
                expect(tokens_page.page_title).to_have_text(EXPECTED_PAGE_TITLE)

            with allure.step("Step 2 — Locate the token in the table"):
                row = tokens_page.get_row_by_name(token_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(tokens_page.get_row_name_cell(row)).to_have_text(token_name)

            with allure.step("Step 3 — Click the trash icon in the Actions column"):
                tokens_page.get_row_action_icon(row, "token-action-delete-button").click()

            with allure.step(
                "Step 4 — Verify the confirmation dialog appears: title, message "
                "naming the token, Cancel, and a Delete button that is DISABLED "
                "before anything is typed"
            ):
                expect(tokens_page.delete_confirm_dialog).to_be_visible(
                    timeout=ROW_WAIT_TIMEOUT
                )
                expect(tokens_page.delete_confirm_title).to_have_text(EXPECTED_DIALOG_TITLE)
                expect(tokens_page.delete_confirm_message).to_have_text(
                    f"Are you sure to delete the {token_name}? "
                    "Enter the name to complete the action."
                )
                expect(tokens_page.delete_confirm_cancel_button).to_be_visible()
                expect(tokens_page.delete_confirm_cancel_button).to_have_text(
                    EXPECTED_CANCEL_TEXT
                )
                expect(tokens_page.delete_confirm_button).to_be_disabled()

            with allure.step(
                "Step 5 — Confirm deletion: a PREFIX of the name leaves Delete "
                "disabled (the gate is a real exact-match gate), the full name "
                "enables it, and confirming returns 204 and closes the dialog"
            ):
                tokens_page.type_delete_confirm_name(token_name[:-2])
                expect(tokens_page.delete_confirm_button).to_be_disabled()
                tokens_page.type_delete_confirm_name(token_name[-2:], click_first=False)
                expect(tokens_page.delete_confirm_button).to_be_enabled()

                delete_response = tokens_page.confirm_delete_and_wait_for_response()
                assert delete_response.status == 204, (
                    f"Expected 204 from DELETE {delete_response.url}, "
                    f"got {delete_response.status}"
                )
                expect(tokens_page.delete_confirm_dialog).to_have_count(0)

            with allure.step(
                "Step 6 — Verify the token is removed from the table (total count "
                "first — the named-row check alone passes vacuously while the "
                "table is unmounted during the refetch)"
            ):
                expect(tokens_page.token_row).to_have_count(
                    rows_before - 1, timeout=ROW_WAIT_TIMEOUT
                )
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(0)

            with allure.step(
                "Step 7 — Reload the page; verify the deleted token does not "
                "reappear, in the DOM or in the reload's own API payload"
            ):
                list_response = tokens_page.reload_and_wait_for_tokens()
                assert list_response.status == 200, (
                    f"Expected 200 from the token-list GET after reload, "
                    f"got {list_response.status}"
                )
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
                expect(tokens_page.token_row).to_have_count(rows_before - 1)

                payload = list_response.json()
                assert isinstance(payload, list), (
                    f"Expected the token-list GET to return a JSON array, got {type(payload)}"
                )
                payload_names = [item.get("name") for item in payload]
                assert token_name not in payload_names, (
                    f"Deleted token {token_name!r} is still present in the token-list "
                    f"API payload {payload_names!r} — the row removal was cosmetic"
                )
                assert len(payload) == rows_before - 1, (
                    f"Expected {rows_before - 1} tokens in the API payload, got {len(payload)}"
                )

            with allure.step("Step 8 — Verify no console errors across the flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Safety net (not an AFS case step) — deleting the token IS this
            # case, so this only fires if the test died before step 5 and would
            # otherwise leak a row into shared live data.
            leftover = tokens_page.get_row_by_name(token_name)
            if leftover.count() > 0:
                tokens_page.get_row_action_icon(
                    leftover.first, "token-action-delete-button"
                ).click()
                tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
                tokens_page.fill_delete_confirm_name(token_name)
                tokens_page.confirm_delete()
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
