"""UI test — Delete a secret via the row's three-dot menu and verify removal.

Creates ONE run-unique secret via the existing inline "+" flow (reused
verbatim from ELITEA-2336) and deletes THAT one via the row's three-dot
("more actions") menu → Delete → shared type-to-confirm modal. Never targets
a pre-existing/real secret (the project has 100+ live secrets; deleting one
would corrupt shared test data — also sidesteps the `isDefault` prop that
disables all three menu items for system/default secrets). No separate
cleanup step needed — the case's own steps 6-8 delete the generated secret
as part of the test flow itself.

Test case: ELITEA-2338
AFS: test-specs/settings-secrets/l3_delete-secret-via-three-dot-menu_ELITEA-2338.md

Known defect (EliteaAI/elitea-testing-public#1203): `/settings/secrets` may
fire a React "Maximum update depth exceeded" console warning on mount
(isolated to `SecretsContent.jsx`, does not affect functional behaviour).
Confirmed deterministic 3/3 in ELITEA-2336's own automated run but NOT
observed in either ELITEA-2336's or ELITEA-2337's own live analyst
exploration sessions — inconclusive whether a fresh automated run of THIS
case's own test reproduces it. Soft-asserted via the same
`soft_failures`/`pytest.fail()` idiom as the covering
`test_secret_create_inline_checkmark_x_cancel.py` so this assertion stays
isolated: an UNEXPECTED console error (any text other than this known
signature) still hard-fails immediately.
"""

import logging
import uuid

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SECRET_VALUE = "delete-test-value-123"
ROW_WAIT_TIMEOUT = 15_000
EXPECTED_MENU_ITEM_TEXTS = ["Edit value", "Hide", "Delete"]


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console warning (EliteaAI/
    elitea-testing-public#1203) — a React "Maximum update depth exceeded"
    warning that may fire on a `/settings/secrets` mount.

    Matches on the STABLE warning-text prefix alone (not a volatile
    component-stack suffix that may or may not be captured — see
    `test_secret_create_inline_checkmark_x_cancel.py`'s own matcher
    docstring for the full rationale)."""
    return "Maximum update depth exceeded" in text


class TestSecretDeleteViaThreeDotMenu:
    """ELITEA-2338 — the three-dot menu on a secret row opens a dropdown with
    exactly Edit value / Hide / Delete; Delete opens the shared
    type-to-confirm modal; confirming fires the DELETE endpoint and removes
    the secret from the table, both immediately and after a fresh reload."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2338_delete-secret-via-three-dot-menu.md",
        "onetest-ai Test Case link",
    )
    def test_delete_secret_via_three_dot_menu(self, page):
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()
        secret_name = f"autotest_delete_target_{uuid.uuid4().hex[:8]}"
        soft_failures: list[str] = []

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets; verify page title"
            ):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got {secrets_page.page_title.text_content()!r}"
                )
                pagination_baseline = secrets_page.get_pagination_text()

            with allure.step(
                "Step 2 — Create a run-unique secret via the inline '+' flow; "
                "verify the create POST resolves 201 Created"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, SECRET_VALUE)
                response = secrets_page.click_save_button()
                assert response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {response.status}"
                )
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 3 — Click the three-dot ('more actions') button on the "
                "created secret's row; verify the actions dropdown opens"
            ):
                secrets_page.open_row_actions_menu(row)

            with allure.step(
                "Step 4 — Verify the dropdown shows exactly three items, in "
                "order: 'Edit value', 'Hide', 'Delete'"
            ):
                item_texts = secrets_page.get_actions_menu_item_texts()
                assert item_texts == EXPECTED_MENU_ITEM_TEXTS, (
                    f"Expected actions-menu items {EXPECTED_MENU_ITEM_TEXTS!r} in "
                    f"order, got {item_texts!r}"
                )

            with allure.step(
                "Step 5 — Click 'Delete'; verify a confirmation dialog appears "
                "with the exact type-to-confirm copy, and the Delete button is "
                "disabled before typing the secret's name"
            ):
                secrets_page.click_delete_menu_item()
                expected_message = (
                    f"Are you sure to delete the {secret_name}? "
                    "Enter the name to complete the action."
                )
                assert secrets_page.delete_confirm_message.text_content() == expected_message, (
                    f"Expected delete-confirm message {expected_message!r}, got "
                    f"{secrets_page.delete_confirm_message.text_content()!r}"
                )
                expect(secrets_page.delete_confirm_button).to_be_disabled(
                    timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Type the exact secret name to enable Delete, confirm "
                "deletion; verify the DELETE request resolves 204 No Content"
            ):
                secrets_page.fill_delete_confirm_name(secret_name)
                delete_response = secrets_page.confirm_delete()
                assert delete_response.status == 204, (
                    f"Expected 204 from the secret-delete DELETE, got "
                    f"{delete_response.status}"
                )

            with allure.step(
                "Step 7 — Verify the secret is removed from the table: row "
                "count drops to 0, and the unfiltered pagination total returns "
                "to the pre-create baseline"
            ):
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
                # Polling assertion (not a one-shot read): the DELETE's list
                # refetch and the pagination-total recompute can land in two
                # separate renders, so a raw text_content() read can catch a
                # transient stale total between them.
                expect(secrets_page.pagination_info).to_have_text(
                    pagination_baseline, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Reload the page; verify the deleted secret still "
                "does not reappear (genuine server round-trip, not a "
                "DOM/client-cache-only check)"
            ):
                secrets_page.reload_and_wait()
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 9 — Verify no UNEXPECTED console errors across the flow "
                "(Known defect EliteaAI/elitea-testing-public#1203 — "
                "soft-asserted, isolated, filtered by exact signature so a "
                "genuinely NEW console error still hard-fails here)"
            ):
                unexpected_errors = [
                    m.text for m in console_errors if not _is_known_defect_1203(m.text)
                ]
                assert not unexpected_errors, (
                    f"Unexpected console errors: {unexpected_errors}"
                )
                known_defect_errors = [
                    m.text for m in console_errors if _is_known_defect_1203(m.text)
                ]
                if known_defect_errors:
                    # Known defect: EliteaAI/elitea-testing-public#1203 — recorded
                    # in soft_failures (real soft-assertion equivalent, see the
                    # pytest.fail() below) rather than only logged, so this stays
                    # a tracked, visible RED until the product fix ships —
                    # sanctioned-RED per .agents/testing.md § Merge gate.
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
            console_errors.stop()
            # No cleanup step needed beyond the flow itself — steps 6-8 above
            # ARE the deletion (this case's own steps delete the secret it
            # creates), unlike ELITEA-2336's save-flow secret which needed a
            # separate API-delete teardown because its own case never deletes
            # it. Per the AFS § Cleanup.
