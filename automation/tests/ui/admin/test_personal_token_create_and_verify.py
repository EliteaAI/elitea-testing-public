"""UI test — Create a new personal token and verify it appears in the table.

Creates one real personal token under the active project (unlike ELITEA-2277,
which is read-only) and deletes it in a mandatory cleanup step regardless of
test outcome, per `.agents/testing.md` § Test data strategy ("clean up loudly
only when the observable requires fresh state" — this case's core observable
IS the freshly created token).

Test case: ELITEA-2280
AFS: test-specs/settings-personal-tokens/l3_personal-token-create-and-verify_ELITEA-2280.md

Also covers ELITEA-2284 ("Expired tokens show a gray icon and active tokens
show a green icon with remaining days") — an `extend-existing` AFS. Steps
4-5 of that case (active token -> green icon + "in X days") are already
asserted by this file's Step 12 below; the new
`test_expired_token_shows_expired_icon_and_label` test appended at the
bottom of this class covers ELITEA-2284's remaining steps 2-3 (expired
token -> gray icon + "Expired" label), read-only against existing live
data.
AFS: test-specs/settings-personal-tokens/lextend_expired-and-active-token-expiration-icons_ELITEA-2284.md

Also covers ELITEA-2286 ("Token name validation — only alphanumeric
characters, underscores, and hyphens are allowed") — an `extend-existing`
AFS. The empty-name-disables-Generate and fresh-valid-name-enables-Generate
observables are already asserted by this file's Step 3 above; the new
`test_invalid_token_name_shows_error_and_keeps_generate_disabled` test
appended at the bottom of this class covers the remaining gap: an invalid
name (special characters or a space) shows the validation error and keeps
Generate disabled, and replacing it with a conforming name clears the error
and re-enables Generate (the invalid->valid recovery transition, never
exercised by the happy path above). Read-only against the create-token
FORM: never clicks Generate, creates no token, needs no cleanup.
AFS: test-specs/settings-personal-tokens/lextend_token-name-validation-invalid-characters-rejected_ELITEA-2286.md
"""

import logging
import uuid

import allure
import pytest
from pages.create_personal_token_page import CreatePersonalTokenPage
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

EXPECTED_WARNING_TEXT = "This token will only be shown once, so make sure to copy and save it."
EXPECTED_TOAST_TEXT = "The token has been copied to the clipboard."
ROW_WAIT_TIMEOUT = 15_000


