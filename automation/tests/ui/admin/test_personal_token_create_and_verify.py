"""UI tests — Settings -> Personal Tokens: expiration icons and token-name validation.

Covers ELITEA-2284 ("Expired tokens show a gray icon and active tokens
show a green icon with remaining days") —
`test_expired_token_shows_expired_icon_and_label` covers the expired-token
steps 2-3 (expired token -> gray icon + "Expired" label), read-only against
existing live data.
AFS: test-specs/settings-personal-tokens/lextend_expired-and-active-token-expiration-icons_ELITEA-2284.md

Covers ELITEA-2286 ("Token name validation — only alphanumeric
characters, underscores, and hyphens are allowed") —
`test_invalid_token_name_shows_error_and_keeps_generate_disabled` verifies
an invalid name (special characters or a space) shows the validation error
and keeps Generate disabled, and replacing it with a conforming name clears
the error and re-enables Generate. Read-only against the create-token
FORM: never clicks Generate, creates no token, needs no cleanup.
AFS: test-specs/settings-personal-tokens/lextend_token-name-validation-invalid-characters-rejected_ELITEA-2286.md
"""

import logging

import allure
import pytest
from pages.create_personal_token_page import CreatePersonalTokenPage
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

ROW_WAIT_TIMEOUT = 15_000


class TestPersonalTokenCreateAndVerify:
    """Personal Tokens table/form checks (ELITEA-2284, ELITEA-2286)."""

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
        or deleted."""
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
        cleanup."""
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
