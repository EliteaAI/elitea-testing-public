"""UI test — Invite users through Settings -> Users, single and multiple.

One parameterized spec over the two flow-variants of ONE flow ("+" -> Emails ->
Roles -> Invite), a row per source case, each row asserting its OWN expected
values:

  * ELITEA-2296 — ONE email, role ``viewer``, singular confirmation
    ``"The user has been invited"``.
  * ELITEA-2297 — TWO comma-separated emails, role ``editor``, plural
    confirmation ``"The users have been invited"``.

The singular/plural split is the product's own (`Users.jsx`:181,
``emailCount > 1 ? … : …``) and is the observable that distinguishes "two
addresses were parsed" from "one string was swallowed" — so it is asserted per
row, not flattened.

Every asserted value is read off the live product: the invite POST's own
status, the rendered toast, and the rendered table. Nothing is substituted.

Both rows create REAL, persistent members of shared live project 400 and delete
them in a ``finally`` block regardless of outcome
(`.agents/testing.md` § Test data strategy).

Test cases: ELITEA-2296, ELITEA-2297
AFS: test-specs/settings-users-and-roles/l3_invite-users-single-and-multiple_ELITEA-2296.md
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

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000

# An invited-but-never-logged-in row's two DIFFERENT null renderings —
# see AdminUsersPage.row_name_cell / row_last_login_cell.
INVITED_ROW_NAME = ""
INVITED_ROW_LAST_LOGIN = "-"

# One row per source case — see module docstring.
INVITE_CASES = [
    pytest.param(
        "ELITEA-2296", 1, "viewer", "The user has been invited",
        id="ELITEA-2296-single-email-viewer",
    ),
    pytest.param(
        "ELITEA-2297", 2, "editor", "The users have been invited",
        id="ELITEA-2297-two-comma-separated-emails-editor",
    ),
]


@allure.epic("Settings")
@allure.feature("Users and Roles — Invite users")
class TestUsersInviteSingleAndMultiple:
    """ELITEA-2296 / ELITEA-2297 — inviting one user, and several at once."""

    @pytest.mark.parametrize("case_id, email_count, role, expected_toast", INVITE_CASES)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2296_invite-a-single-user-with-a-role.md",
        "onetest-ai Test Case link (ELITEA-2296)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2297_invite-multiple-users-simultaneously-using-comma-separated-e.md",
        "onetest-ai Test Case link (ELITEA-2297)",
    )
    @allure.title("Invite {email_count} user(s) with role {role}")
    def test_invite_users_with_role(self, page, case_id, email_count, role, expected_toast):
        """Run once per Test Data row — ``case_id`` ties a failure back to its
        originating case so one row's regression never masks its sibling."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)
        suffix = uuid.uuid4().hex[:8]
        emails = [
            f"elitea-invite-{case_id.lower()}-{index}-{suffix}@example.com"
            for index in range(1, email_count + 1)
        ]
        # The shape the case text shows: "user1@test.com, user2@test.com".
        emails_text = ", ".join(emails)
        invite_submitted = False

        try:
            with allure.step(
                f"[{case_id}] Step 1 — Navigate to Settings -> Users: the populated "
                f"table renders; capture the baseline row count"
            ):
                users_page.navigate()
                baseline_row_count = users_page.user_row.count()
                assert baseline_row_count > 0, (
                    f"[{case_id}] Expected the users table to render at least one row, "
                    f"got {baseline_row_count}"
                )

            with allure.step(f'[{case_id}] Step 2 — Click "+": the Invite users dialog opens'):
                users_page.open_invite_dialog()
                expect(users_page.invite_dialog).to_be_visible()

            with allure.step(
                f"[{case_id}] Step 3 — Enter {email_count} email address(es) in the "
                f"Emails field: the field displays exactly what was typed "
                f"({emails_text!r})"
            ):
                users_page.type_email_in_invite_dialog(emails_text)
                assert users_page.invite_emails_input.input_value() == emails_text, (
                    f"[{case_id}] Expected the Emails field to display {emails_text!r}, got "
                    f"{users_page.invite_emails_input.input_value()!r}"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Open the Roles dropdown and select {role!r}: the "
                f"combobox displays it"
            ):
                users_page.select_role_in_invite_dialog(role)
                assert users_page.get_invite_selected_role_text() == role, (
                    f"[{case_id}] Expected the Roles combobox to display {role!r}, got "
                    f"{users_page.get_invite_selected_role_text()!r}"
                )

            with allure.step(
                f"[{case_id}] Step 5 — Click Invite: the driving POST resolves 200 OK"
            ):
                invite_response = users_page.submit_invite()
                invite_submitted = True
                assert invite_response.status == 200, (
                    f"[{case_id}] Expected 200 from the invite-users POST, got "
                    f"{invite_response.status}"
                )

            with allure.step(
                f"[{case_id}] Step 6 — The dialog closes and a success confirmation is "
                f"shown: {expected_toast!r}"
            ):
                # The success toast auto-hides after 3 000 ms, so it is asserted
                # FIRST — before any table read — while it is still mounted. It
                # renders in the same tick the POST above resolved.
                expect(users_page.get_toast_by_severity("success")).to_be_visible()
                expect(users_page.toast_message).to_have_text(expected_toast)
                expect(users_page.invite_dialog).to_have_count(0)

            with allure.step(
                f"[{case_id}] Step 7 — The {email_count} invited user(s) appear in the "
                f"Users table with role {role!r}, exactly one row each, and the "
                f"pre-existing rows are undisturbed"
            ):
                expect(users_page.user_row).to_have_count(
                    baseline_row_count + email_count, timeout=ROW_WAIT_TIMEOUT
                )
                for email in emails:
                    row = users_page.get_row_by_text(email)
                    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                    expect(users_page.get_role_cell_for_row(row)).to_have_text(role)
                    # An invited user has not logged in yet: the Name cell is
                    # empty and the Last-login cell holds the literal "-".
                    expect(users_page.get_name_cell_for_row(row)).to_have_text(INVITED_ROW_NAME)
                    expect(users_page.get_last_login_cell_for_row(row)).to_have_text(
                        INVITED_ROW_LAST_LOGIN
                    )

            with allure.step(f"[{case_id}] Step 8 — Verify no unexpected console errors"):
                # Known defect: #1971 (regression of the closed #554) — during the
                # project switch this page object performs, EliteaUI's `toolkitTypes`
                # query can fire before `useSelectedProjectId()` resolves and request
                # a project-id-less `.../toolkits/prompt_lib/`, which 404s. Cosmetic,
                # unrelated to anything this case drives. Excluded by that EXACT URL
                # only — never by status code. Delete this argument when #1971 ships.
                unexpected = exclude_known_defect_urls(
                    console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
                )
                assert not unexpected, f"[{case_id}] Unexpected console errors: {unexpected}"
        finally:
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs
            # regardless of outcome: this case creates REAL, persistent members
            # of shared live project 400).
            #
            # Per-email isolate-and-aggregate, exactly as ELITEA-2304's teardown
            # does: a presence check that WAITS (never a single immediate
            # snapshot, which a post-delete refetch can read as "already gone"),
            # and one try/except per email so the first failure cannot skip the
            # rest. The two `elitea-batch-edit-test2-*` rows still sitting in
            # project 400 are what a non-isolated loop leaks.
            if invite_submitted:
                cleanup_failures: list[str] = []
                for email in emails:
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
                            "Cleanup failed for invited user %r — row may be leaked "
                            "into shared live project data: %s",
                            email,
                            exc,
                        )
                assert not cleanup_failures, (
                    "Cleanup failed for one or more invited users — leaked into "
                    f"shared live project data: {cleanup_failures}"
                )