class TestPersonalTokenCreateAndVerify:
    """ELITEA-2280 — Create a new personal token and verify it appears in the table."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2280_personal-token-create-and-verify.md",
        "onetest-ai Test Case link",
    )
    def test_create_personal_token_and_verify_in_table(self, page):
        """Create a personal token end-to-end (form defaults, Generate, the
        success dialog with warning/name/value/copy-to-clipboard), verify the
        row appears in the table with masked value + active expiration, then
        delete it. No console errors across the flow."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = tokens_page.capture_console_errors()
        token_name = f"autotest-token-{uuid.uuid4().hex[:8]}"
        token_value = None
        row = None

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Personal Tokens, click the add-token "
                "button, and verify navigation to the New Token page (a route change, "
                "not an inline dialog)"
            ):
                tokens_page.navigate()
                tokens_page.click_add_button()
                assert "/settings/create-personal-token" in page.url, (
                    f"Expected navigation to /settings/create-personal-token, got {page.url!r}"
                )

            with allure.step(
                "Step 2 — Verify the New Token form: page title, empty Name input, "
                "Expiration-period defaults (Days / 30)"
            ):
                create_page.wait_for_loaded()
                assert create_page.page_title.text_content() == "New Token", (
                    f"Expected page title 'New Token', got {create_page.page_title.text_content()!r}"
                )
                assert create_page.name_input.input_value() == "", (
                    "Expected the Name input to start empty"
                )
                assert create_page.get_expiration_measure_text() == "Days", (
                    f"Expected expiration unit 'Days', got {create_page.get_expiration_measure_text()!r}"
                )
                assert create_page.get_expiration_value() == "30", (
                    f"Expected expiration value '30', got {create_page.get_expiration_value()!r}"
                )

            with allure.step(
                "Step 3 — Enter the token name; verify Generate transitions from "
                "disabled to enabled"
            ):
                assert create_page.generate_button.is_disabled(), (
                    "Expected Generate disabled while the Name field is empty"
                )
                create_page.fill_name(token_name)
                assert create_page.name_input.input_value() == token_name, (
                    f"Expected Name input to show {token_name!r}, "
                    f"got {create_page.name_input.input_value()!r}"
                )
                assert create_page.generate_button.is_enabled(), (
                    "Expected Generate enabled once a valid name is entered"
                )

            with allure.step(
                "Step 4 — Verify expiration still reads Days / 30 (the case's own "
                "step 5 assertion — these are the page's own defaults, nothing to set)"
            ):
                assert create_page.get_expiration_measure_text() == "Days"
                assert create_page.get_expiration_value() == "30"

            with allure.step(
                "Step 5 — Click Generate; verify the token-create POST resolves 200"
            ):
                response = create_page.click_generate()
                assert response.status == 200, (
                    f"Expected 200 from the token-create POST, got {response.status}"
                )

            with allure.step('Step 6 — Verify the "New token generated!" dialog appears'):
                assert create_page.get_dialog_title_text() == "New token generated!", (
                    f"Expected dialog title 'New token generated!', "
                    f"got {create_page.get_dialog_title_text()!r}"
                )

            with allure.step("Step 7 — Verify the dialog's warning text"):
                assert create_page.get_dialog_warning_text() == EXPECTED_WARNING_TEXT, (
                    f"Expected warning {EXPECTED_WARNING_TEXT!r}, "
                    f"got {create_page.get_dialog_warning_text()!r}"
                )

            with allure.step(
                "Step 8 — Verify the token name is shown above the full token value"
            ):
                assert create_page.get_dialog_token_name_text() == token_name, (
                    f"Expected dialog token-name {token_name!r}, "
                    f"got {create_page.get_dialog_token_name_text()!r}"
                )
                token_value = create_page.get_dialog_token_value_text()
                assert token_value, "Expected a non-empty token value in the dialog"
                assert create_page.is_token_name_above_token_value(), (
                    "Expected the dialog's token-name element to render above the "
                    "token-value element"
                )

            with allure.step(
                "Step 9 — Click Copy; verify the confirmation toast, the button's "
                "state change, and the actual OS clipboard content"
            ):
                toast_text = create_page.click_copy_and_get_toast_text()
                assert toast_text == EXPECTED_TOAST_TEXT, (
                    f"Expected toast {EXPECTED_TOAST_TEXT!r}, got {toast_text!r}"
                )
                assert create_page.get_copy_button_text() == "Copied!", (
                    f"Expected Copy button text 'Copied!', "
                    f"got {create_page.get_copy_button_text()!r}"
                )
                assert create_page.is_copy_button_disabled(), (
                    "Expected the Copy button to be disabled immediately after copying"
                )
                clipboard_text = create_page.read_clipboard_text()
                assert clipboard_text == token_value, (
                    f"Expected clipboard content to equal the dialog's token value, "
                    f"got {clipboard_text!r}"
                )

            with allure.step(
                "Step 10 — Close the dialog; verify navigation back to the tokens table"
            ):
                create_page.close_dialog()
                assert page.url.split("?")[0].rstrip("/").endswith("/settings/tokens"), (
                    f"Expected to land back on /settings/tokens, got {page.url!r}"
                )

            with allure.step(
                "Step 11 — Verify the new token row appears with the entered name and "
                "masked value"
            ):
                row = tokens_page.get_row_by_name(token_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                name_cell_text = tokens_page.get_row_name_cell(row).text_content()
                assert name_cell_text == token_name, (
                    f"Expected the row's name cell to read {token_name!r}, got {name_cell_text!r}"
                )
                expected_masked_value = "..." + token_value[-4:]
                value_cell_text = tokens_page.get_row_value_cell(row).text_content()
                assert value_cell_text == expected_masked_value, (
                    f"Expected the row's value cell to read {expected_masked_value!r}, "
                    f"got {value_cell_text!r}"
                )

            with allure.step(
                'Step 12 — Verify the Expiration cell shows the active (green) state '
                'and "in 30 days"'
            ):
                status = tokens_page.get_row_expiration_status(row, state="active")
                expect(status).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                status_text = (status.text_content() or "").strip()
                assert status_text == "in 30 days", (
                    f"Expected the Expiration cell to read 'in 30 days', got {status_text!r}"
                )

            with allure.step("Step 13 — Verify no console errors were raised across the flow"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs
            # regardless of test outcome: this case creates a real,
            # persistent token in shared live project data).
            cleanup_row = tokens_page.get_row_by_name(token_name)
            if cleanup_row.count() > 0:
                delete_button = tokens_page.get_row_action_icon(
                    cleanup_row, "token-action-delete-button"
                )
                delete_button.click()
                tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
                tokens_page.fill_delete_confirm_name(token_name)
                tokens_page.confirm_delete()
                expect(tokens_page.get_row_by_name(token_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2284_expired-tokens-show-icon-and-active-tokens-show-icon-with-re.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_expired_token_shows_expired_icon_and_label(self, page):
        """ELITEA-2284 (steps 2-3) — an existing expired token's Expiration
        cell shows the gray/expired state icon and the exact 'Expired'
        label. Read-only: uses existing live project data, no token created
        or deleted. (ELITEA-2284 steps 4-5 — active token, green icon, 'in X
        days' — are already asserted by
        test_create_personal_token_and_verify_in_table's Step 12 above; not
        repeated here.)"""
        tokens_page = PersonalTokensPage(page)

        with allure.step("Step 1 — Navigate to Settings -> Personal Tokens"):
            tokens_page.navigate()

        with allure.step("Step 2 — Locate an existing expired token row"):
            row = tokens_page.get_row_by_name("Marian")
            expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            'Step 3 — Verify the Expiration cell shows the expired state '
            '(gray icon) and the exact "Expired" label'
        ):
            status = tokens_page.get_row_expiration_status(row, state="expired")
            expect(status).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
            status_text = (status.text_content() or "").strip()
            assert status_text == "Expired", (
                f"Expected the Expiration cell to read 'Expired', got {status_text!r}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-personal-tokens/ELITEA-2286_token-name-validation-invalid-characters-rejected.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_invalid_token_name_shows_error_and_keeps_generate_disabled(self, page):
        """ELITEA-2286 — a token name containing any character outside
        [a-zA-Z0-9_-] (special characters or a space) shows the validation
        error and keeps Generate disabled; replacing it with a conforming name
        clears the error and re-enables Generate. Read-only against the
        create-token FORM: never clicks Generate, creates no token, needs no
        cleanup. (The empty-name-disables-Generate and
        fresh-valid-name-enables-Generate observables are already asserted by
        test_create_personal_token_and_verify_in_table's Step 2/Step 3 — not
        repeated here.)"""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = tokens_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to the New Token form via the add-token button"
            ):
                tokens_page.navigate()
                tokens_page.click_add_button()
                create_page.wait_for_loaded()

            with allure.step(
                "Step 2 — Enter a name with special characters; verify the "
                "validation error is shown and Generate stays disabled"
            ):
                create_page.type_name("my token!@#")
                assert create_page.name_input.input_value() == "my token!@#", (
                    f"Expected Name input to show 'my token!@#', "
                    f"got {create_page.name_input.input_value()!r}"
                )
                expect(create_page.name_error).to_have_text(
                    "Only alphanumeric characters, underscore and hyphen are allowed"
                )
                assert create_page.generate_button.is_disabled(), (
                    "Expected Generate disabled for a name with special characters"
                )

            with allure.step(
                "Step 3 — Replace with a name containing only a space; verify the "
                "same validation error and Generate stays disabled"
            ):
                create_page.clear_and_type_name("my token")
                assert create_page.name_input.input_value() == "my token", (
                    f"Expected Name input to show 'my token', "
                    f"got {create_page.name_input.input_value()!r}"
                )
                expect(create_page.name_error).to_have_text(
                    "Only alphanumeric characters, underscore and hyphen are allowed"
                )
                assert create_page.generate_button.is_disabled(), (
                    "Expected Generate disabled for a name containing a space"
                )

            with allure.step(
                "Step 4 — Replace with a conforming name; verify the validation "
                "error clears and Generate becomes enabled"
            ):
                create_page.clear_and_type_name("my_token-123")
                expect(create_page.name_error).to_have_count(0)
                assert create_page.generate_button.is_enabled(), (
                    "Expected Generate enabled once the name only uses allowed characters"
                )

            with allure.step("Step 5 — Verify no console errors across the flow"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
