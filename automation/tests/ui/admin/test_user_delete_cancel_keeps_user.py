"""UI test — cancelling the delete confirmation keeps the user intact.

The subject is a user this test invites: "unchanged" is only provable against a
before-image, and a seeded row has three known, stable field values (Name "",
Last login "-", Role "viewer") where a real member's Last login moves under the
test. The flow under test is unchanged, and the seeded member is removed in a
``finally`` block — this case, unlike ELITEA-2298/2299, deliberately does NOT
delete its own subject.

The decisive assertion is not the table read but the REQUEST log: cancelling
must issue no DELETE at all. A table can look right while a delete is in
flight. The listener is a passive observer — nothing is intercepted, stubbed or
fabricated.

Test case: ELITEA-2300
AFS: test-specs/settings-users-and-roles/l2_cancel-deletion-keeps-the-user-intact_ELITEA-2300.md
"""

import logging
import uuid

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)
from utils.request_capture import collect_requests

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000

SEED_ROLE = "viewer"
DIALOG_TITLE = "Delete confirmation"
DIALOG_MESSAGE_SINGULAR_STEM = "Are you sure to delete the selected user"
CANCEL_BUTTON_TEXT = "Cancel"

# An invited-but-never-logged-in row's two DIFFERENT null renderings.
INVITED_ROW_NAME = ""
INVITED_ROW_LAST_LOGIN = "-"


@allure.epic("Settings")
@allure.feature("Users and Roles — Delete user")
class TestUserDeleteCancelKeepsUser:
    """ELITEA-2300 — Cancel dismisses the dialog and changes nothing."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2300_cancel-deletion-keeps-the-user-intact.md",
        "onetest-ai Test Case link (ELITEA-2300)",
    )
    @allure.title("Cancel deletion keeps the user intact")
    def test_cancel_deletion_keeps_user_intact(self, page):
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)
        email = f"elitea-del-cancel-{uuid.uuid4().hex[:8]}@example.com"

        # Passive observer over the whole test: every DELETE the page issues,
        # for any resource. Registered BEFORE the first click so nothing can
        # slip past it. Step 5 reads it for ABSENCE; the cleanup below reads it
        # again as the positive control that proves it was really wired.
        delete_requests = collect_requests(page)

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Users: the populated table renders; "
                "capture the baseline row count"
            ):
                users_page.navigate()
                baseline_row_count = users_page.user_row.count()
                assert baseline_row_count > 0, (
                    f"Expected the users table to render at least one row, got {baseline_row_count}"
                )

            with allure.step(
                f"Precondition — invite {email!r} with role {SEED_ROLE!r} and capture its "
                f"rendered field values as the before-image"
            ):
                users_page.open_invite_dialog()
                invite_response = users_page.invite_users([email], SEED_ROLE)
                assert invite_response.status == 200, (
                    f"Expected 200 from the invite-users POST, got {invite_response.status}"
                )
                seeded_row = users_page.get_row_by_text(email)
                expect(seeded_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(users_page.user_row).to_have_count(
                    baseline_row_count + 1, timeout=ROW_WAIT_TIMEOUT
                )
                before_name = users_page.get_name_cell_for_row(seeded_row).inner_text()
                before_last_login = users_page.get_last_login_cell_for_row(
                    seeded_row
                ).inner_text()
                before_role = users_page.get_role_cell_for_row(seeded_row).inner_text()
                # The before-image is the product's own rendering, and it is the
                # documented null shape for a never-logged-in invitee.
                assert before_name == INVITED_ROW_NAME, (
                    f"Expected an invited user's Name cell to render {INVITED_ROW_NAME!r}, "
                    f"got {before_name!r}"
                )
                assert before_last_login == INVITED_ROW_LAST_LOGIN, (
                    f"Expected an invited user's Last-login cell to render "
                    f"{INVITED_ROW_LAST_LOGIN!r}, got {before_last_login!r}"
                )
                assert before_role == SEED_ROLE, (
                    f"Expected the seeded Role cell to render {SEED_ROLE!r}, got {before_role!r}"
                )

            with allure.step("Step 2 — Click the trash icon on that user row"):
                users_page.open_delete_dialog_for_row(seeded_row)

            with allure.step("Step 3 — Verify a confirmation dialog appears"):
                expect(users_page.delete_confirm_dialog).to_be_visible()
                expect(users_page.delete_confirm_title).to_have_text(DIALOG_TITLE)
                expect(users_page.delete_confirm_message).to_contain_text(
                    DIALOG_MESSAGE_SINGULAR_STEM
                )
                expect(users_page.delete_confirm_cancel_button).to_have_text(
                    CANCEL_BUTTON_TEXT
                )

            with allure.step("Step 4 — Click Cancel: the dialog closes"):
                users_page.cancel_delete()
                expect(users_page.delete_confirm_dialog).to_have_count(0)

            with allure.step(
                "Step 5 — Verify the user remains in the table unchanged, and that no "
                "delete was ever issued"
            ):
                surviving_row = users_page.get_row_by_text(email)
                expect(surviving_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(users_page.get_name_cell_for_row(surviving_row)).to_have_text(
                    before_name
                )
                expect(
                    users_page.get_last_login_cell_for_row(surviving_row)
                ).to_have_text(before_last_login)
                expect(users_page.get_role_cell_for_row(surviving_row)).to_have_text(
                    before_role
                )
                expect(users_page.user_row).to_have_count(baseline_row_count + 1)
                assert not delete_requests, (
                    "Cancelling the confirmation must issue no DELETE at all, but the "
                    f"page sent: {delete_requests}"
                )
                expect(users_page.toast_alert).to_have_count(0)

            with allure.step("Step 6 — Verify no unexpected console errors"):
                # Known defect: #1971 (regression of the closed #554) — during the
                # project switch this page object performs, EliteaUI's `toolkitTypes`
                # query can fire before `useSelectedProjectId()` resolves and request
                # a project-id-less `.../toolkits/prompt_lib/`, which 404s. Cosmetic,
                # unrelated to anything this case drives. Excluded by that EXACT URL
                # only — never by status code. Delete this argument when #1971 ships.
                unexpected = exclude_known_defect_urls(
                    console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
                )
                assert not unexpected, f"Unexpected console errors: {unexpected}"
        finally:
            # Cleanup (not an AFS case step — MANDATORY here): this case
            # deliberately does not delete its subject, so the seeded member
            # survives the test body and would otherwise leak into shared live
            # project 400 (the two orphaned `elitea-batch-edit-test2-*` rows
            # already there are what that looks like).
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
                # Positive control for step 5's absence assertion. A listener
                # that was never wired records nothing, which would satisfy
                # "no DELETE was issued" vacuously; the cleanup delete is the
                # one DELETE this case does issue, so seeing it here proves the
                # earlier assertion was checked rather than unfalsifiable.
                assert delete_requests, (
                    "The DELETE observer recorded nothing even though cleanup "
                    "deleted the seeded user — step 5's 'no DELETE was issued' "
                    "assertion could not have been meaningful."
                )
            except Exception as exc:  # noqa: BLE001 - never swallow a leak
                logger.error(
                    "Cleanup failed for seeded user %r — row may be leaked into "
                    "shared live project data: %s",
                    email,
                    exc,
                )
                raise
