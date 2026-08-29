"""UI test — Invite users dialog opens with correct layout.

Read-only verification: the dialog is opened, its layout is read, and it is
dismissed via its own Close (x) button. Nothing is typed, Invite is never
clicked, so no `POST /admin/users/default/{project}` ever fires and no user is
created — Step 5's row-count assertion proves that rather than assuming it.

Every asserted value is read off the live rendered dialog; nothing about the
system under test is substituted.

The exact strings asserted here are deterministic literals in
`InviteUserDialog.jsx` / `Users.jsx`, so exact-text assertions are correct
rather than brittle. Note the description text's missing space before the
parenthesis ("emails(separated") — that is the product's own wording and the
case's, reproduced verbatim.

The Emails field's required marker is asserted through its <label> text
("Emails *"): the asterisk is rendered because the field carries `required`, so
the label text IS the observable the case's "marked as required with *"
describes. The assertion reads innerText rather than textContent — the label
node carries two asterisks, the visible one and MUI's own display:none
`MuiFormLabel-asterisk` span, and only the visible one is what the case means.

Test case: ELITEA-2295
AFS: test-specs/settings-users-and-roles/l3_invite-users-dialog-opens-with-correct-layout_ELITEA-2295.md
"""

import logging

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_TITLE = "Invite users"
EXPECTED_DESCRIPTION = (
    "Enter user emails(separated by comma) and select roles to define permissions for this project."
)
EXPECTED_EMAILS_LABEL = "Emails *"
EXPECTED_ROLES = ["admin", "editor", "viewer"]


class TestUsersInviteDialogLayout:
    """ELITEA-2295 — Invite users dialog opens with correct layout."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2295_invite-users-dialog-opens-with-correct-layout.md",
        "onetest-ai Test Case link",
    )
    def test_invite_users_dialog_opens_with_correct_layout(self, page):
        """The "+" button opens a dialog carrying the expected title, helper
        text, required Emails field, three-role dropdown and Close (x) control,
        and the Close button dismisses it without inviting anyone."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users: the page loads, the '+' invite "
            "button is visible and enabled, and the Invite dialog is NOT mounted yet"
        ):
            users_page.navigate()
            row_count_before = users_page.user_row.count()

            expect(users_page.invite_button).to_be_visible()
            expect(users_page.invite_button).to_be_enabled()
            # Without the before-state, "the dialog is visible" in Step 2 would also
            # pass for a dialog that was already open — which is not what "opens" means.
            expect(users_page.invite_dialog).to_have_count(0)

        with allure.step('Step 2 — Click the "+" button: the "Invite users" dialog opens'):
            users_page.open_invite_dialog()
            expect(users_page.invite_dialog).to_be_visible()

        with allure.step('Step 3 — Verify the dialog title is exactly "Invite users"'):
            expect(users_page.invite_dialog_title).to_have_text(EXPECTED_TITLE)

        with allure.step(
            "Step 4 — Verify the dialog description matches the case text verbatim"
        ):
            expect(users_page.invite_dialog_description).to_have_text(EXPECTED_DESCRIPTION)

        with allure.step(
            "Step 5 — Verify the Emails field is present and marked required: its "
            'label reads "Emails *", where the asterisk is MUI\'s rendering of the '
            "field's `required` flag"
        ):
            expect(users_page.invite_emails_input).to_be_visible()
            # use_inner_text: the label node holds TWO asterisks — the visible one
            # StyledInputEnhancer renders inside the label Box ("Emails *"), and MUI's
            # own display:none `MuiFormLabel-asterisk` span. textContent (Playwright's
            # default) concatenates both into "Emails * *"; innerText is what the user
            # actually reads, which is the observable the case describes.
            expect(users_page.invite_emails_label).to_have_text(
                EXPECTED_EMAILS_LABEL, use_inner_text=True
            )

        with allure.step(
            "Step 6 — Verify the Roles dropdown offers exactly three options: admin, "
            "editor, viewer"
        ):
            expect(users_page.invite_role_select_combobox).to_be_visible()
            users_page.open_roles_menu(users_page.invite_role_select_combobox)

            # "showing: admin, editor, viewer" is an enumeration — asserting only that
            # the three named roles are present would miss a fourth role appearing.
            expect(users_page.get_role_options_locator()).to_have_text(EXPECTED_ROLES)

            users_page.close_roles_menu()

        with allure.step("Step 7 — Verify the Close (x) button is present in the dialog"):
            expect(users_page.invite_close_button).to_be_visible()

        with allure.step(
            "Step 8 — Click the Close (x) button: the dialog unmounts and the users "
            "table is untouched — the open/close round trip invited nobody"
        ):
            users_page.close_invite_dialog()

            expect(users_page.invite_dialog).to_have_count(0)
            expect(users_page.user_row).to_have_count(row_count_before)

        with allure.step("Step 9 — Verify no unexpected console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
