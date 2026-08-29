"""UI test — delete a user via the per-row Delete (trash) icon.

The case's "any user row" is a row this test creates: project 400's real rows
are the acting automation account itself, a human admin, and two orphaned seed
rows — none of them safe to delete. The seeded subject makes the case
self-contained; the flow under test is unchanged.

The decisive assertion for "the icon deletes nothing on its own" is not the
table read but the REQUEST log: a row survives a DELETE that is still in
flight, so only "no DELETE was issued" can prove the icon is non-destructive.
Step 4 then asserts the confirm issued exactly one — the positive control that
keeps step 2's absence assertion from passing vacuously.

Every asserted value is produced by the live product — the DELETE's own status,
the rendered toast, the rendered table, and the table again after a full page
reload. The request listener is a passive observer: nothing is intercepted,
stubbed or substituted.

Test case: ELITEA-2298
AFS: test-specs/settings-users-and-roles/l3_delete-a-user-via-per-row-delete-icon_ELITEA-2298.md
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

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

ROW_WAIT_TIMEOUT = 15_000

SEED_ROLE = "viewer"
DIALOG_TITLE = "Delete confirmation"
# The singular branch of DeleteUserButton.jsx's textContent. Asserted as a
# STEM, not verbatim: the sentence embeds the subject's name, and a
# never-logged-in invitee's name is the empty string.
DIALOG_MESSAGE_SINGULAR_STEM = "Are you sure to delete the selected user"


@allure.epic("Settings")
@allure.feature("Users and Roles — Delete user")
class TestUserDeleteViaRowIcon:
    """ELITEA-2298 — the per-row trash icon deletes exactly one user, for good."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2298_delete-a-user-via-per-row-delete-icon.md",
        "onetest-ai Test Case link (ELITEA-2298)",
    )
    @allure.title("Delete a user via the per-row Delete icon")
    def test_delete_user_via_row_icon(self, page):
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)
        email = f"elitea-del-row-{uuid.uuid4().hex[:8]}@example.com"
        deleted = False

        # Passive observer over the whole test: every DELETE the page issues,
        # for any resource. Registered BEFORE the first click so nothing can
        # slip past it. Step 2 reads it for ABSENCE, step 4 for the count that
        # proves the observer was really wired.
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
                f"Precondition — invite {email!r} with role {SEED_ROLE!r}: it becomes a "
                f"real member and gets its own row"
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

            with allure.step(
                "Step 2 — Click the trash icon in the Actions column of that row: it "
                "opens a dialog and issues no DELETE at all"
            ):
                # open_delete_dialog_for_row waits for the confirmation dialog to
                # render — that is the anchor. The product has demonstrably
                # finished reacting to the click, so "no DELETE has been issued"
                # is a statement about a settled UI, not a race against an
                # in-flight request. The table read below cannot make that
                # statement on its own: a row outlives a DELETE in flight.
                users_page.open_delete_dialog_for_row(seeded_row)
                assert not delete_requests, (
                    "Opening the confirmation must issue no DELETE at all, but the "
                    f"page sent: {delete_requests}"
                )
                expect(users_page.get_row_by_text(email)).to_have_count(1)

            with allure.step("Step 3 — Verify a confirmation dialog appears"):
                expect(users_page.delete_confirm_dialog).to_be_visible()
                expect(users_page.delete_confirm_title).to_have_text(DIALOG_TITLE)
                expect(users_page.delete_confirm_message).to_contain_text(
                    DIALOG_MESSAGE_SINGULAR_STEM
                )
                expect(users_page.delete_confirm_button).to_be_visible()
                expect(users_page.delete_confirm_cancel_button).to_be_visible()

            with allure.step(
                "Step 4 — Confirm deletion: the driving DELETE resolves 204 and a "
                "success confirmation is shown"
            ):
                delete_response = users_page.confirm_delete()
                deleted = True
                assert delete_response.status == 204, (
                    f"Expected 204 from the delete-user DELETE, got {delete_response.status}"
                )
                # The success toast auto-hides after 3 000 ms, so it is asserted
                # FIRST — before any table read — while it is still mounted.
                expect(users_page.get_toast_by_severity("success")).to_be_visible()
                expect(users_page.delete_confirm_dialog).to_have_count(0)
                # Positive control for step 2's absence assertion: confirming is
                # what issues the DELETE, and exactly one of them. An observer
                # that recorded this proves the earlier "none yet" was checked,
                # not vacuous.
                assert len(delete_requests) == 1, (
                    f"Expected confirming to issue exactly one DELETE, got "
                    f"{delete_requests}"
                )

            with allure.step(
                "Step 5 — Verify the user is removed from the table, and only that user"
            ):
                expect(users_page.get_row_by_text(email)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
                expect(users_page.user_row).to_have_count(
                    baseline_row_count, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Reload the page: the user does not reappear — the deletion "
                "was server-side, not a local list edit"
            ):
                reload_response = users_page.reload_and_wait()
                assert reload_response.status == 200, (
                    f"Expected 200 from the post-reload users-list GET, got "
                    f"{reload_response.status}"
                )
                expect(users_page.get_row_by_text(email)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )
                expect(users_page.user_row).to_have_count(
                    baseline_row_count, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step("Step 7 — Verify no unexpected console errors"):
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
            # Cleanup (not an AFS case step). The case's own step 4 IS the
            # deletion, so on the happy path there is nothing left to remove —
            # this only catches a test that died before confirming, because the
            # seed is a REAL, persistent member of shared live project 400.
            if not deleted:
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
                except Exception as exc:  # noqa: BLE001 - never swallow a leak
                    logger.error(
                        "Cleanup failed for seeded user %r — row may be leaked into "
                        "shared live project data: %s",
                        email,
                        exc,
                    )
                    raise
