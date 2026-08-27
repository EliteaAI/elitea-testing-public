"""UI test — a secret name must be unique within the project.

Creates ONE run-unique secret, then attempts to create a second one with the
SAME name and a DIFFERENT value. Verifies the product rejects the duplicate
server-side (create POST -> 400), surfaces an error toast naming the secret, and
leaves exactly one secret with that name — still holding its ORIGINAL value
(so a silent overwrite, which "no duplicate created" alone would not catch,
fails this test).

Never collides on a real project secret: typing a live secret's name into a
create form and depending on shared data that another run may delete is both a
data-safety and a determinism hazard.

Uniqueness is enforced SERVER-side only — the Save (✓) button stays enabled and
no inline error renders for a duplicate name. That is asserted deliberately, so
nobody later "repairs" this test toward a client-side validation the product
does not implement.

No substitution of the system under test: no route interception, no fabricated
response, no injected state.

Test case: ELITEA-2341
AFS: test-specs/settings-secrets/l2_secret-name-must-be-unique-within-project_ELITEA-2341.md

Known defect (EliteaAI/elitea-testing-public#1203): React "Maximum update depth
exceeded" on every `/settings/secrets` mount — isolated soft failure at the end
of the flow, sanctioned-RED per `.agents/testing.md` § Merge gate.
"""

import logging
import uuid

import allure
import pytest
from config import settings
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
#: The error toast auto-hides after 10s (TOAST_DURATION_DEFAULTS.error).
TOAST_TIMEOUT = 10_000
SECRETS_CREATE_URL_SUBSTRING = "/secrets/secrets/default/"


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


def _is_expected_duplicate_rejection(text: str) -> bool:
    """True for the browser's own log line for THIS test's expected 400.

    The duplicate create is *supposed* to be rejected, and Chromium logs every
    failed request as a console error. Filtered by URL + status (never by status
    alone, and never blanket) so a genuinely new console error still hard-fails.
    """
    return "400" in text and SECRETS_CREATE_URL_SUBSTRING in text


class TestSecretNameUniquenessWithinProject:
    """ELITEA-2341 — creating a second secret with an existing name is rejected
    (400 + error toast) and leaves the original secret untouched."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2341_secret-name-must-be-unique-within-the-project.md",
        "onetest-ai Test Case link",
    )
    def test_duplicate_secret_name_is_rejected_and_original_is_untouched(self, page, api):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []
        run_id = uuid.uuid4().hex[:8]
        secret_name = f"autotest_unique_{run_id}"
        original_value = f"unique-original-{run_id}"
        duplicate_value = f"unique-duplicate-{run_id}"
        created = False

        try:
            with allure.step("Step 1 — Navigate to Settings -> Secrets; verify the page title"):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got "
                    f"{secrets_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Step 2 — Establish the 'existing secret' whose name will be reused: "
                "create a run-unique secret; verify 201 Created and one matching row"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, original_value)
                create_response = secrets_page.click_save_button()
                assert create_response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {create_response.status}"
                )
                created = True
                secrets_page.type_search(secret_name)
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    1, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Click '+' and enter the SAME name (with a different value) in "
                "the new inline row; verify the product applies NO client-side "
                "uniqueness check (Save enabled, no inline error) — uniqueness is a "
                "server-side contract on this surface"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, duplicate_value)
                expect(secrets_page.name_input).to_have_value(
                    secret_name, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.value_input).to_have_value(
                    duplicate_value, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.save_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)
                expect(secrets_page.name_error).to_have_count(0, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 4 — Click the checkmark to save; verify the create POST is "
                "REJECTED with 400 Bad Request"
            ):
                duplicate_response = secrets_page.click_save_button_expect_rejection()
                assert duplicate_response.status == 400, (
                    "Expected 400 Bad Request from the duplicate-name create POST, got "
                    f"{duplicate_response.status}"
                )

            with allure.step(
                "Step 5 — Verify a validation error is shown: an error-severity toast "
                "naming the conflicting secret"
            ):
                expect(secrets_page.toast_alert_with_severity("error")).to_be_visible(
                    timeout=TOAST_TIMEOUT
                )
                expect(secrets_page.toast_message).to_have_text(
                    f'Secret "{secret_name}" already exists', timeout=TOAST_TIMEOUT
                )

            with allure.step(
                "Step 6 (beyond the case) — Verify the rejected row survives in edit "
                "mode with the typed name intact (a rejected save must not destroy the "
                "user's input)"
            ):
                expect(secrets_page.name_input).to_have_value(
                    secret_name, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Discard the rejected row and verify NO duplicate secret was "
                "created: exactly one row carries that name, and it survives a reload "
                "(a genuine server round-trip, not a client-cache read)"
            ):
                secrets_page.click_cancel_button()
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    1, timeout=ROW_WAIT_TIMEOUT
                )
                secrets_page.reload_and_wait()
                secrets_page.type_search(secret_name)
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 8 (beyond the case) — Verify the surviving secret still holds its "
                "ORIGINAL value: 'no duplicate created' would also be satisfied by a "
                "silent overwrite, which this distinguishes"
            ):
                reveal_response = secrets_page.reveal_secret_value(row)
                assert reveal_response.status == 200, (
                    f"Expected 200 from the reveal GET, got {reveal_response.status}"
                )
                revealed_value = reveal_response.json()["value"]
                assert revealed_value == original_value, (
                    "Expected the surviving secret to still hold its ORIGINAL value "
                    "after the rejected duplicate create (a silent overwrite would show "
                    f"the duplicate's value); got {revealed_value!r}"
                )
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    original_value, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 9 — Verify no UNEXPECTED console errors across the flow. This "
                "test's own expected 400 is filtered by URL + status (never blanket), "
                "and Known defect EliteaAI/elitea-testing-public#1203 is soft-asserted "
                "— a genuinely NEW console error still hard-fails here"
            ):
                unexpected_errors = [
                    e
                    for e in console_errors
                    if not _is_known_defect_1203(e) and not _is_expected_duplicate_rejection(e)
                ]
                assert not unexpected_errors, (
                    f"Unexpected console errors: {unexpected_errors}"
                )
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
        finally:
            # Cleanup (not a case step) — the case's own steps never delete the
            # secret they establish, so teardown must, via the same endpoint the
            # UI's delete flow calls.
            if created:
                delete_response = api.delete(
                    f"/secrets/secret/default/{settings.elitea_project_id}/{secret_name}"
                )
                assert delete_response.status_code == 204, (
                    f"Cleanup failed: expected 204 deleting {secret_name!r}, got "
                    f"{delete_response.status_code} {delete_response.text}"
                )
