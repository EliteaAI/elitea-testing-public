"""UI test — clicking a masked secret value copies the real value to the clipboard.

Creates ONE run-unique secret via the existing inline "+" flow, clicks its
masked `{{secret.<name>}}` value cell, and verifies the clipboard holds the
PLAINTEXT (never the masked reference). The clipboard content is checked
against two independent system-produced oracles: the value the create POST
persisted, and the `value` field of the reveal GET the click itself fires.

Never targets a pre-existing/real secret: the case's step 6 requires knowing
what "the actual secret value" is, and reading a live shared secret's plaintext
into a test process (and into a failure message) is both a data-safety and a
correctness hazard.

No substitution of the system under test: no route interception, no fabricated
response, no injected state. `clear_clipboard()` before the click is
precondition hygiene (it removes a stale value so a passing read cannot be a
false positive) — the asserted value is written by the product.

Test case: ELITEA-2335
AFS: test-specs/settings-secrets/l3_secret-value-click-copies-to-clipboard_ELITEA-2335.md

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

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
#: The info toast auto-hides after 3s (TOAST_DURATION_DEFAULTS.info) — every
#: toast assertion is a web-first expect() attached immediately after the click.
TOAST_TIMEOUT = 10_000


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


class TestSecretValueClickCopiesToClipboard:
    """ELITEA-2335 — clicking the masked value copies the real secret value to
    the clipboard, shows the copy confirmation toast, and leaves the cell masked."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2335_clicking-the-masked-secret-value-copies-it-to-clipboard.md",
        "onetest-ai Test Case link",
    )
    def test_clicking_masked_value_copies_real_value_to_clipboard(self, page, api):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []
        run_id = uuid.uuid4().hex[:8]
        secret_name = f"autotest_copy_{run_id}"
        secret_value = f"copy-test-value-{run_id}"
        masked_reference = f"{{{{secret.{secret_name}}}}}"
        created = False

        try:
            with allure.step("Step 1 — Navigate to Settings -> Secrets; verify the page title"):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got "
                    f"{secrets_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Setup (not a case step) — create a run-unique secret via the inline "
                "'+' flow so the case's 'actual secret value' is known; verify 201 Created"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, secret_value)
                create_response = secrets_page.click_save_button()
                assert create_response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {create_response.status}"
                )
                created = True

            with allure.step(
                "Step 2 — Locate the secret's row and verify its Value column shows "
                "the masked {{secret.<name>}} reference"
            ):
                secrets_page.type_search(secret_name)
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    masked_reference, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Click the masked value text; verify the reveal GET resolves 200 "
                "(its response body is the system's own oracle for the clipboard content)"
            ):
                # Precondition hygiene, NOT substitution: a stale clipboard entry
                # must not be readable as a fresh copy. The asserted value below is
                # written by the product.
                secrets_page.clear_clipboard()
                reveal_response = secrets_page.copy_secret_value(row)
                assert reveal_response.status == 200, (
                    f"Expected 200 from the reveal GET fired by the copy click, got "
                    f"{reveal_response.status}"
                )

            with allure.step(
                "Step 4 — Verify the copy-confirmation toast appears (info severity, "
                "exact text)"
            ):
                expect(secrets_page.toast_alert_with_severity("info")).to_be_visible(
                    timeout=TOAST_TIMEOUT
                )
                expect(secrets_page.toast_message).to_have_text(
                    f"The {secret_name} values have been copied.", timeout=TOAST_TIMEOUT
                )

            with allure.step(
                "Steps 5-6 — Read the clipboard back (the automation equivalent of "
                "pasting) and verify it holds the ACTUAL secret value, not the masked "
                "reference — cross-checked against both system-produced oracles"
            ):
                clipboard_text = secrets_page.get_clipboard_text()
                server_value = reveal_response.json()["value"]
                assert clipboard_text == secret_value, (
                    "Expected the clipboard to hold the secret's real value after the "
                    f"copy click, got {clipboard_text!r}"
                )
                assert clipboard_text == server_value, (
                    "Expected the clipboard to hold exactly what the server returned "
                    f"for this secret; clipboard={clipboard_text!r}, "
                    f"server value={server_value!r}"
                )
                assert clipboard_text != masked_reference, (
                    "Expected the clipboard to hold the plaintext, NOT the masked "
                    f"reference {masked_reference!r}"
                )

            with allure.step(
                "Step 7 (beyond the case) — Verify the Value cell is still MASKED after "
                "the copy: copying must not double as revealing"
            ):
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    masked_reference, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Verify no UNEXPECTED console errors across the flow "
                "(Known defect EliteaAI/elitea-testing-public#1203 — soft-asserted, "
                "isolated, filtered by exact signature so a genuinely NEW console "
                "error still hard-fails here)"
            ):
                unexpected_errors = [e for e in console_errors if not _is_known_defect_1203(e)]
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
            # Cleanup (not a case step) — this case's own steps never delete the
            # secret they create, so teardown must, via the same endpoint the UI's
            # delete flow calls.
            if created:
                delete_response = api.delete(
                    f"/secrets/secret/default/{settings.elitea_project_id}/{secret_name}"
                )
                assert delete_response.status_code == 204, (
                    f"Cleanup failed: expected 204 deleting {secret_name!r}, got "
                    f"{delete_response.status_code} {delete_response.text}"
                )
