"""UI test — Inviting a user who is already a project member is rejected.

Seeds ONE disposable member (a single invite, role ``viewer``), then re-invites
that same address and verifies the product refuses it: the driving POST resolves
**400 Bad Request**, an ``error``-severity toast names the address and the
project, and the table gains no duplicate row.

Why the "existing member" is seeded rather than borrowed: project 400's only
pre-existing members are the acting test account itself and a real human admin
(plus two orphaned seed rows nobody guarantees). Re-inviting either real account
risks a role overwrite on the identity the whole suite authenticates as. Seeding
the member reaches the same observable through a disposable subject and makes
the case independent of live project topology — declared in the AFS
(`.agents/role-overrides.md` § declared-improvisation protocol): it shapes HOW
the precondition is reached, not WHAT is verified.

Every asserted value is produced by the system — the POST's own status, the
rendered toast, the rendered table. Nothing is substituted.

No console-error assertion here, deliberately: this case's own subject IS a 400
response, which the browser logs as a console error; excluding the very request
under test would be noise, not signal.

Test case: ELITEA-2309
AFS: test-specs/settings-users-and-roles/l3_invite-existing-project-member-shows-error_ELITEA-2309.md
"""

import logging
import uuid

import allure
import pytest
from config import settings
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SEEDED_ROLE = "viewer"
ROW_WAIT_TIMEOUT = 15_000


@allure.epic("Settings")
@allure.feature("Users and Roles — Invite users")
class TestUsersInviteExistingMemberError:
    """ELITEA-2309 — Invite user who is already a project member shows an error."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2309_invite-user-who-is-already-a-project-member-shows-appropriat.md",
        "onetest-ai Test Case link",
    )
    def test_invite_existing_project_member_shows_error(self, page):
        """Re-inviting an existing project member returns 400, surfaces an
        'already exists' error toast, and adds no duplicate row."""
        users_page = AdminUsersPage(page)
        member_email = f"elitea-invite-dup-{uuid.uuid4().hex[:8]}@example.com"
        # The backend's message embeds the project id — build it from config so
        # it tracks the env key instead of a literal.
        expected_error = (
            f"user {member_email} already exists in project {settings.users_team_project_id}"
        )
        member_seeded = False

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Users: the populated table renders; "
                "capture the baseline row count"
            ):
                users_page.navigate()
                baseline_row_count = users_page.user_row.count()
                assert baseline_row_count > 0, (
                    f"Expected the users table to render at least one row, got "
                    f"{baseline_row_count}"
                )

            with allure.step(
                f"Step 2 — Note the email of an existing project member: invite "
                f"{member_email!r} once with role {SEEDED_ROLE!r}, making it a member; "
                f"it appears exactly once"
            ):
                users_page.open_invite_dialog()
                seed_response = users_page.invite_users([member_email], SEEDED_ROLE)
                member_seeded = True
                assert seed_response.status == 200, (
                    f"Expected 200 from the seeding invite POST, got {seed_response.status}"
                )

                expect(users_page.user_row).to_have_count(
                    baseline_row_count + 1, timeout=ROW_WAIT_TIMEOUT
                )
                member_row = users_page.get_row_by_text(member_email)
                expect(member_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                member_row_count = baseline_row_count + 1

            with allure.step(
                f'Step 3 — Click "+" and enter the existing member\'s email '
                f"({member_email!r}): the dialog opens and the field displays it"
            ):
                users_page.open_invite_dialog()
                expect(users_page.invite_dialog).to_be_visible()
                users_page.type_email_in_invite_dialog(member_email)
                assert users_page.invite_emails_input.input_value() == member_email, (
                    f"Expected the Emails field to display {member_email!r}, got "
                    f"{users_page.invite_emails_input.input_value()!r}"
                )

            with allure.step(
                f"Step 4 — Select role {SEEDED_ROLE!r} and click Invite: the driving "
                f"POST is rejected with 400 Bad Request — the product refuses the "
                f"duplicate at the API, not merely in the UI"
            ):
                users_page.select_role_in_invite_dialog(SEEDED_ROLE)
                duplicate_response = users_page.submit_invite()
                assert duplicate_response.status == 400, (
                    f"Expected 400 from the duplicate-invite POST, got "
                    f"{duplicate_response.status}"
                )

            with allure.step(
                f"Step 5 — An error indicating the user is already a member is shown: "
                f"{expected_error!r}"
            ):
                expect(users_page.get_toast_by_severity("error")).to_be_visible()
                expect(users_page.toast_message).to_have_text(expected_error)

            with allure.step(
                "Step 6 — No duplicate entry appears in the table: the row count is "
                "unchanged, the address still matches exactly one row, and that row's "
                "role is untouched"
            ):
                expect(users_page.user_row).to_have_count(
                    member_row_count, timeout=ROW_WAIT_TIMEOUT
                )
                surviving_row = users_page.get_row_by_text(member_email)
                expect(surviving_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                expect(users_page.get_role_cell_for_row(surviving_row)).to_have_text(SEEDED_ROLE)
        finally:
            # Cleanup (not an AFS case step — mandatory, runs regardless of
            # outcome): step 2 creates a REAL, persistent member of shared live
            # project 400. The duplicate invite creates nothing — that is the
            # case's point — so there is exactly one row to remove. Presence is
            # confirmed with a WAITING assertion, never a single snapshot that a
            # refetch window could read as "already gone" (ELITEA-2304 teardown
            # lesson).
            if member_seeded:
                try:
                    row = users_page.get_row_by_text(member_email)
                    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                    delete_response = users_page.delete_user_row(row)
                    assert delete_response.status == 204, (
                        f"Expected 204 from deleting seeded user {member_email!r}, "
                        f"got {delete_response.status}"
                    )
                    expect(users_page.get_row_by_text(member_email)).to_have_count(
                        0, timeout=ROW_WAIT_TIMEOUT
                    )
                except Exception:
                    logger.error(
                        "Cleanup failed for seeded member %r — row may be leaked into "
                        "shared live project data",
                        member_email,
                    )
                    raise
