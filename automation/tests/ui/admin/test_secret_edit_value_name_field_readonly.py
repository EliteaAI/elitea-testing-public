"""UI test — Edit secret value inline: the Name field is read-only after
creation.

Creates ONE run-unique secret via the existing inline "+" flow (reused
verbatim from ELITEA-2336), opens its row's three-dot ("more actions") menu
and clicks "Edit value" (reusing ELITEA-2338's declared-improvisation
`open_row_actions_menu()` workaround), verifies the Value column becomes an
EMPTY editable input while the Name column stays the SAME static-text cell
it shows in view mode (no Name input ever renders for an existing row),
saves a new value via the checkmark, and reveals it via the eye icon
(reusing ELITEA-2343's `reveal_secret_value()`) to prove server-side
persistence. Deletes the generated secret via the existing three-dot-menu
delete flow (reused verbatim from ELITEA-2338) as this case's own explicit
cleanup step.

Test case: ELITEA-2347
AFS: test-specs/settings-secrets/l3_edit-secret-value-name-field-readonly_ELITEA-2347.md

Known defect (EliteaAI/elitea-testing-public#1203): `/settings/secrets` may
fire a React "Maximum update depth exceeded" console warning on mount. NOT
observed during this case's own AFS exploration session (steps 1-8).
Soft-asserted via the same `soft_failures`/`pytest.fail()` idiom as every
sibling case in this feature so this assertion stays isolated: an
UNEXPECTED console error (any text other than this known signature) still
hard-fails immediately.
"""

import logging
import uuid

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ORIGINAL_VALUE = "original-value-123"
ROW_WAIT_TIMEOUT = 15_000
EXPECTED_MENU_ITEM_TEXTS = ["Edit value", "Hide", "Delete"]
SECRETS_LIST_URL_SUBSTRING = "/secrets/secrets/default/"


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console warning (EliteaAI/
    elitea-testing-public#1203) — a React "Maximum update depth exceeded"
    warning that may fire on a `/settings/secrets` mount.

    Matches on the STABLE warning-text prefix alone (not a volatile
    component-stack suffix that may or may not be captured — see
    `test_secret_create_inline_checkmark_x_cancel.py`'s own matcher
    docstring for the full rationale)."""
    return "Maximum update depth exceeded" in text


class TestSecretEditValueNameFieldReadonly:
    """ELITEA-2347 — editing an existing secret's value via the three-dot
    menu's "Edit value" opens the Value column as an EMPTY editable input
    while the Name column stays the same static-text cell it shows in view
    mode (no Name input ever renders for an existing row); saving persists
    via PUT and a fresh reveal proves server-side persistence, not just
    optimistic local state."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2347_edit-secret-value-inline-name-field-is-read-only-after-creat.md",
        "onetest-ai Test Case link",
    )
    def test_edit_secret_value_name_field_readonly(self, page):
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()
        secret_name = f"autotest_edit_{uuid.uuid4().hex[:8]}"
        new_value = f"updated-value-{uuid.uuid4().hex[:8]}"
        soft_failures: list[str] = []

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets; verify page title"
            ):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got {secrets_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Step 2 — Create a run-unique secret via the inline '+' flow; "
                "verify the create POST resolves 201 Created"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(secret_name, ORIGINAL_VALUE)
                response = secrets_page.click_save_button()
                assert response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {response.status}"
                )
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 3 — Click the three-dot ('more actions') button, then "
                "'Edit value'; verify the dropdown shows exactly 'Edit "
                "value'/'Hide'/'Delete' and the edit-open GET resolves 200 OK"
            ):
                secrets_page.open_row_actions_menu(row)
                item_texts = secrets_page.get_actions_menu_item_texts()
                assert item_texts == EXPECTED_MENU_ITEM_TEXTS, (
                    f"Expected actions-menu items {EXPECTED_MENU_ITEM_TEXTS!r} in "
                    f"order, got {item_texts!r}"
                )
                edit_open_response = secrets_page.click_edit_value_menu_item(row)
                assert edit_open_response.status == 200, (
                    f"Expected 200 from the edit-open GET, got {edit_open_response.status}"
                )

            with allure.step(
                "Step 4 — Verify the Value field becomes inline editable and "
                "starts EMPTY (not pre-filled with the existing plaintext "
                "value)"
            ):
                value_input = secrets_page.get_row_value_input(row)
                expect(value_input).to_have_count(1)
                assert value_input.input_value() == "", (
                    f"Expected the Value input to start empty, got "
                    f"{value_input.input_value()!r}"
                )

            with allure.step(
                "Step 5 — Verify the Name field is read-only: no Name input "
                "renders for this existing row (only a brand-new row does), "
                "just the same static-text cell shown in view mode, "
                "unchanged"
            ):
                expect(secrets_page.get_row_name_input(row)).to_have_count(0)
                name_cell_text = secrets_page.get_row_name_cell(row).text_content()
                assert name_cell_text == secret_name, (
                    f"Expected the row's name cell to still read {secret_name!r}, "
                    f"got {name_cell_text!r}"
                )

            with allure.step(
                "Step 6 — Enter a new value and click the checkmark; verify "
                "the PUT body and 200 OK response, and that NO list-GET "
                "refetch follows (local-state-only update, per source)"
            ):
                list_refetch_requests = secrets_page.capture_requests_matching(
                    SECRETS_LIST_URL_SUBSTRING, method="GET"
                )
                secrets_page.fill_edit_value(row, new_value)
                assert value_input.input_value() == new_value, (
                    f"Expected Value input to show {new_value!r}, got "
                    f"{value_input.input_value()!r}"
                )
                save_response, save_request_body = secrets_page.save_edit_value()
                assert save_response.status == 200, (
                    f"Expected 200 from the secret-edit PUT, got {save_response.status}"
                )
                assert save_request_body == {"value": new_value}, (
                    f"Expected PUT body {{'value': {new_value!r}}}, got {save_request_body!r}"
                )
                assert len(list_refetch_requests) == 0, (
                    f"Expected zero list-GET refetch requests after the edit PUT, "
                    f"got {list(list_refetch_requests)}"
                )
                list_refetch_requests.stop()

            with allure.step(
                "Step 7 — Verify the secret saves without error: the row "
                "returns to view mode showing the masked "
                "'{{secret.<name>}}' template string"
            ):
                expected_masked_value = "{{secret." + secret_name + "}}"
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    expected_masked_value, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Click the eye icon to reveal; verify a FRESH "
                "server GET returns the exact new value and the icon flips "
                "to the crossed-out (revealed) state"
            ):
                reveal_response = secrets_page.reveal_secret_value(row)
                assert reveal_response.status == 200, (
                    f"Expected 200 from the secret-reveal GET, got {reveal_response.status}"
                )
                expect(secrets_page.get_row_value_cell(row)).to_have_text(
                    new_value, timeout=ROW_WAIT_TIMEOUT
                )
                secrets_page.expect_visibility_icon_revealed_state(row)

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
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs
            # regardless of test outcome). This case's own steps never
            # delete the created secret — reuse the existing three-dot-menu
            # delete flow verbatim from ELITEA-2338, per the AFS § Cleanup.
            row = secrets_page.get_row_by_name(secret_name)
            if row.count() > 0:
                secrets_page.open_row_actions_menu(row)
                secrets_page.click_delete_menu_item()
                secrets_page.fill_delete_confirm_name(secret_name)
                secrets_page.confirm_delete()
