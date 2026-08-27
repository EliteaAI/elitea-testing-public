"""UI test — cancelling the delete confirmation keeps the secret intact.

Creates ONE run-unique secret via the existing inline "+" flow, opens its
three-dot menu -> Delete, then clicks **Cancel** in the shared type-to-confirm
modal and verifies the secret survives unchanged — in the table, on the wire
(no DELETE request is issued at all), and after a full page reload.

Never targets a pre-existing/real secret: all three menu items are
`disabled={isDefault}` for system secrets, and a mis-step on a real one would
corrupt shared project data (the project holds 120+ live secrets).

No substitution of the system under test: no route interception, no fabricated
response, no injected state. The DELETE-absence check is a passive request
listener, not an intercept.

Test case: ELITEA-2339
AFS: test-specs/settings-secrets/l2_cancel-deletion-keeps-secret-intact_ELITEA-2339.md

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
EXPECTED_MENU_ITEM_TEXTS = ["Edit value", "Hide", "Delete"]
SECRET_DELETE_URL_SUBSTRING = "/secrets/secret/default/"


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


class TestSecretCancelDeletionKeepsSecret:
    """ELITEA-2339 — Delete opens the confirmation modal; Cancel closes it
    without issuing a DELETE, and the secret remains in the table unchanged."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2339_cancel-deletion-keeps-the-secret-intact.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_deletion_keeps_secret_intact(self, page, api):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []
        run_id = uuid.uuid4().hex[:8]
        secret_name = f"autotest_cancel_del_{run_id}"
        secret_value = f"cancel-delete-value-{run_id}"
        masked_reference = f"{{{{secret.{secret_name}}}}}"
        created = False

        # Passive listener (never an intercept): "the secret is intact" is a claim
        # about the SYSTEM, and the DOM alone cannot distinguish "nothing was
        # deleted" from "deleted, list not refetched yet".
        delete_requests: list[str] = []
        page.on(
            "request",
            lambda request: (
                delete_requests.append(request.url)
                if request.method == "DELETE" and SECRET_DELETE_URL_SUBSTRING in request.url
                else None
            ),
        )

        try:
            with allure.step("Step 1 — Navigate to Settings -> Secrets; verify the page title"):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got "
                    f"{secrets_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Setup (not a case step) — create a run-unique secret via the inline "
                "'+' flow; verify 201 Created and that its row renders"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, secret_value)
                create_response = secrets_page.click_save_button()
                assert create_response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {create_response.status}"
                )
                created = True
                secrets_page.type_search(secret_name)
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 2 — Open the row's three-dot menu and click Delete; verify the "
                "dropdown offers exactly Edit value / Hide / Delete, in order"
            ):
                secrets_page.open_row_actions_menu(row)
                item_texts = secrets_page.get_actions_menu_item_texts()
                assert item_texts == EXPECTED_MENU_ITEM_TEXTS, (
                    f"Expected actions-menu items {EXPECTED_MENU_ITEM_TEXTS!r} in order, "
                    f"got {item_texts!r}"
                )
                secrets_page.click_delete_menu_item()

            with allure.step(
                "Step 3 — Verify the confirmation dialog appears, names THIS secret, "
                "and keeps its Delete button disabled before anything is typed"
            ):
                expect(secrets_page.delete_confirm_dialog).to_be_visible(
                    timeout=ROW_WAIT_TIMEOUT
                )
                expected_message = (
                    f"Are you sure to delete the {secret_name}? "
                    "Enter the name to complete the action."
                )
                expect(secrets_page.delete_confirm_message).to_have_text(
                    expected_message, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.delete_confirm_button).to_be_disabled(
                    timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Click Cancel; verify the dialog closes and NO DELETE request "
                "is issued (the cancel is purely client-side)"
            ):
                secrets_page.cancel_delete()
                assert not delete_requests, (
                    "Expected cancelling the delete confirmation to issue NO DELETE "
                    f"request, but observed: {delete_requests}"
                )

            with allure.step(
                "Step 5 — Verify the secret remains in the table UNCHANGED: row still "
                "present, name and masked value identical"
            ):
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(secrets_page.get_row_name_cell(row)).to_have_text(
                    secret_name, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    masked_reference, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 6 (beyond the case) — Reload the page and re-assert the secret is "
                "still there, unchanged: a genuine server round-trip, so a "
                "client-cache-only survival cannot pass"
            ):
                secrets_page.reload_and_wait()
                secrets_page.type_search(secret_name)
                reloaded_row = secrets_page.get_row_by_name(secret_name)
                expect(reloaded_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(secrets_page.get_row_value_cell(reloaded_row)).to_have_text(
                    masked_reference, timeout=ROW_WAIT_TIMEOUT
                )
                assert not delete_requests, (
                    "Expected NO DELETE request across the whole flow, but observed: "
                    f"{delete_requests}"
                )

            with allure.step(
                "Step 7 — Verify no UNEXPECTED console errors across the flow "
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
            # Cleanup (not a case step) — this case's whole point is that its own
            # steps do NOT delete the secret, so teardown must, via the same
            # endpoint the UI's delete flow calls.
            if created:
                delete_response = api.delete(
                    f"/secrets/secret/default/{settings.elitea_project_id}/{secret_name}"
                )
                assert delete_response.status_code == 204, (
                    f"Cleanup failed: expected 204 deleting {secret_name!r}, got "
                    f"{delete_response.status_code} {delete_response.text}"
                )
