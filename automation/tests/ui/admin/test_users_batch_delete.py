"""UI test — batch-delete several users via the row checkboxes.

The two subjects are users this test invites: a batch delete needs two rows it
is safe to destroy, and project 400 holds only the acting automation account, a
human admin, and two orphaned seed rows. The flow under test is unchanged.

**This spec is sanctioned-RED on `#1974`.** Confirming a batch delete leaves the
Users page in an unbounded React re-render loop (`Maximum update depth
exceeded`, `DeleteUserButton.jsx`'s success effect calls `setSelectedUsers([])`
while `users` is in its own dependency array), so the table renders zero rows
and never recovers until a page reload. The case's "verify only the selected
users are removed" is therefore asserted TWICE: once in place with
``expect.soft()`` — the visible signal, red until the product ships — and once
after a reload, hard, because the deletion itself is correct and "all other
users remain unaffected" is still fully verifiable.

The success toast is asserted for presence and `success` severity but NOT for
its wording: it currently reads the singular `"The user user has been
successfully deleted."` for a multi-user delete (`#1975`, same root cause).
Asserting that text would freeze a defect into the contract; soft-asserting the
correct text would add a second red for a cause `#1974` already covers.

Every asserted value is produced by the live product. Nothing is substituted.

Test case: ELITEA-2299
AFS: test-specs/settings-users-and-roles/l2_batch-delete-multiple-users-using-checkboxes_ELITEA-2299.md
"""

import logging
import uuid

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000
# The in-place recovery assertion is a KNOWN red (#1974) — keep its wait short
# so the expected failure costs seconds rather than the default timeout.
KNOWN_DEFECT_TIMEOUT = 5_000

SEED_ROLE = "viewer"
SEED_COUNT = 2
DIALOG_TITLE = "Delete confirmation"
# The PLURAL branch of DeleteUserButton.jsx — verbatim, no entity name is
# embedded when more than one user is selected.
DIALOG_MESSAGE_PLURAL = "Are you sure to delete the selected users?"


