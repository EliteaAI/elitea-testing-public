"""UI test — Eye icon reveals the actual secret value and changes to
crossed-out eye (row-level Show/Hide toggle).

Creates ONE run-unique secret via the existing inline "+" flow (reused
verbatim from ELITEA-2336), clicks its row's Show/Hide (eye) toggle to reveal
the plaintext value, clicks the crossed-out eye to re-mask it, then deletes
the generated secret via the existing three-dot-menu delete flow (reused
verbatim from ELITEA-2338) as this case's own explicit cleanup step.

This case exercises the ROW-LEVEL eye-icon toggle only — a DIFFERENT
mechanism from the three-dot menu's "Hide" item (server-side mutation behind
a confirmation dialog, covered by sibling case ELITEA-2344/#852). Reveal
fires a real `GET .../secret/default/{project_id}/{name}` server round-trip;
hide/re-mask is purely client-side (zero network requests) — see the AFS
§ Network Behavior and Note on the two distinct "hide" mechanisms.

Test case: ELITEA-2343
AFS: test-specs/settings-secrets/l3_secret-eye-icon-reveal-and-mask-toggle_ELITEA-2343.md

Known defect (EliteaAI/elitea-testing-public#1203): `/settings/secrets` may
fire a React "Maximum update depth exceeded" console warning on mount.
Deterministic 3/3 in ELITEA-2336's own automated run but NOT observed in
several other cases' live analyst exploration sessions. Soft-asserted via
the same `soft_failures`/`pytest.fail()` idiom as the covering
`test_secret_delete_via_three_dot_menu.py` so this assertion stays isolated.
"""

import logging
import uuid

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

SECRET_REVEAL_URL_SUBSTRING = "/secrets/secret/default/"
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


class TestSecretEyeIconRevealAndMaskToggle:
    """ELITEA-2343 — the row-level eye (Show/Hide) toggle reveals the actual
    plaintext secret value via a real server round-trip and swaps the icon
    to crossed-out; clicking again re-masks the value client-side only (zero
    network requests) and restores the normal eye icon."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2343_eye-icon-reveals-the-actual-secret-value-and-changes-to-cros.md",
        "onetest-ai Test Case link",
    )
    def test_secret_eye_icon_reveal_and_mask_toggle(self, page):
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()
        secret_name = f"autotest_eye_reveal_{uuid.uuid4().hex[:8]}"
        secret_value = f"reveal-value-{uuid.uuid4().hex[:8]}"
        masked_value = f"{{{{secret.{secret_name}}}}}"
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
                secrets_page.fill_new_row(secret_name, secret_value)
                response = secrets_page.click_save_button()
                assert response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {response.status}"
                )

            with allure.step(
                "Step 3 — Locate the created secret's row; verify the Value cell "
                "shows the masked '{{secret.<name>}}' template and the toggle "
                "renders the normal (masked) eye icon"
            ):
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                value_cell = secrets_page.get_row_value_cell(row)
                expect(value_cell).to_have_text(masked_value, timeout=ROW_WAIT_TIMEOUT)
                secrets_page.expect_visibility_icon_masked_state(row)

            with allure.step(
                "Step 4 — Click the eye (Show/Hide) toggle; verify the reveal GET "
                "resolves 200 OK"
            ):
                reveal_response = secrets_page.reveal_secret_value(row)
                assert reveal_response.status == 200, (
                    f"Expected 200 from the secret-reveal GET, got {reveal_response.status}"
                )

            with allure.step(
                "Step 5 — Verify the Value column now shows the exact plaintext "
                "value this test created"
            ):
                expect(value_cell).to_have_text(secret_value, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 6 — Verify the eye icon changed to the crossed-out "
                "(revealed) state"
            ):
                secrets_page.expect_visibility_icon_revealed_state(row)

            with allure.step(
                "Step 7 — Click the crossed-out eye icon; verify ZERO new "
                "network requests fire (purely client-side hide, distinct from "
                "the three-dot menu's server-side Hide)"
            ):
                requests_during_hide = secrets_page.capture_requests_matching(
                    SECRET_REVEAL_URL_SUBSTRING
                )
                secrets_page.hide_secret_value(row)
                expect(value_cell).to_have_text(masked_value, timeout=ROW_WAIT_TIMEOUT)
                assert len(requests_during_hide) == 0, (
                    f"Expected zero network requests on hide/re-mask, got "
                    f"{list(requests_during_hide)}"
                )
                requests_during_hide.stop()

            with allure.step(
                "Step 8 — Verify the value returned to the exact original masked "
                "'{{secret.<name>}}' string"
            ):
                assert value_cell.text_content() == masked_value, (
                    f"Expected value cell to revert to {masked_value!r}, got "
                    f"{value_cell.text_content()!r}"
                )

            with allure.step(
                "Step 9 — Verify the icon reverted to the normal (masked) eye "
                "icon"
            ):
                secrets_page.expect_visibility_icon_masked_state(row)

            with allure.step(
                "Step 10 — Verify no UNEXPECTED console errors across the flow "
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
            # Cleanup — this case's own steps do NOT delete the generated
            # secret (unlike ELITEA-2338, whose steps ARE a delete flow); the
            # AFS's § Cleanup directs reusing the existing three-dot-menu
            # delete flow (verbatim from ELITEA-2338).
            row = secrets_page.get_row_by_name(secret_name)
            if row.count() > 0:
                secrets_page.open_row_actions_menu(row)
                secrets_page.click_delete_menu_item()
                secrets_page.fill_delete_confirm_name(secret_name)
                secrets_page.confirm_delete()
