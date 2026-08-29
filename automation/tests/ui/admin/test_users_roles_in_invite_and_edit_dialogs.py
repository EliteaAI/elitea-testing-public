"""UI test — Available roles in Invite and Edit dialogs are admin, editor, viewer.

Read-only verification: both dialogs are opened purely to READ their role
options and are dismissed without saving. The Invite button is never clicked
(no user is created) and the Edit dialog's Save is never clicked (its Save
stays disabled until a role actually changes). Step 5's unchanged-role
assertion is the cleanliness proof, not an assumption.

Every asserted value is read off the live rendered dialogs; nothing about the
system under test is substituted. The role list itself comes from the product
(`GET /admin/roles/default/{project}` -> `Users.jsx`'s `rolesOptions`), so the
comparison is against what the platform actually offers.

The case's operative word is "the SAME three options", so the two lists are
compared TO EACH OTHER as well as to the expected triple — comparing both
against a literal alone would still pass if the product's two dialogs had
drifted apart and the case text had gone stale in the same direction.

⚠️ `[data-testid^="select-option-"]` is NOT an option count on this surface.
`SingleSelect` renders a checkmark carrying `select-option-selected-icon` next
to the currently-selected option, and the row-Edit dialog always opens with
the user's current role selected — so the bare prefix yields 4, not 3. The
page object's `ROLE_OPTION_ANY_SELECTOR` excludes it; see that constant's note.

Test case: ELITEA-2305
AFS: test-specs/settings-users-and-roles/l3_available-roles-in-invite-and-edit-dialogs_ELITEA-2305.md
"""

import logging

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_ROLES = ["admin", "editor", "viewer"]


class TestUsersRolesInInviteAndEditDialogs:
    """ELITEA-2305 — Available roles in Invite and Edit dialogs."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2305_available-roles-in-invite-and-edit-dialogs.md",
        "onetest-ai Test Case link",
    )
    def test_available_roles_in_invite_and_edit_dialogs(self, page):
        """Both the Invite-users dialog and a per-row Edit-roles dialog offer
        exactly admin, editor and viewer — and offer the identical list — while
        leaving the subject row's role untouched."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Users: the populated table renders"):
            users_page.navigate()
            expect(users_page.user_row.first).to_be_visible()

        with allure.step('Step 2 — Click "+" to open the Invite users dialog'):
            users_page.open_invite_dialog()
            expect(users_page.invite_dialog).to_be_visible()

        with allure.step(
            "Step 3 — Open the Roles dropdown: exactly three options are offered — "
            "admin, editor, viewer"
        ):
            users_page.open_roles_menu(users_page.invite_role_select_combobox)
            expect(users_page.get_role_options_locator()).to_have_text(EXPECTED_ROLES)
            invite_roles = users_page.get_role_option_texts()
            users_page.close_roles_menu()

        with allure.step("Step 4 — Close the Invite dialog"):
            users_page.close_invite_dialog()
            expect(users_page.invite_dialog).to_have_count(0)

        with allure.step(
            "Step 5 — Click Edit on the first user row and open its Roles dropdown"
        ):
            first_row = users_page.user_row.first
            role_before = (users_page.get_role_cell_for_row(first_row).text_content() or "").strip()

            users_page.open_row_edit_roles_dialog(first_row)
            expect(users_page.row_edit_roles_dialog).to_be_visible()

            users_page.open_roles_menu(users_page.row_edit_roles_select_combobox)

        with allure.step(
            "Step 6 — Verify the SAME three options: exactly admin, editor, viewer, "
            "and a list identical to the Invite dialog's"
        ):
            expect(users_page.get_role_options_locator()).to_have_text(EXPECTED_ROLES)
            edit_roles = users_page.get_role_option_texts()
            assert edit_roles == invite_roles, (
                "The case asserts the two dialogs offer the SAME options — Invite "
                f"offered {invite_roles}, row Edit offered {edit_roles}"
            )

        with allure.step(
            "Step 7 — Dismiss the Edit dialog without saving: it unmounts and the "
            "row's role is unchanged, proving this read-only visit mutated nothing"
        ):
            users_page.close_roles_menu()
            users_page.close_row_edit_roles_dialog()

            expect(users_page.row_edit_roles_dialog).to_have_count(0)
            expect(users_page.get_role_cell_for_row(users_page.user_row.first)).to_have_text(role_before)

        with allure.step("Step 8 — Verify no unexpected console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
