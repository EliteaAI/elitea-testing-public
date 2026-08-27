"""UI test — the new-secret Name field is required: Save must be gated when empty.

Drives the inline "+" create row with an EMPTY name and a filled value, and
asserts the case's own expectation — Save (✓) disabled **or** an inline
validation error shown. The live product satisfies NEITHER (filed as
EliteaAI/elitea-testing-public#1903), so that assertion is recorded as an
isolated soft failure with the correct expected behaviour left intact: it flips
green the moment the product enforces the requirement via either branch.

Nothing is ever saved — the row is always cancelled, so no secret is created
and no teardown is needed. Clicking Save with an empty name is deliberately NOT
exercised: `useSecretRowUpdate` drops the row only when name AND value are both
empty, so with a value present it would POST `name: ""` into shared live project
data and could leave an unnamed secret with no deletable URL path.

No substitution of the system under test: no route interception, no fabricated
response, no injected state.

Test case: ELITEA-2340
AFS: test-specs/settings-secrets/l3_secret-name-required-save-disabled-when-empty_ELITEA-2340.md

Known defects:
- EliteaAI/elitea-testing-public#1903 — Save stays enabled with an empty name,
  no inline error (the case's step 3). Soft-asserted below.
- EliteaAI/elitea-testing-public#1203 — React "Maximum update depth exceeded"
  on every `/settings/secrets` mount. Soft-asserted at the end of the flow.

Both make this spec sanctioned-RED per `.agents/testing.md` § Merge gate.
"""

import logging
import uuid

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
SECRETS_CREATE_URL_SUBSTRING = "/secrets/secrets/default/"


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


class TestSecretNameRequiredWhenEmpty:
    """ELITEA-2340 — an empty secret name must gate the Save (✓) control, and a
    valid name must enable it."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2340_secret-name-is-required-save-disabled-when-name-is-empty.md",
        "onetest-ai Test Case link",
    )
    def test_empty_secret_name_gates_save_and_valid_name_enables_it(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []
        run_id = uuid.uuid4().hex[:8]
        valid_name = f"autotest_required_{run_id}"
        secret_value = f"name-required-value-{run_id}"

        # Passive listener (never an intercept): the consequential half of the
        # defect is whether an empty name can reach the server at all.
        create_requests: list[str] = []
        page.on(
            "request",
            lambda request: (
                create_requests.append(request.url)
                if request.method == "POST" and SECRETS_CREATE_URL_SUBSTRING in request.url
                else None
            ),
        )

        with allure.step("Step 1 — Navigate to Settings -> Secrets and click '+'"):
            secrets_page.navigate()
            assert secrets_page.page_title.text_content() == "Secrets", (
                f"Expected page title 'Secrets', got "
                f"{secrets_page.page_title.text_content()!r}"
            )
            secrets_page.click_add_button()
            expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            "Step 2 — Leave the Name field empty and fill the Value field; verify "
            "the row really is in that state before asserting on it"
        ):
            secrets_page.type_value(secret_value)
            expect(secrets_page.name_input).to_have_value("", timeout=ROW_WAIT_TIMEOUT)
            expect(secrets_page.value_input).to_have_value(
                secret_value, timeout=ROW_WAIT_TIMEOUT
            )

        with allure.step(
            "Step 3 — Verify the Save button is disabled OR an inline validation error "
            "is shown (Known defect EliteaAI/elitea-testing-public#1903 — the live "
            "product does neither; soft-asserted so the correct expectation stays in "
            "the suite and flips green when the fix ships)"
        ):
            save_disabled = secrets_page.save_button.is_disabled()
            name_error_visible = secrets_page.name_error.count() > 0
            if not (save_disabled or name_error_visible):
                # Known defect: EliteaAI/elitea-testing-public#1903
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1903: "
                    "with an EMPTY name and a filled value the Save (checkmark) button is "
                    f"enabled (disabled={save_disabled}) and no inline name-validation "
                    f"error is shown (secret-name-error count="
                    f"{secrets_page.name_error.count()}), although the field is marked "
                    "required — the case expects one or the other"
                )

            # Honest today, and the bigger risk: an empty name must not reach the
            # server while the row sits in this state.
            assert not create_requests, (
                "Expected NO create POST to fire while the name is empty, but observed: "
                f"{create_requests}"
            )

        with allure.step(
            "Step 4 — Enter a valid name; verify it is accepted with no inline error"
        ):
            secrets_page.type_name(valid_name)
            expect(secrets_page.name_input).to_have_value(
                valid_name, timeout=ROW_WAIT_TIMEOUT
            )
            expect(secrets_page.name_error).to_have_count(0, timeout=ROW_WAIT_TIMEOUT)

        with allure.step("Step 5 — Verify the Save button is enabled"):
            expect(secrets_page.save_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            "Step 6 (beyond the case) — Cancel the row; verify it is discarded with no "
            "network call, so this case persists nothing into the shared project"
        ):
            secrets_page.click_cancel_button()
            expect(secrets_page.name_input).to_have_count(0, timeout=ROW_WAIT_TIMEOUT)
            assert not create_requests, (
                "Expected NO create POST across the whole flow (the case never saves), "
                f"but observed: {create_requests}"
            )

        with allure.step(
            "Step 7 — Verify no UNEXPECTED console errors across the flow "
            "(Known defect EliteaAI/elitea-testing-public#1203 — soft-asserted, "
            "isolated, filtered by exact signature so a genuinely NEW console error "
            "still hard-fails here)"
        ):
            unexpected_errors = [e for e in console_errors if not _is_known_defect_1203(e)]
            assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"
            known_defect_errors = [e for e in console_errors if _is_known_defect_1203(e)]
            if known_defect_errors:
                # Known defect: EliteaAI/elitea-testing-public#1203
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1203: "
                    f"React 'Maximum update depth exceeded' console error(s) on "
                    f"/settings/secrets mount: {len(known_defect_errors)} occurrence(s)"
                )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
