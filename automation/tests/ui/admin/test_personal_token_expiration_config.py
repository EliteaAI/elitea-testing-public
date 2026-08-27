"""UI test — Token expiration period unit and value can be configured.

Creates one real personal token with a NON-DEFAULT expiration (`Days` / `7`)
and deletes it in a mandatory cleanup step regardless of outcome — the merged
ELITEA-2280 test only ever exercises the form's defaults (`Days` / `30`), so
nothing about a *configured* expiration is covered today.

⚠️ Case-text drift, deliberately asserted against the LIVE contract (issue
#1882): the case's step 6 demands a "green ✅ icon" at 7 days. `ExpiryInDays.jsx`
branches on a strict `expiryInDays > 7` for the green `active` state, and
`calculateExpiryInDays` rounds to whole days — so a `Days`/`7` token lands in the
AMBER `warning` branch by design, with the label "in 7 days". Asserting "green"
here would fail a correct product (reverse masking, `.agents/testing.md`
§ reverse-masking guard), so this test asserts `warning` and pins the boundary
with an absence assertion on `active`. The clarification is filed as #1882; it
is a case-text issue, NOT a product defect, so nothing here is soft-asserted.

The token NAME is supplied although the case text never mentions one: Generate
stays disabled until a valid non-empty name is entered, so a name is a
precondition of the case's own step 5, not an added scenario. It is
uuid4-suffixed because duplicate names are legal on this surface (ELITEA-2288),
so a literal name would collide with any leftover from a failed run.

Test case: ELITEA-2282
AFS: test-specs/settings-personal-tokens/l3_token-expiration-period-unit-and-value_ELITEA-2282.md
"""

import logging
import uuid
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import allure
import pytest
from pages.create_personal_token_page import CreatePersonalTokenPage
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
EXPIRATION_DAYS = 7
# The app's own closed set (`EXPIRATION_MEASURES`, src/common/constants.js) —
# value -> rendered label, in rendered order.
EXPECTED_MEASURE_OPTIONS = [
    ("never", "Never"),
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("hours", "Hours"),
    ("minutes", "Minutes"),
]


class TestPersonalTokenExpirationConfig:
    """ELITEA-2282 — Token expiration period unit and value can be configured."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2282_token-expiration-period-unit-and-value-can-be-configured.md",
        "onetest-ai Test Case link",
    )
    def test_token_expiration_unit_and_value_can_be_configured(self, page):
        """The Expiration period is a unit dropdown (five `EXPIRATION_MEASURES`
        options) plus a numeric value input; selecting `Days` / `7` flows
        through to a create POST whose `expires` is ~7 days out, and the table
        renders the amber `warning` state with the label "in 7 days"."""
        tokens_page = PersonalTokensPage(page)
        create_page = CreatePersonalTokenPage(page)
        console_errors = collect_console_errors(page)
        token_name = f"autotest-token-{uuid.uuid4().hex[:8]}"

        try:
            with allure.step(
                'Step 1 — Navigate to Settings -> Personal Tokens and click "+"'
            ):
                tokens_page.navigate()
                tokens_page.click_add_button()
                create_page.wait_for_loaded()
                expect(create_page.page_title).to_have_text("New Token")

            with allure.step(
                "Step 2 — Verify the Expiration period field has two parts: a unit "
                "dropdown (default Days) and a numeric value input (default 30)"
            ):
                expect(create_page.expiration_measure_combobox).to_be_visible()
                expect(create_page.expiration_measure_combobox).to_have_text("Days")
                expect(create_page.expiration_value_input).to_be_visible()
                assert create_page.get_expiration_value() == "30", (
                    f"Expected the default expiration value '30', "
                    f"got {create_page.get_expiration_value()!r}"
                )
                # "numeric value input" is the case's own wording — visibility
                # alone would also pass for a plain text box.
                expect(create_page.expiration_value_input).to_have_attribute(
                    "type", "number"
                )

            with allure.step(
                "Step 3 — Open the unit dropdown; verify Never, Days, Weeks, Hours "
                "and Minutes are offered, and that they are the ONLY options"
            ):
                create_page.open_expiration_measure_dropdown()
                for measure, label in EXPECTED_MEASURE_OPTIONS:
                    option = create_page.get_expiration_measure_option(measure)
                    expect(option).to_have_count(1)
                    expect(option).to_have_text(label)
                # The case says "at least", but the product's set is closed
                # (`EXPIRATION_MEASURES`) — a sixth option would be an unreviewed
                # unit that "at least" silently tolerates.
                assert create_page.get_expiration_measure_option_count() == len(
                    EXPECTED_MEASURE_OPTIONS
                ), (
                    f"Expected exactly {len(EXPECTED_MEASURE_OPTIONS)} expiration-unit "
                    f"options, got {create_page.get_expiration_measure_option_count()}"
                )

            with allure.step('Step 4 — Select "Days" and enter the value "7"'):
                create_page.get_expiration_measure_option("days").click()
                expect(create_page.expiration_measure_combobox).to_have_text("Days")
                create_page.fill_expiration_value(str(EXPIRATION_DAYS))
                assert create_page.get_expiration_value() == str(EXPIRATION_DAYS), (
                    f"Expected the expiration value {EXPIRATION_DAYS!r}, "
                    f"got {create_page.get_expiration_value()!r}"
                )
                create_page.fill_name(token_name)

            with allure.step(
                'Step 5 — Click "Generate"; verify the create POST returns 200 with '
                "an expiry ~7 days out, then close the dialog"
            ):
                response = create_page.click_generate()
                assert response.status == 200, (
                    f"Expected 200 from the token-create POST, got {response.status}"
                )
                body = response.json()
                assert body.get("expires"), (
                    f"Expected a non-empty 'expires' in the create response, got {body!r}"
                )
                expires_at = parsedate_to_datetime(body["expires"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=UTC)
                remaining_days = (
                    expires_at - datetime.now(UTC)
                ).total_seconds() / 86_400
                assert EXPIRATION_DAYS - 1 <= remaining_days <= EXPIRATION_DAYS + 1, (
                    f"Expected the backend's expiry to be ~{EXPIRATION_DAYS} days out, "
                    f"got {remaining_days:.2f} days ({body['expires']!r})"
                )
                expect(create_page.dialog_title).to_have_text("New token generated!")
                expect(create_page.dialog_token_name).to_have_text(token_name)
                create_page.close_dialog()

            with allure.step(
                "Step 6 — Verify the Expiration column shows the configured period: "
                'the label "in 7 days" and the amber warning state'
            ):
                row = tokens_page.get_row_by_name(token_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                # Case-text drift: the case says "green" at exactly 7 days; the
                # product's `> 7` threshold makes 7 days amber by design.
                # Clarification: issue #1882 (case text, not a product defect).
                warning_status = tokens_page.get_row_expiration_status(row, state="warning")
                expect(warning_status).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(warning_status).to_have_text(f"in {EXPIRATION_DAYS} days")
                # Absence assertion pinning the boundary #1882 is about.
                expect(
                    tokens_page.get_row_expiration_status(row, state="active")
                ).to_have_count(0)

            with allure.step("Step 7 — Verify no console errors across the flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Cleanup (not an AFS case step) — mandatory, unwrapped: this case
            # creates a real, persistent token in shared live project data.
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