@allure.epic("Settings")
@allure.feature("Users and Roles — Delete user")
class TestUsersBatchDelete:
    """ELITEA-2299 — checkbox selection + the header Delete icon."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2299_batch-delete-multiple-users-using-checkboxes.md",
        "onetest-ai Test Case link (ELITEA-2299)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1974",
        "Known defect #1974 — batch delete leaves the page in a render loop",
    )
    @allure.title("Batch delete multiple users using checkboxes")
    def test_batch_delete_multiple_users(self, page):
        users_page = AdminUsersPage(page)
        suffix = uuid.uuid4().hex[:8]
        emails = [f"elitea-del-batch-{suffix}-{index}@example.com" for index in range(1, SEED_COUNT + 1)]
        deleted = False

        # Passive observer: proves the header icon issues nothing before the
        # confirmation is accepted. Nothing is intercepted or fabricated.
        delete_requests: list[str] = []
        page.on(
            "request",
            lambda request: delete_requests.append(request.url)
            if request.method == "DELETE"
            else None,
        )

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Users: the populated table renders and "
                "the header Delete icon is DISABLED with nothing selected"
            ):
                users_page.navigate()
                baseline_row_count = users_page.user_row.count()
                assert baseline_row_count > 0, (
                    f"Expected the users table to render at least one row, got {baseline_row_count}"
                )
                # "Becomes active" is a transition — it needs both ends.
                expect(users_page.header_delete_button).to_be_disabled()

            with allure.step(
                f"Precondition — invite {SEED_COUNT} disposable users with role "
                f"{SEED_ROLE!r}, and capture the OTHER rows' emails as the control set"
            ):
                users_page.open_invite_dialog()
                invite_response = users_page.invite_users(emails, SEED_ROLE)
                assert invite_response.status == 200, (
                    f"Expected 200 from the invite-users POST, got {invite_response.status}"
                )
                expect(users_page.user_row).to_have_count(
                    baseline_row_count + SEED_COUNT, timeout=ROW_WAIT_TIMEOUT
                )
                seeded_rows = [users_page.get_row_by_text(email) for email in emails]
                for email, row in zip(emails, seeded_rows, strict=True):
                    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                    assert email in users_page.get_row_emails(), (
                        f"Expected {email!r} to be listed after the invite"
                    )
                control_emails = {
                    email for email in users_page.get_row_emails() if email not in emails
                }
                assert len(control_emails) == baseline_row_count, (
                    f"Expected {baseline_row_count} untouched rows to act as the control "
                    f"set, got {len(control_emails)}: {sorted(control_emails)}"
                )

            with allure.step(
                f"Step 2 — Select the checkboxes on the {SEED_COUNT} seeded rows: only "
                f"those rows read checked"
            ):
                for row in seeded_rows:
                    users_page.select_user_row(row)
                for email, row in zip(emails, seeded_rows, strict=True):
                    assert users_page.is_row_checkbox_checked(row), (
                        f"Expected the row for {email!r} to be checked"
                    )
                for email in control_emails:
                    assert not users_page.is_row_checkbox_checked(
                        users_page.get_row_by_text(email)
                    ), f"Expected the untouched row for {email!r} to stay unchecked"

            with allure.step(
                "Step 3 — Verify the Delete (trash) icon in the header has become ACTIVE"
            ):
                expect(users_page.header_delete_button).to_be_enabled()

            with allure.step(
                "Step 4 — Click the header Delete icon: it opens a dialog and deletes "
                "nothing on its own"
            ):
                users_page.open_batch_delete_dialog()
                assert not delete_requests, (
                    "Opening the batch-delete confirmation must issue no DELETE, but the "
                    f"page sent: {delete_requests}"
                )

            with allure.step("Step 5 — Verify a confirmation dialog appears"):
                expect(users_page.delete_confirm_dialog).to_be_visible()
                expect(users_page.delete_confirm_title).to_have_text(DIALOG_TITLE)
                # Plural wording is the product's own proof that a multi-row
                # selection reached the dialog.
                expect(users_page.delete_confirm_message).to_have_text(
                    DIALOG_MESSAGE_PLURAL
                )

            with allure.step(
                "Step 6 — Confirm deletion: ONE DELETE carries both ids and resolves 204, "
                "and a success confirmation is shown"
            ):
                delete_response = users_page.confirm_delete()
                deleted = True
                assert delete_response.status == 204, (
                    f"Expected 204 from the batch-delete DELETE, got {delete_response.status}"
                )
                # The success toast auto-hides after 3 000 ms, so it is asserted
                # FIRST, before any table read. Presence + severity only — its
                # wording is wrong today (#1975), and asserting the wrong text
                # would freeze a defect into the contract.
                expect(users_page.get_toast_by_severity("success")).to_be_visible()

            with allure.step(
                "Step 7 — Verify only the selected users are removed, IN PLACE "
                "(known defect #1974 — the page enters a render loop instead)"
            ):
                # Known defect: #1974 — after a batch delete, DeleteUserButton's
                # success effect re-triggers itself forever (setSelectedUsers([])
                # with `users` in its own dependency array), so the table renders
                # zero rows and never recovers until a reload. Asserted SOFT
                # against the CORRECT expected behaviour so the red stays visible
                # and flips green when the fix ships. Not masking — the case's
                # data claim is still verified hard in Step 8.
                expect.soft(users_page.user_row).to_have_count(
                    baseline_row_count, timeout=KNOWN_DEFECT_TIMEOUT
                )
                for email in emails:
                    expect.soft(users_page.get_row_by_text(email)).to_have_count(
                        0, timeout=KNOWN_DEFECT_TIMEOUT
                    )

            with allure.step(
                "Step 8 — Reload, then verify the DATA truth: only the selected users are "
                "gone and every other user is unaffected"
            ):
                reload_response = users_page.reload_and_wait()
                assert reload_response.status == 200, (
                    f"Expected 200 from the post-reload users-list GET, got "
                    f"{reload_response.status}"
                )
                for email in emails:
                    expect(users_page.get_row_by_text(email)).to_have_count(
                        0, timeout=ROW_WAIT_TIMEOUT
                    )
                expect(users_page.user_row).to_have_count(
                    baseline_row_count, timeout=ROW_WAIT_TIMEOUT
                )
                # A count alone survives a swap — compare the SET.
                assert set(users_page.get_row_emails()) == control_emails, (
                    "Expected every non-selected user to be unaffected. Expected "
                    f"{sorted(control_emails)}, got {sorted(users_page.get_row_emails())}"
                )
        finally:
            # Cleanup (not an AFS case step). The case's own Step 6 IS the
            # deletion, so this only catches a test that died before confirming —
            # the seeds are REAL, persistent members of shared live project 400.
            if not deleted:
                cleanup_failures: list[str] = []
                for email in emails:
                    try:
                        leftover = users_page.get_row_by_text(email)
                        expect(leftover).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                        cleanup_response = users_page.delete_user_row(leftover)
                        assert cleanup_response.status == 204, (
                            f"Expected 204 from deleting seeded user {email!r}, "
                            f"got {cleanup_response.status}"
                        )
                        expect(users_page.get_row_by_text(email)).to_have_count(
                            0, timeout=ROW_WAIT_TIMEOUT
                        )
                    except Exception as exc:  # noqa: BLE001 - isolate + aggregate
                        cleanup_failures.append(f"{email!r}: {exc}")
                        logger.error(
                            "Cleanup failed for seeded user %r — row may be leaked "
                            "into shared live project data: %s",
                            email,
                            exc,
                        )
                assert not cleanup_failures, (
                    "Cleanup failed for one or more seeded users — leaked into "
                    f"shared live project data: {cleanup_failures}"
                )
