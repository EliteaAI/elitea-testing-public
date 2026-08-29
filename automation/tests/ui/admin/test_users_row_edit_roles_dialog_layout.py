"""UI test — Row Edit-roles dialog opens with correct layout and current role pre-selected.

Read-only verification: the per-row "Edit roles" dialog is opened purely to
READ its layout and is dismissed via its Close (x). Save is never clicked and
cannot be — it stays disabled until a role actually changes
(``EditUserRolesDialog.jsx``: ``disabled={!selectedRoles.length ||
!hasChangedRoles}``). Step 8's unchanged-role assertion is the cleanliness
proof, not an assumption.

Every asserted value is produced by the system: the subject row's current role
is READ off the rendered table at runtime and then used to build the expected
chip / checkmark handles, so the test never asserts a role it authored. Nothing
is mocked, injected or stubbed.

⚠️ The case text quotes the dialog description WITHOUT the word "user"
("Select the roles to define permissions for this project."). The product
renders "Select the roles to define user permissions for this project."
(``EditUserRolesDialog.jsx``). The product is ground truth and is what this
test asserts — weakening the assertion toward the stale case text would be
reverse-masking. Case-text clarification filed; see the AFS § Known Defects.

Test case: ELITEA-2301
AFS: test-specs/settings-users-and-roles/l3_edit-roles-dialog-layout-and-current-role_ELITEA-2301.md
"""

import logging

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

EXPECTED_TITLE = "Edit roles"
EXPECTED_DESCRIPTION = "Select the roles to define user permissions for this project."


class TestUsersRowEditRolesDialogLayout:
    """ELITEA-2301 — Edit roles dialog layout and pre-selected current role."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2301_edit-roles-dialog-opens-with-correct-layout-and-current-role.md",
        "onetest-ai Test Case link",
    )
    def test_row_edit_roles_dialog_layout_and_current_role(self, page):
        """The per-row Edit-roles dialog renders its title, description, the
        user's current role as a removable chip, that role checkmarked in the
        dropdown, and a working Close (x) — leaving the role unchanged."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users: the populated table renders; "
            "capture the first row's current role"
        ):
            users_page.navigate()
            expect(users_page.user_row.first).to_be_visible()
            first_row = users_page.user_row.first
            current_roles = users_page.get_row_role_set(first_row)
            assert len(current_roles) == 1, (
                "This case's subject must hold exactly one role for its "
                f"'current role as a chip' assertions to be meaningful, got {current_roles!r}"
            )
            current_role = next(iter(current_roles))
            logger.info("Subject row's current role: %s", current_role)

        with allure.step(
            "Step 2 — Click the Edit (pencil) icon on the first user row: the "
            '"Edit roles" dialog opens'
        ):
            users_page.open_row_edit_roles_dialog(first_row)
            expect(users_page.row_edit_roles_dialog).to_be_visible()

        with allure.step('Step 3 — The dialog title is exactly "Edit roles"'):
            expect(users_page.row_edit_roles_title).to_have_text(EXPECTED_TITLE)

        with allure.step(
            "Step 4 — The dialog description is exactly the product's string "
            '("...define USER permissions..." — the case text omits "user"; '
            "the product is ground truth)"
        ):
            expect(users_page.row_edit_roles_description).to_have_text(EXPECTED_DESCRIPTION)

        with allure.step(
            "Step 5 — The Roles multi-select shows the user's current role as a "
            "single removable chip"
        ):
            expect(users_page.get_selected_role_chips_locator()).to_have_count(1)
            assert users_page.get_selected_role_chip_values() == [current_role], (
                f"Expected exactly the row's current role {current_role!r} as a chip, got "
                f"{users_page.get_selected_role_chip_values()!r}"
            )
            expect(users_page.get_role_chip(current_role)).to_have_text(current_role)
            expect(
                page.locator(users_page.SELECT_VALUE_CHIP_REMOVE.format(current_role))
            ).to_be_visible()

        with allure.step(
            "Step 6 — Open the Roles dropdown: the currently assigned role — and "
            "only it — carries the selected checkmark"
        ):
            users_page.open_roles_menu(users_page.row_edit_roles_select_combobox)
            expect(users_page.get_option_selected_icon_locator()).to_have_count(1)
            selected_option = users_page.get_role_option(current_role)
            expect(
                selected_option.locator(users_page.SELECT_OPTION_SELECTED_ICON_SELECTOR)
            ).to_have_count(1)
            for other_role in users_page.get_role_option_texts():
                if other_role == current_role:
                    continue
                expect(
                    users_page.get_role_option(other_role).locator(
                        users_page.SELECT_OPTION_SELECTED_ICON_SELECTOR
                    )
                ).to_have_count(0)

        with allure.step(
            "Step 7 — Close the menu, then dismiss the dialog with the Close (x) "
            "button in the top right: the dialog unmounts"
        ):
            users_page.close_roles_menu()
            expect(users_page.row_edit_roles_close_button).to_be_visible()
            users_page.close_row_edit_roles_dialog_via_close_button()
            expect(users_page.row_edit_roles_dialog).to_have_count(0)

        with allure.step(
            "Step 8 — The subject row's Role column is unchanged — the read-only "
            "visit mutated nothing"
        ):
            assert users_page.get_row_role_set(users_page.user_row.first) == current_roles, (
                f"Expected the first row's role to remain {current_roles!r} after opening and "
                f"dismissing the dialog, got {users_page.get_row_role_set(users_page.user_row.first)!r}"
            )

        with allure.step("Step 9 — No unexpected console errors across the flow"):
            # Known defect: #1971 — the project switch this page object performs
            # reopens EliteaUI's `toolkitTypes` project-id race, 404-ing on a
            # project-id-less URL. URL-keyed exclusion, never status-code-keyed.
            unexpected = exclude_known_defect_urls(
                console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
            )
            assert not unexpected, f"Unexpected console errors: {unexpected}"
