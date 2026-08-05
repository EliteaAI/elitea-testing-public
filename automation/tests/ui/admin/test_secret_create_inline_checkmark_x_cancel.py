"""UI test — Create secret inline: "+" adds editable row, checkmark saves,
X cancels.

Creates ONE real secret under the active project (via the ✓ save flow) and
deletes it via the API in a mandatory cleanup step regardless of test
outcome, per `.agents/testing.md` § Test data strategy ("clean up loudly
only when the observable requires fresh state" — this case's core observable
IS the freshly created secret). The second (✗ cancel) flow's secret is never
persisted server-side — that is itself the assertion — so it needs no
cleanup.

Test case: ELITEA-2336
AFS: test-specs/settings-secrets/l3_create-secret-inline-checkmark-x-cancel_ELITEA-2336.md

Known defect (EliteaAI/elitea-testing-public#1203, confirmed live this run,
3/3 deterministic across two full pytest runs + one isolated repro script):
`/settings/secrets` fires a React "Maximum update depth exceeded" console
warning repeatedly on EVERY mount, before any interaction — isolated to
`SecretsContent.jsx`. Does not affect functional behaviour (the full
create/verify/cancel/verify flow below passes). NOT caused by this case's
own testid additions (static string props, no render/dependency-array
effect). Soft-asserted via the pytest-native `soft_failures`/`pytest.fail()`
mechanism (same idiom as `test_agent_publish_unpublish_version.py`'s #611
handling — a raw console-message list isn't `expect.soft()`-bindable) so
this assertion stays isolated: an UNEXPECTED console error (any text other
than this known signature) still hard-fails immediately. `_is_known_defect_1203()`
matches on the warning's own STABLE text prefix alone (NOT a component-stack
suffix — Playwright's console-message capture does not always include the
full stack, see the function's own docstring) so the classification stays
deterministic across a short-form and a long-form occurrence alike.
Sanctioned-RED per `.agents/testing.md` § Merge gate — this test is expected
to stay RED until EliteaAI/elitea-testing-public#1203 ships.
"""

import logging
import uuid

import allure
import pytest
from config import settings
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

