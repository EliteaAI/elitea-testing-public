"""Test for Create Credential — Required Fields Validation.

Verifies the Create-Credential form's client-side Save-button gating on
required fields: Save stays disabled while any required field is empty,
enables once all required fields are filled, and (per the case's own
Pass/Fail criteria) should re-disable the instant any required field is
cleared.

Uses the Jira credential type — GitHub's Base Url field ships with a live
default value that would satisfy "all required fields filled" after Display
Name alone, contradicting Step 3's expected result (see AFS Preconditions
note). No credential is ever persisted — Save is never clicked.

Known defect (github.com/EliteaAI/elitea-testing-public#526): clearing the
Display Name field does not re-disable Save, unlike every other required
field (base_url / api_key / username), which correctly re-disable it. This
is asserted with ``expect.soft()`` per this project's no-masking policy —
the assertion stays RED until #526 is fixed.

Test case: ELITEA-1975
AFS: test-specs/toolkits-credentials/l1_create-credential-required-fields-validation_ELITEA-1975.md
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.credential_create_page import CredentialCreatePage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p0, pytest.mark.regression, pytest.mark.new]

DISPLAY_NAME = "autotest_reqfields_cred2"
BASE_URL_VALUE = "https://autotest2.atlassian.net"
API_KEY_VALUE = "dummy-api-key-value-2"
USERNAME_VALUE = "autotest2.user@example.com"


class TestCredentialRequiredFieldsValidation:
    """ELITEA-1975 — Create Credential form required-field Save-gating."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1975_create-credential-required-fields-validation.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/526", "Known defect #526")
    @pytest.mark.p0
    def test_create_credential_required_fields_validation(self, page):
        """Save reflects required-field state; Display Name clearing is a known defect."""
        create_page = CredentialCreatePage(page)

        with allure.step("Step 1 — Navigate to the credential creation form (Jira type)"):
            create_page.navigate_to_type("jira")
            expect(create_page.display_name_input).to_have_value("")
            expect(create_page.base_url_input).to_have_value("")
            expect(create_page.api_key_input).to_have_value("")
            expect(create_page.username_input).to_have_value("")

            # Console listener starts AFTER the list -> create-form navigation:
            # the /credentials/all type-selector grid (CredentialTypeSelector.jsx
            # / GroupedCategory.jsx) emits a pre-existing React "missing key prop"
            # dev warning on its own render, out of scope for this case's Save-
            # gating flow (Steps 2-5) — same scoping precedent as
            # test_credential_discard_changes.py's console listener placement.
            console_messages = []
            page.on(
                "console",
                lambda msg: console_messages.append(msg) if msg.type in ("error", "warning") else None,
            )

        with allure.step("Step 2 — Leave all fields empty: Save remains disabled"):
            expect(create_page.save_button).to_be_disabled()

        with allure.step("Step 3 — Fill only the Display Name field: Save remains disabled"):
            create_page.set_display_name(DISPLAY_NAME)
            expect(create_page.display_name_input).to_have_value(DISPLAY_NAME)
            expect(create_page.save_button).to_be_disabled()

        with allure.step(
            "Step 4 — Fill the other required fields (Base Url, Api Key, Username): Save becomes enabled"
        ):
            create_page.set_base_url(BASE_URL_VALUE)
            create_page.set_api_key(API_KEY_VALUE)
            create_page.set_username(USERNAME_VALUE)
            expect(create_page.save_button).to_be_enabled()

        with allure.step(
            "Step 5 — Clear the Display Name field: Save should become disabled again "
            "(Known defect: #526 — Save incorrectly stays enabled)"
        ):
            create_page.clear_display_name()
            expect(create_page.display_name_input).to_have_value("")
            # Known defect: #526 — Save does not re-disable when Display Name is
            # cleared, unlike every other required field. Soft assertion so the
            # rest of the test (control checks below) still runs; stays RED
            # until #526 ships a fix, per .agents/testing.md's no-masking policy.
            expect.soft(create_page.save_button).to_be_disabled()

        with allure.step(
            "Control check (Axis 2) — clearing Username instead re-disables Save correctly"
        ):
            create_page.set_display_name(DISPLAY_NAME)
            expect(create_page.display_name_input).to_have_value(DISPLAY_NAME)
            expect(create_page.save_button).to_be_enabled()

            create_page.clear_username()
            expect(create_page.username_input).to_have_value("")
            expect(create_page.save_button).to_be_disabled()

        with allure.step(
            "Control check (Axis 2) — clearing Base Url instead re-disables Save correctly"
        ):
            create_page.set_username(USERNAME_VALUE)
            expect(create_page.save_button).to_be_enabled()

            create_page.clear_base_url()
            expect(create_page.base_url_input).to_have_value("")
            expect(create_page.save_button).to_be_disabled()

        with allure.step("Side-channel check — no console errors/warnings across the flow"):
            assert not console_messages, (
                f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
            )
