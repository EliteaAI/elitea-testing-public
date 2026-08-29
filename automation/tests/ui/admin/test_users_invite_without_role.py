"""UI test — Invite user without selecting a role leaves Invite disabled.

Read-only verification: a valid probe email is TYPED into the Invite dialog,
but the Invite button is never clicked — so no `POST /admin/users/default/
{project}` ever fires and no user is created. Step 6's row-count assertion is
the proof, not an assumption; no cleanup is therefore required.

Every asserted value is read off the live rendered dialog; nothing about the
system under test is substituted.

Why Step 5 exists. `InviteUserDialog.jsx` gates the button with
`disabled={!emails.length || !selectedRoles.length || error}` — three
independent conditions OR'd together. A test that only asserts "disabled"
proves nothing about WHICH gate fired, and would pass identically against a
permanently-broken button. So this test (a) enters a VALID email and asserts
no validation error, ruling out the `error` arm, and (b) after asserting the
disabled state, selects a role and watches the button ENABLE — which is what
makes Step 4's assertion actually about the empty Roles selection. The same
confound was caught by review on the sibling invalid-email case (ELITEA-2307);
it is designed out here rather than fixed in a round.

Test case: ELITEA-2308
AFS: test-specs/settings-users-and-roles/l3_invite-user-without-selecting-a-role_ELITEA-2308.md
"""

import logging
import uuid

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

PROBE_ROLE = "viewer"


class TestUsersInviteWithoutRole:
    """ELITEA-2308 — Invite user without selecting a role."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2308_invite-user-without-selecting-a-role.md",
        "onetest-ai Test Case link",
    )
    def test_invite_user_without_selecting_a_role(self, page):
        """With a valid email entered and no role selected the Invite button is
        disabled; selecting a role enables it, proving the empty Roles
        selection is what blocked the invite."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)
        probe_email = f"elitea-role-gate-{uuid.uuid4().hex[:8]}@example.com"

        with allure.step("Step 1 — Navigate to Settings -> Users: the populated table renders"):
            users_page.navigate()
            row_count_before = users_page.user_row.count()

        with allure.step(
            'Step 2 — Click "+": the Invite users dialog opens with the Invite button '
            "already disabled (nothing typed, no role chosen)"
        ):
            users_page.open_invite_dialog()
            expect(users_page.invite_dialog).to_be_visible()
            expect(users_page.invite_confirm_button).to_be_disabled()

        with allure.step(
            f"Step 3 — Enter the valid email {probe_email!r} and blur the field: the "
            "field displays it and NO validation error appears, so the `error` arm of "
            "the button's disabled gate is provably not what is firing"
        ):
            users_page.type_email_in_invite_dialog(probe_email)
            users_page.blur_invite_emails_field()

            assert users_page.invite_emails_input.input_value() == probe_email, (
                f"Expected the Emails field to display {probe_email!r}, got "
                f"{users_page.invite_emails_input.input_value()!r}"
            )
            expect(users_page.invite_emails_error_text).to_have_count(0)

        with allure.step(
            "Step 4 — Leave the Roles dropdown empty and verify the Invite button is "
            "disabled"
        ):
            assert users_page.get_invite_selected_role_text() == "", (
                "Expected no role to be selected, but the Roles combobox displays "
                f"{users_page.get_invite_selected_role_text()!r}"
            )
            expect(users_page.invite_confirm_button).to_be_disabled()

        with allure.step(
            f"Step 5 — Differentiator: select the {PROBE_ROLE!r} role — the Invite "
            "button becomes ENABLED, proving Step 4's disabled state was caused by "
            "the empty Roles selection and not by some other gate. Invite is still "
            "never clicked, so no user is created."
        ):
            users_page.select_role_in_invite_dialog(PROBE_ROLE)

            assert users_page.get_invite_selected_role_text() == PROBE_ROLE, (
                f"Expected the Roles combobox to display {PROBE_ROLE!r}, got "
                f"{users_page.get_invite_selected_role_text()!r}"
            )
            expect(users_page.invite_confirm_button).to_be_enabled()

        with allure.step(
            "Step 6 — Close the dialog: it unmounts and the users table is unchanged "
            "— this test invited nobody"
        ):
            users_page.close_invite_dialog()

            expect(users_page.invite_dialog).to_have_count(0)
            expect(users_page.user_row).to_have_count(row_count_before)

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
