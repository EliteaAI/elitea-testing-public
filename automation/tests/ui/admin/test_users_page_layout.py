"""UI test — Users page loads with correct layout and components.

Read-only verification against the logged-in admin's existing project user
data (`.agents/testing.md` § Test data strategy — prefer read-only
assertions on existing data when the observable doesn't require fresh
state). This case never creates, edits, or deletes a user. If the active
project's users are ever bulk-removed, this test will correctly go RED for
a genuinely missing precondition — the page renders `GridTableContainer`'s
``emptyMessage="No users"`` instead of the table when the user list is
empty (see AFS § Preconditions) — though in practice this floor is
self-guaranteed since the acting admin is always a member of its own
project's user list.

Test case: ELITEA-2292
AFS: test-specs/settings-users-and-roles/l2_users-page-layout-and-components_ELITEA-2292.md
"""

import logging
import re

import allure
import pytest
from pages.admin_users_page import AdminUsersPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

EXPECTED_COLUMN_COUNT = 5
EXPECTED_SEARCH_PLACEHOLDER = "Search "
SORTABLE_COLUMN_ATTRS = ("column_header_name", "column_header_email", "column_header_last_login")
NON_SORTABLE_COLUMN_ATTRS = ("column_header_roles", "column_header_actions")
EMAIL_PATTERN = re.compile(r".+@.+\..+")
ISO_LAST_LOGIN_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