SECRET_VALUE = "my-secret-value-123"
ROW_WAIT_TIMEOUT = 15_000


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console warning (EliteaAI/
    elitea-testing-public#1203) — a React "Maximum update depth exceeded"
    warning that fires on every `/settings/secrets` mount.

    Matches on the STABLE warning-text prefix alone. An earlier version of
    this matcher also required the `SecretsContent.jsx` component-stack
    substring to be present, but Playwright's console-message capture does
    not always include the full component stack for this warning — a
    short-form occurrence (~250 chars, no stack suffix) was observed
    live during round-2 verification (fix-round 3, ELITEA-2336/PR #1204),
    alongside the normal long-form occurrence (~4600 chars, full stack incl.
    `SecretsContent.jsx`). Requiring both substrings meant the short-form
    occurrence fell into `unexpected_errors` and hard-failed the test with a
    different failure signature than the long-form occurrence — violating
    the sanctioned-RED gate's "(a) deterministic — identical failure 3/3"
    requirement (`.agents/testing.md` § Merge gate). Same fix shape already
    applied to the #518 known-defect matcher (`test_credential_create.py`) —
    anchor on the warning's own stable text, not a volatile stack/component
    suffix that may or may not be captured.
    """
    return "Maximum update depth exceeded" in text


class TestSecretCreateInlineCheckmarkXCancel:
    """ELITEA-2336 — "+" adds an inline editable row (not a modal); checkmark
    persists it via POST + shows the masked placeholder at its alphabetical
    position; X discards it client-side with zero network calls and no
    server-side secret."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2336_create-secret-inline-adds-editable-row-checkmark-saves-x-can.md",
        "onetest-ai Test Case link",
    )
    def test_create_secret_inline_checkmark_saves_x_cancels(self, page, api):
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()
        saved_name = f"autotest_secret_{uuid.uuid4().hex[:8]}"
        cancelled_name = f"autotest_secret_{uuid.uuid4().hex[:8]}"
        saved = False
        soft_failures: list[str] = []

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets; verify page title and "
                "at least one existing secret row (table is pre-populated, not empty)"
            ):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got {secrets_page.page_title.text_content()!r}"
                )
                expect(secrets_page.secret_row.first).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                pagination_before = secrets_page.get_pagination_text()

            with allure.step(
                "Step 2 — Click the '+' (add) button; verify it becomes disabled "
                "immediately (only one row editable at a time)"
            ):
                secrets_page.click_add_button()

            with allure.step(
                "Step 3 — Verify the new row is an inline table row (not a modal/"
                "dialog) and that pagination resets to page 1, count including the "
                "unsaved pending row (case-text clarification, "
                "EliteaAI/elitea-testing-public#1202: the case says 'at the current "
                "pagination position' — live behaviour always resets to page 1)"
            ):
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                expect(secrets_page.value_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                # Proves the new row's input lives INSIDE the same `secret-row`
                # table structure as every other row — not a separate modal/
                # dialog (no page-level dialog testid exists to assert absence
                # of; this positive containment check is the compliant proof).
                expect(secrets_page.get_editing_row_name_input()).to_be_visible(
                    timeout=ROW_WAIT_TIMEOUT
                )
                pagination_after_add = secrets_page.get_pagination_text()
                assert pagination_after_add != pagination_before, (
                    f"Expected the pagination total to increase after '+' (pending row "
                    f"counted client-side), got {pagination_after_add!r} == "
                    f"{pagination_before!r}"
                )
                assert pagination_after_add.startswith("1 - "), (
                    f"Expected pagination to reset to page 1 ('1 - ...'), got "
                    f"{pagination_after_add!r}"
                )

            with allure.step(
                "Step 4 — Enter name and value into the new row; verify both inputs "
                "display the typed text"
            ):
                secrets_page.fill_new_row(saved_name, SECRET_VALUE)
                assert secrets_page.name_input.input_value() == saved_name, (
                    f"Expected name input to show {saved_name!r}, got "
                    f"{secrets_page.name_input.input_value()!r}"
                )
                assert secrets_page.value_input.input_value() == SECRET_VALUE, (
                    f"Expected value input to show {SECRET_VALUE!r}, got "
                    f"{secrets_page.value_input.input_value()!r}"
                )

            with allure.step(
                "Step 5 — Click the checkmark (save) icon; verify the create POST "
                "resolves 201 Created"
            ):
                response = secrets_page.click_save_button()
                assert response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {response.status}"
                )
                saved = True

            with allure.step(
                "Step 6 — Verify the row saved: exact name + masked "
                "'{{secret.<name>}}' value, add button re-enabled, row NOT pinned "
                "to the top (alphabetically sorted, unlike a pending row)"
            ):
                row = secrets_page.get_row_by_name(saved_name)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                name_cell_text = secrets_page.get_row_name_cell(row).text_content()
                assert name_cell_text == saved_name, (
                    f"Expected the row's name cell to read {saved_name!r}, got "
                    f"{name_cell_text!r}"
                )
                expected_masked_value = "{{secret." + saved_name + "}}"
                value_cell_text = secrets_page.get_row_value_cell(row).text_content()
                assert value_cell_text == expected_masked_value, (
                    f"Expected the row's value cell to read {expected_masked_value!r}, "
                    f"got {value_cell_text!r}"
                )
                expect(secrets_page.add_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)
                first_row_name_text = secrets_page.get_row_name_cell(
                    secrets_page.secret_row.first
                ).text_content()
                assert first_row_name_text != saved_name, (
                    f"Expected the saved row NOT to be pinned as page-1's first row "
                    f"(alphabetically sorted like any other secret), but the first "
                    f"row is {first_row_name_text!r}"
                )

            with allure.step(
                "Step 7 — Click '+' again; enter a second, different generated name "
                "and value — verify the same new-row behavior"
            ):
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(cancelled_name, SECRET_VALUE)
                assert secrets_page.name_input.input_value() == cancelled_name, (
                    f"Expected name input to show {cancelled_name!r}, got "
                    f"{secrets_page.name_input.input_value()!r}"
                )
                assert secrets_page.value_input.input_value() == SECRET_VALUE, (
                    f"Expected value input to show {SECRET_VALUE!r}, got "
                    f"{secrets_page.value_input.input_value()!r}"
                )

            with allure.step(
                "Step 8 — Click the X (cancel) icon; verify NO POST fires — cancel "
                "is purely client-side"
            ):
                create_requests = secrets_page.capture_requests_matching(
                    "/secrets/secrets/default/", method="POST"
                )
                secrets_page.click_cancel_button()
                assert len(create_requests) == 0, (
                    f"Expected zero POST requests on cancel, got {list(create_requests)}"
                )
                create_requests.stop()

            with allure.step(
                "Step 9 — Verify the row is discarded: absent from the DOM, absent "
                "from a fresh server GET (reload), and the add button re-enabled"
            ):
                expect(secrets_page.get_row_by_name(cancelled_name)).to_have_count(0)
                expect(secrets_page.add_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)

                secrets_page.reload_and_wait()
                expect(secrets_page.get_row_by_name(cancelled_name)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Verify no UNEXPECTED console errors across the flow "
                "(Known defect EliteaAI/elitea-testing-public#1203: a React "
                "'Maximum update depth exceeded' warning fires on every "
                "/settings/secrets mount — soft-asserted, isolated, filtered "
                "by exact signature so a genuinely NEW console error still "
                "hard-fails here)"
            ):
                unexpected_errors = [
                    m.text for m in console_errors if not _is_known_defect_1203(m.text)
                ]
                assert not unexpected_errors, (
                    f"Unexpected console errors: {unexpected_errors}"
                )
                # Known defect: EliteaAI/elitea-testing-public#1203 — recorded
                # in soft_failures (real soft-assertion equivalent, see the
                # pytest.fail() below) rather than only logged, so this stays
                # a tracked, visible RED until the product fix ships —
                # sanctioned-RED per .agents/testing.md § Merge gate.
                known_defect_errors = [
                    m.text for m in console_errors if _is_known_defect_1203(m.text)
                ]
                if known_defect_errors:
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
            # regardless of test outcome: step 5-6 creates a real, persistent
            # secret in shared live project data). The step 7-9 secret is
            # never persisted server-side (that's the assertion), so nothing
            # to clean up there. No UI testids exist for the row's dots-menu /
            # Delete flow (SecretActionsMenu.jsx has zero testids and this
            # case's own steps never exercise delete) — use the generic API
            # client directly, same pattern as e.g. AgentAPI.delete_agent()
            # teardown, per the AFS § Cleanup.
            if saved:
                delete_response = api.delete(
                    f"/secrets/secret/default/{settings.elitea_project_id}/{saved_name}"
                )
                assert delete_response.status_code == 204, (
                    f"Cleanup failed: expected 204 deleting {saved_name!r}, got "
                    f"{delete_response.status_code} {delete_response.text}"
                )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2337_secret-name-only-allows-letters-numbers-and-underscores-hyph.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_secret_name_rejects_hyphen_and_special_chars_valid_name_clears_error(
        self, page
    ):
        """ELITEA-2337 — a secret name containing a hyphen, or a space/special
        character, shows the validation error "Only alphanumeric characters and
        underscore are allowed" and disables the save (checkmark) icon;
        replacing it with a conforming name (letters/numbers/underscores only)
        clears the error and re-enables the checkmark. Read-only against the
        pending row: never clicks the checkmark, creates no secret, needs no
        API cleanup - discards the pending row via the existing Cancel (X) icon.
        (The empty-row-starts-enabled and fresh-valid-name-enables-checkmark
        observables are already touched by
        test_create_secret_inline_checkmark_saves_x_cancels's own Steps 1-4 -
        not repeated here; this test's own new ground is the INVALID states and
        the invalid->valid recovery transition.)"""
        secrets_page = SecretsPage(page)
        console_errors = secrets_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets; click '+' and wait "
                "for the new row's name input"
            ):
                secrets_page.navigate()
                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 2 — Enter a hyphenated name; verify the validation error "
                "is shown and the checkmark stays disabled"
            ):
                secrets_page.type_name("my-secret")
                assert secrets_page.name_input.input_value() == "my-secret", (
                    f"Expected name input to show 'my-secret', got "
                    f"{secrets_page.name_input.input_value()!r}"
                )
                expect(secrets_page.name_error).to_have_text(
                    "Only alphanumeric characters and underscore are allowed"
                )
                expect(secrets_page.save_button).to_be_disabled(timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 3 — Replace with a name containing a space and a special "
                "character; verify the same validation error and disabled "
                "checkmark"
            ):
                secrets_page.clear_and_type_name("my secret!")
                assert secrets_page.name_input.input_value() == "my secret!", (
                    f"Expected name input to show 'my secret!', got "
                    f"{secrets_page.name_input.input_value()!r}"
                )
                expect(secrets_page.name_error).to_have_text(
                    "Only alphanumeric characters and underscore are allowed"
                )
                expect(secrets_page.save_button).to_be_disabled(timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 4 — Replace with a conforming name; verify the "
                "validation error clears and the checkmark becomes enabled"
            ):
                secrets_page.clear_and_type_name("my_secret_123")
                expect(secrets_page.name_error).to_have_count(0)
                expect(secrets_page.save_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)

            with allure.step("Step 5 — Verify no console errors across the flow"):
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
                    # Known defect: EliteaAI/elitea-testing-public#1203 - this
                    # test also mounts /settings/secrets, so it is expected to
                    # hit the same deterministic mount-time console warning
                    # as the covering test in this same file. Sanctioned-RED
                    # per .agents/testing.md § Merge gate.
                    pytest.fail(
                        "Test flow completed and all functional assertions passed, "
                        "but a known-defect soft failure was recorded:\n"
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1203: "
                        f"React 'Maximum update depth exceeded' console error(s) on "
                        f"/settings/secrets mount: {len(known_defect_errors)} occurrence(s)"
                    )
        finally:
            console_errors.stop()
            # Cleanup (not an AFS case step) - the pending row is never saved
            # (checkmark is never clicked in this test), so discard it via the
            # existing Cancel (X) icon: zero network calls, no secret ever
            # created, no API cleanup needed. Guard with a bare try since the
            # row may already be gone if an earlier assertion failed mid-flow.
            try:
                secrets_page.click_cancel_button()
            except Exception:
                logger.warning(
                    "Cleanup: could not click cancel button (row may already "
                    "be gone or page navigated away)"
                )
