"""UI test — Hide a secret via the row's three-dot menu and verify removal.

Creates ONE run-unique secret via the existing inline "+" flow (reused
verbatim from ELITEA-2336/2338) and hides THAT one via the row's three-dot
("more actions") menu → Hide → the shared, generic AlertDialog confirmation.
Never targets a pre-existing/real secret (the project has 100+ live secrets;
hiding one is NOT reversible via the UI — also sidesteps the `isDefault` prop
that disables all three menu items for system/default secrets).

Case-text drift (filed as clarification, not a defect —
EliteaAI/elitea-testing-public#1226): the case's step 5 quotes stale
confirmation copy ("...is completely removed from the Secrets table...
Hidden secrets cannot be unhidden."). The LIVE dialog (confirmed via source +
DOM read) shows title "Hide secret?", body `Are you sure to hide the secret
"<name>"? Once hidden, the secret will no longer be visible.`, confirm button
"Hide". This test asserts the LIVE copy per the reverse-masking guard.

Step 9 goes beyond "the '+' button is visible" (the case's own literal text)
to a CONCRETE re-creation with the exact same name, proving the case's own
stated Objective/Expected Final State that the backend does not reject a
previously-hidden name — see the AFS's step 9 note for the full reasoning.
The recreated secret is NOT hidden, so it is cleaned up via the UI delete
flow (reused from ELITEA-2338) as this test's own teardown.

Test case: ELITEA-2344
AFS: test-specs/settings-secrets/l3_hide-secret-via-three-dot-menu_ELITEA-2344.md

Known defect (EliteaAI/elitea-testing-public#1203): `/settings/secrets` may
fire a React "Maximum update depth exceeded" console warning on mount
(isolated to `SecretsContent.jsx`, does not affect functional behaviour).
NOT observed in this case's own analyst exploration session (0 console
errors across navigate -> create -> hide -> reload -> recreate -> delete).
Soft-asserted via the same `soft_failures`/`pytest.fail()` idiom as the
covering delete/create tests so this assertion stays isolated: an UNEXPECTED
console error (any text other than this known signature) still hard-fails
immediately.
"""

import logging
import uuid

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SECRET_VALUE = "hide-test-value-123"
RECREATE_SECRET_VALUE = "hide-test-recreated-value-456"
ROW_WAIT_TIMEOUT = 15_000


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console warning (EliteaAI/
    elitea-testing-public#1203) — a React "Maximum update depth exceeded"
    warning that may fire on a `/settings/secrets` mount.

    Matches on the STABLE warning-text prefix alone (not a volatile
    component-stack suffix that may or may not be captured — see
    `test_secret_create_inline_checkmark_x_cancel.py`'s own matcher
    docstring for the full rationale)."""
    return "Maximum update depth exceeded" in text


class TestSecretHideViaThreeDotMenu:
    """ELITEA-2344 — the three-dot menu's 'Hide' item opens the shared
    AlertDialog confirmation; confirming fires the hide POST and removes the
    secret from the table, both immediately and after a fresh reload — and
    the '+' button remains available to create a NEW secret with the exact
    same (previously-hidden) name."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2344_hide-secret-via-three-dot-menu.md",
        "onetest-ai Test Case link",
    )
    def test_hide_secret_via_three_dot_menu(self, page):
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()
        secret_name = f"autotest_hide_{uuid.uuid4().hex[:8]}"
        soft_failures: list[str] = []
        recreated = False

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
                "Step 2 — Create a run-unique secret via the inline '+' flow "
                "(this also decomposes the case's 'note the name' step — the "
                "generated name IS the noted name); verify the create POST "
                "resolves 201 Created"
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

            with allure.step("Step 4 — Click 'Hide'"):
                secrets_page.click_hide_menu_item()

            with allure.step(
                "Step 5 — Verify the confirmation dialog shows the LIVE copy "
                "(case-text drift filed as clarification #1226, not a "
                "defect — the case's own quoted text is stale per the "
                "reverse-masking guard)"
            ):
                expected_body = (
                    f'Are you sure to hide the secret "{secret_name}"? '
                    "Once hidden, the secret will no longer be visible."
                )
                assert secrets_page.get_hide_confirm_text() == expected_body, (
                    f"Expected hide-confirm dialog body {expected_body!r}, got "
                    f"{secrets_page.get_hide_confirm_text()!r}"
                )
                assert secrets_page.alert_dialog_confirm_button.text_content() == "Hide", (
                    "Expected the hide-confirmation dialog's confirm button text "
                    f"'Hide', got {secrets_page.alert_dialog_confirm_button.text_content()!r}"
                )

            with allure.step(
                "Step 6 — Confirm the action; verify the hide POST resolves "
                "200 OK (side-channel proof of persistence, not just DOM "
                "removal)"
            ):
                hide_response = secrets_page.confirm_hide()
                assert hide_response.status == 200, (
                    f"Expected 200 from the secret-hide POST, got {hide_response.status}"
                )

            with allure.step(
                "Step 7 — Verify the secret is no longer visible in the "
                "table: row count drops to 0, and the unfiltered pagination "
                "total returns to the pre-create baseline"
            ):
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.pagination_info).to_have_text(
                    pagination_baseline, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Reload the page; verify the hidden secret still "
                "does not reappear (genuine server round-trip, not a "
                "DOM/client-cache-only check)"
            ):
                secrets_page.reload_and_wait()
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 9 — Verify the '+' button is available to create a NEW "
                "secret with the exact same (previously-hidden) name: type "
                "the name, confirm no client-side collision error and Save "
                "is enabled, save, and verify the create POST resolves 201 "
                "(not a 409/400 conflict) — a concrete re-creation, not just "
                "a button-visibility check (per the AFS's strengthened step 9)"
            ):
                expect(secrets_page.add_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.type_name(secret_name)
                expect(secrets_page.name_error).to_have_count(0)
                expect(secrets_page.save_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.value_input.click()
                secrets_page.value_input.press_sequentially(
                    RECREATE_SECRET_VALUE, delay=20
                )
                recreate_response = secrets_page.click_save_button()
                assert recreate_response.status == 201, (
                    "Expected 201 (not a conflict) recreating a previously-"
                    f"hidden name, got {recreate_response.status}"
                )
                recreated = True
                expect(secrets_page.get_row_by_name(secret_name)).to_have_count(
                    1, timeout=ROW_WAIT_TIMEOUT
                )
                expect(secrets_page.pagination_info).not_to_have_text(
                    pagination_baseline, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Verify no UNEXPECTED console errors across the "
                "flow (Known defect EliteaAI/elitea-testing-public#1203 — "
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
            if recreated:
                # Cleanup: step 9's recreated secret is NOT hidden — it is a
                # live, visible row that WILL pollute shared project data if
                # left behind (unlike the originally-hidden secret, which
                # needs no cleanup — it's already server-removed by steps
                # 6-8). Reuses ELITEA-2338's UI delete flow verbatim.
                row = secrets_page.get_row_by_name(secret_name)
                if row.count() == 1:
                    secrets_page.open_row_actions_menu(row)
                    secrets_page.click_delete_menu_item()
                    secrets_page.fill_delete_confirm_name(secret_name)
                    secrets_page.confirm_delete()