class TestUsersPageLayout:
    """ELITEA-2292 — Users page loads with correct layout and components."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2292_users-page-loads-with-correct-layout-and-components.md",
        "onetest-ai Test Case link",
    )
    def test_users_page_layout_and_components(self, page):
        """Page header, search input, batch Edit/Delete/Invite buttons,
        5-column table (with correct per-column sortability), and the
        first row's cell content + action icons all render as specified;
        no console errors/warnings and both driving list-fetch GETs
        resolve 200 OK."""
        users_page = AdminUsersPage(page)

        # Registered before Step 1 so console errors/warnings from the
        # whole page-load flow are captured. AFS Expected Results say
        # "no console error or warning" — both message types matched, per
        # .agents/memory/test-automation-engineer/console_side_channel_checks.md.
        console_issues = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type in ("error", "warning"):
                console_issues.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users: user rows become visible "
            "(confirms the page loaded past the loading spinner AND the "
            "empty-state precondition did not trigger)"
        ):
            users_list_response, roles_list_response = users_page.navigate()
            row_count = users_page.user_row.count()
            assert row_count > 0, (
                f"Expected the users table to render at least one row, got {row_count}"
            )

        with allure.step('Step 2 — Verify the page header shows "Users"'):
            assert users_page.page_title.text_content() == "Users", (
                f"Expected page header text 'Users', got "
                f"{users_page.page_title.text_content()!r}"
            )

        with allure.step(
            "Step 3 — Verify the header-level components: search input "
            "(exact placeholder), header batch-Edit/Delete buttons visible "
            "and disabled (no rows selected), invite '+' button visible and "
            "enabled"
        ):
            assert users_page.search_input.is_visible(), (
                "Expected the users search input to be visible"
            )
            placeholder = users_page.search_input.get_attribute("placeholder")
            assert placeholder == EXPECTED_SEARCH_PLACEHOLDER, (
                f"Expected search input placeholder {EXPECTED_SEARCH_PLACEHOLDER!r}, "
                f"got {placeholder!r}"
            )

            assert users_page.header_edit_button.is_visible(), (
                "Expected the header batch-Edit button to be visible"
            )
            assert users_page.header_edit_button.is_disabled(), (
                "Expected the header batch-Edit button to be disabled with no "
                "rows selected"
            )

            assert users_page.header_delete_button.is_visible(), (
                "Expected the header batch-Delete button to be visible"
            )
            assert users_page.header_delete_button.is_disabled(), (
                "Expected the header batch-Delete button to be disabled with no "
                "rows selected"
            )

            assert users_page.invite_button.is_visible(), (
                "Expected the invite-users '+' button to be visible"
            )
            assert users_page.invite_button.is_enabled(), (
                "Expected the invite-users '+' button to be enabled"
            )

        with allure.step(
            "Step 4 — Verify the table header shows a select-all checkbox, "
            "present and unchecked"
        ):
            assert users_page.select_all_checkbox.is_visible(), (
                "Expected the select-all checkbox to be visible"
            )
            assert not users_page.is_select_all_checked(), (
                "Expected the select-all checkbox to be unchecked on initial load"
            )

        with allure.step(
            "Step 5 — Verify exactly 5 field columns (Name, Email, Last login, "
            "Role, Actions) with correct labels and per-column sortability "
            "(sort-indicator icon present for Name/Email/Last login, absent "
            "for Role/Actions)"
        ):
            header_count = users_page.get_column_header_count()
            assert header_count == EXPECTED_COLUMN_COUNT, (
                f"Expected exactly {EXPECTED_COLUMN_COUNT} column headers, "
                f"got {header_count}"
            )

            expected_labels = {
                "column_header_name": "Name",
                "column_header_email": "Email",
                "column_header_last_login": "Last login",
                "column_header_roles": "Role",
                "column_header_actions": "Actions",
            }
            for attr_name, expected_label in expected_labels.items():
                header = getattr(users_page, attr_name)
                actual_label = header.text_content()
                assert actual_label == expected_label, (
                    f"Expected {attr_name} column header {expected_label!r}, "
                    f"got {actual_label!r}"
                )

            for attr_name in SORTABLE_COLUMN_ATTRS:
                column_field = attr_name.removeprefix("column_header_")
                sort_icon_count = users_page.get_column_sort_icon_count(column_field)
                assert sort_icon_count == 1, (
                    f"Expected a sort-indicator icon on sortable column "
                    f"{attr_name}, got {sort_icon_count}"
                )

            for attr_name in NON_SORTABLE_COLUMN_ATTRS:
                column_field = attr_name.removeprefix("column_header_")
                sort_icon_count = users_page.get_column_sort_icon_count(column_field)
                assert sort_icon_count == 0, (
                    f"Expected NO sort-indicator icon on non-sortable column "
                    f"{attr_name}, got {sort_icon_count}"
                )

        with allure.step(
            "Step 6 — For the first user row: verify row checkbox present, "
            "non-empty Name, email-shaped Email, ISO-datetime-shaped Last "
            "login, non-empty Role, and both Edit/Delete action icons visible"
        ):
            assert users_page.get_first_row_checkbox().is_visible(), (
                "Expected the first row's checkbox to be visible"
            )

            name_text = users_page.get_first_row_name_cell().text_content() or ""
            assert name_text.strip() != "", "Expected the first row's Name cell to be non-empty"

            email_text = users_page.get_first_row_email_cell().text_content() or ""
            assert EMAIL_PATTERN.match(email_text), (
                f"Expected the first row's Email cell to match an email pattern, "
                f"got {email_text!r}"
            )

            last_login_text = users_page.get_first_row_last_login_cell().text_content() or ""
            assert ISO_LAST_LOGIN_PATTERN.match(last_login_text), (
                f"Expected the first row's Last login cell to match ISO datetime "
                f"format {ISO_LAST_LOGIN_PATTERN.pattern!r}, got {last_login_text!r}"
            )

            role_text = users_page.get_first_row_role_cell().text_content() or ""
            assert role_text.strip() != "", "Expected the first row's Role cell to be non-empty"

            assert users_page.get_first_row_edit_button().is_visible(), (
                "Expected the first row's Edit icon to be visible"
            )
            assert users_page.get_first_row_delete_button().is_visible(), (
                "Expected the first row's Delete icon to be visible"
            )

        with allure.step(
            "Step 7 — Verify no console errors/warnings and both driving "
            "list-fetch requests (users, roles) resolved 200 OK"
        ):
            assert users_list_response.status == 200, (
                f"Expected the users-list GET to resolve 200, got "
                f"{users_list_response.status}"
            )
            assert roles_list_response.status == 200, (
                f"Expected the roles-list GET to resolve 200, got "
                f"{roles_list_response.status}"
            )
            assert not console_issues and not page_errors, (
                "Expected no console errors/warnings and no uncaught page "
                f"errors, got console_issues={[(m.type, m.text) for m in console_issues]!r}, "
                f"page_errors={page_errors!r}"
            )
