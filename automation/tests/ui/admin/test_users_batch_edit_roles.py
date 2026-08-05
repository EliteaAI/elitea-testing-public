"""UI test — Batch edit roles for multiple selected users.

Invites 2 disposable users into project 400 ("UI Testing" — the only
reachable project where the acting test account holds `admin`; see the
AFS's Preconditions), batch-selects ONLY those 2 rows, edits their role
via the header "Edit roles" dialog, and verifies the 2 pre-existing rows
(`Levon Dadayan`, and `Test Bot` — the acting account itself) keep their
original `admin` role unchanged. The 2 seeded rows are deleted in a
`finally` block regardless of test outcome — this project's user list is
shared, reused, real data (`.agents/testing.md` § Test data strategy).

Test case: ELITEA-2304
AFS: test-specs/settings-users-and-roles/l2_batch-edit-roles-for-multiple-selected-users_ELITEA-2304.md
"""

import logging
import uuid

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression]

SEEDED_ROLE = "editor"
TARGET_ROLE = "viewer"
EXPECTED_PUT_MSG = "roles updated"
UNSELECTED_ADMIN_ROWS = ("Levon Dadayan", "Test Bot")
ROW_WAIT_TIMEOUT = 15_000


class TestBatchEditRolesForMultipleSelectedUsers:
    """ELITEA-2304 — Batch edit roles for multiple selected users."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2304_batch-edit-roles-for-multiple-selected-users.md",
        "onetest-ai Test Case link",
    )
    def test_batch_edit_roles_for_multiple_selected_users(self, page):
        """Invite 2 disposable users (role editor), batch-select ONLY
        them, edit their role to viewer via the header Edit-roles dialog,
        and verify the 2 pre-existing users' roles are provably
        unaffected."""
        users_page = AdminUsersPage(page)
        suffix = uuid.uuid4().hex[:8]
        seeded_emails = [
            f"elitea-batch-edit-test1-{suffix}@example.com",
            f"elitea-batch-edit-test2-{suffix}@example.com",
        ]
        seeded_rows_present = False

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Users: user rows become visible"
            ):
                users_page.navigate()
                # Captured (not hardcoded) so Step 2's assertion self-heals
                # against any already-present rows instead of permanently
                # breaking after a single leaked row (ELITEA-2304 hardening-
                # gate diagnosis, 2026-08-05 — this project's user list is
                # shared, persistent, live data; see the cleanup discussion
                # below the try/finally).
                initial_row_count = users_page.user_row.count()
                assert initial_row_count > 0, (
                    f"Expected the users table to render at least one row, got {initial_row_count}"
                )

            with allure.step(
                "Step 2 — Seed test data: invite 2 disposable users with role "
                "'editor'; verify the table now lists 2 more rows than at Step "
                "1, each seeded row showing role 'editor'"
            ):
                users_page.open_invite_dialog()
                invite_response = users_page.invite_users(seeded_emails, SEEDED_ROLE)
                assert invite_response.status == 200, (
                    f"Expected 200 from the invite-users POST, got {invite_response.status}"
                )
                seeded_rows_present = True

                expect(users_page.user_row).to_have_count(
                    initial_row_count + 2, timeout=ROW_WAIT_TIMEOUT
                )
                for email in seeded_emails:
                    row = users_page.get_row_by_text(email)
                    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                    role_text = (users_page.get_role_cell_for_row(row).text_content() or "").strip()
                    assert role_text == SEEDED_ROLE, (
                        f"Expected seeded row {email!r} to show role {SEEDED_ROLE!r}, got {role_text!r}"
                    )

            with allure.step(
                "Step 3 — Select the checkboxes on the 2 newly invited rows only "
                "(never Levon Dadayan or Test Bot)"
            ):
                for email in seeded_emails:
                    row = users_page.get_row_by_text(email)
                    users_page.select_user_row(row)
                    assert users_page.is_row_checkbox_checked(row), (
                        f"Expected the checkbox for {email!r} to be checked after selecting it"
                    )

            with allure.step(
                "Step 4 — Verify the header batch-Edit (pencil) button is now "
                "enabled (was disabled with 0 rows selected)"
            ):
                assert users_page.header_edit_button.is_enabled(), (
                    "Expected the header batch-Edit button to be enabled once 2 rows are selected"
                )

            with allure.step(
                'Step 5 — Click the header batch-Edit button; verify the "Edit '
                'roles" dialog opens with exact title text'
            ):
                users_page.open_edit_roles_dialog()
                assert users_page.edit_roles_dialog.is_visible(), (
                    "Expected the Edit roles dialog to be visible"
                )
                title_text = users_page.edit_roles_dialog_title.text_content()
                assert title_text == "Edit roles", (
                    f"Expected dialog title 'Edit roles', got {title_text!r}"
                )

            with allure.step(
                "Step 6 — Select role 'viewer' in the dialog's Roles select; "
                "verify Save transitions from disabled to enabled"
            ):
                assert users_page.edit_roles_save_button.is_disabled(), (
                    "Expected Save to be disabled before any role is selected"
                )
                users_page.select_role_in_edit_dialog(TARGET_ROLE)
                assert users_page.edit_roles_save_button.is_enabled(), (
                    "Expected Save to be enabled once a role is selected"
                )

            with allure.step(
                "Step 7 — Click Save; verify the driving PUT resolves 200 OK "
                'with body {"msg": "roles updated"}, the dialog closes, and '
                "the users list re-fetches"
            ):
                put_response, refetch_response = users_page.save_edit_roles()
                assert put_response.status == 200, (
                    f"Expected 200 from the batch-edit-roles PUT, got {put_response.status}"
                )
                put_body = put_response.json()
                assert put_body.get("msg") == EXPECTED_PUT_MSG, (
                    f"Expected PUT response body msg {EXPECTED_PUT_MSG!r}, got {put_body!r}"
                )
                assert refetch_response.status == 200, (
                    f"Expected 200 from the users-list refetch GET, got {refetch_response.status}"
                )
                expect(users_page.edit_roles_dialog).to_have_count(0, timeout=ROW_WAIT_TIMEOUT)

            with allure.step(
                "Step 8 — Verify both selected (invited) users now show role "
                "'viewer' in the Role column"
            ):
                for email in seeded_emails:
                    row = users_page.get_row_by_text(email)
                    role_text = (users_page.get_role_cell_for_row(row).text_content() or "").strip()
                    assert role_text == TARGET_ROLE, (
                        f"Expected {email!r}'s role to be {TARGET_ROLE!r} after batch-edit, "
                        f"got {role_text!r}"
                    )

            with allure.step(
                "Step 9 — Verify the 2 unselected, pre-existing users (Levon "
                "Dadayan, Test Bot) still show role 'admin' (unchanged)"
            ):
                for name in UNSELECTED_ADMIN_ROWS:
                    row = users_page.get_row_by_text(name)
                    role_text = (users_page.get_role_cell_for_row(row).text_content() or "").strip()
                    assert role_text == "admin", (
                        f"Expected unselected row {name!r} to keep role 'admin', got {role_text!r}"
                    )
        finally:
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs
            # regardless of test outcome: this case seeds real, persistent
            # rows in shared live project data — see AFS § Cleanup).
            #
            # Per-item isolation + non-atomicity fix (ELITEA-2304 hardening-
            # gate diagnosis, 2026-08-05): the previous loop gated deletion on
            # a single non-retrying `row.count() > 0` snapshot and had zero
            # exception isolation between emails, so (a) deleting the first
            # seeded row invalidates the users-list query cache — if the
            # SECOND row's existence check landed during that refetch
            # window, `.count()` could read 0 and silently skip deletion
            # with no exception anywhere, and (b) an assert/expect failure
            # while processing the first email aborted the loop outright,
            # so the second email was never even attempted. Both defects
            # land on the same symptom: only the last seeded row ever
            # leaked into the live project's shared table.
            #
            # Fixed by: (1) confirming presence via a WAITING assertion
            # instead of a single immediate snapshot, so a transient
            # refetch race can never be misread as "already gone"; and
            # (2) wrapping each email's delete+verify in its own
            # try/except so one row's failure never skips the rest —
            # failures are collected and raised together as one aggregated
            # error only after every seeded email has been attempted.
            if seeded_rows_present:
                cleanup_failures: list[str] = []
                for email in seeded_emails:
                    try:
                        row = users_page.get_row_by_text(email)
                        expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                        delete_response = users_page.delete_user_row(row)
                        assert delete_response.status == 204, (
                            f"Expected 204 from deleting seeded user {email!r}, "
                            f"got {delete_response.status}"
                        )
                        expect(users_page.get_row_by_text(email)).to_have_count(
                            0, timeout=ROW_WAIT_TIMEOUT
                        )
                    except Exception as exc:  # noqa: BLE001 - isolate + aggregate, never swallow
                        cleanup_failures.append(f"{email!r}: {exc}")
                        logger.error(
                            "Cleanup failed for seeded user %r — row may be "
                            "leaked into shared live project data: %s",
                            email,
                            exc,
                        )
                assert not cleanup_failures, (
                    "Cleanup failed for one or more seeded users — leaked "
                    f"into shared live project data: {cleanup_failures}"
                )
