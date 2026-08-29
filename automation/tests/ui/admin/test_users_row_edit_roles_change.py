"""UI test (FAMILY) — Change / multi-assign a user's roles via the row Edit-roles dialog.

One parameterized spec, one row per TMS case, each row asserting its OWN
expected role set:

* **ELITEA-2302** — remove the seeded ``viewer`` chip via its x, pick
  ``editor``: the Role column becomes exactly ``editor``.
* **ELITEA-2303** — keep the seeded role and add ``editor`` + ``admin``: the
  Role column lists all three. The multi-select ADDS; the case never removes
  the existing role, so its own expected value legitimately includes it.

Both rows drive the SAME product flow (seed -> row Edit dialog -> manipulate
the Roles multi-select -> Save -> Role column -> reload), which is why they are
one family rather than two near-identical specs.

**Subject is a SEEDED disposable user, never a pre-existing row.** Project 400
is the only project this account can mutate, and its non-seeded rows are the
acting automation account itself (losing its ``admin`` would strand every test
on this surface) and a real human. Inviting is instant and needs no acceptance,
so the case's "a user with viewer role" / "any user" is satisfied honestly by a
row this test creates and deletes. The seeded user is removed in a ``finally``
regardless of outcome.

Nothing about the system under test is substituted: the role change is driven
through the real dialog, asserted against the real PUT response and the real
re-fetched table, and re-read after a real page reload.

Test cases: ELITEA-2302, ELITEA-2303
AFS: test-specs/settings-users-and-roles/l3_change-and-multi-assign-roles-via-row-edit-dialog_ELITEA-2302.md
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

SEEDED_ROLE = "viewer"
ROW_WAIT_TIMEOUT = 15_000

TMS_CASE_URL = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/settings/users-and-roles/{}"
)
TMS_CASE_FILES = {
    "ELITEA-2302": "ELITEA-2302_change-a-users-role-via-edit-roles-dialog.md",
    "ELITEA-2303": "ELITEA-2303_assign-multiple-roles-to-a-user-via-edit-roles-dialog.md",
}

ROLE_CHANGE_CASES = [
    pytest.param(
        "ELITEA-2302",
        True,  # remove the seeded chip via its x — the case's own step 3
        ["editor"],
        {"editor"},
        id="ELITEA-2302",
    ),
    pytest.param(
        "ELITEA-2303",
        False,  # the case only ADDS roles; the seeded one stays
        ["editor", "admin"],
        {SEEDED_ROLE, "editor", "admin"},
        id="ELITEA-2303",
    ),
]


class TestUsersRowEditRolesChange:
    """ELITEA-2302 / ELITEA-2303 — role change and multi-role assignment."""

    @pytest.mark.parametrize(
        "case_id,remove_seeded_chip,roles_to_select,expected_roles", ROLE_CHANGE_CASES
    )
    def test_change_roles_via_row_edit_dialog(
        self, page, case_id, remove_seeded_chip, roles_to_select, expected_roles
    ):
        """Seed a disposable ``viewer`` user, change its roles through the
        per-row Edit-roles dialog, and verify the Role column and its
        persistence across a reload."""
        allure.dynamic.issue(
            TMS_CASE_URL.format(TMS_CASE_FILES[case_id]), "onetest-ai Test Case link"
        )
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)
        seeded_email = f"elitea-role-edit-{case_id.lower()}-{uuid.uuid4().hex[:8]}@example.com"
        seeded_row_present = False

        try:
            with allure.step("Step 1 — Navigate to Settings -> Users: the table renders"):
                users_page.navigate()
                expect(users_page.user_row.first).to_be_visible()
                # Captured, never hardcoded: this project's user list is shared,
                # persistent live data that drifts between runs (surface digest).
                initial_row_count = users_page.user_row.count()
                assert initial_row_count > 0, (
                    f"Expected the users table to render at least one row, got {initial_row_count}"
                )

            with allure.step(
                f"Step 2 — Seed: invite one disposable user with role '{SEEDED_ROLE}'; "
                "the table gains exactly that row"
            ):
                users_page.open_invite_dialog()
                invite_response = users_page.invite_users([seeded_email], SEEDED_ROLE)
                assert invite_response.status == 200, (
                    f"Expected 200 from the invite-users POST, got {invite_response.status}"
                )
                seeded_row_present = True
                expect(users_page.user_row).to_have_count(
                    initial_row_count + 1, timeout=ROW_WAIT_TIMEOUT
                )
                seeded_row = users_page.get_row_by_text(seeded_email)
                expect(seeded_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                assert users_page.get_row_role_set(seeded_row) == {SEEDED_ROLE}, (
                    f"Expected the seeded row to start with role {SEEDED_ROLE!r}, got "
                    f"{users_page.get_row_role_set(seeded_row)!r}"
                )

            with allure.step(
                "Step 3 — Click the Edit (pencil) icon on the seeded row: the dialog "
                "opens showing its current role as a chip, with Save disabled"
            ):
                users_page.open_row_edit_roles_dialog(seeded_row)
                expect(users_page.row_edit_roles_dialog).to_be_visible()
                expect(users_page.get_selected_role_chips_locator()).to_have_count(1)
                assert users_page.get_selected_role_chip_values() == [SEEDED_ROLE], (
                    f"Expected the dialog to open with the {SEEDED_ROLE!r} chip, got "
                    f"{users_page.get_selected_role_chip_values()!r}"
                )
                expect(users_page.row_edit_roles_save_button).to_be_disabled()

            if remove_seeded_chip:
                with allure.step(
                    f"Step 4 — Remove the '{SEEDED_ROLE}' chip by clicking its x: no chips "
                    "remain and Save is STILL disabled (an empty role set is not saveable)"
                ):
                    users_page.remove_role_chip(SEEDED_ROLE)
                    expect(users_page.get_selected_role_chips_locator()).to_have_count(0)
                    expect(users_page.row_edit_roles_save_button).to_be_disabled()

            with allure.step(
                f"Step 5 — Select {roles_to_select} in the Roles dropdown: the chips are "
                "exactly the expected roles and Save becomes enabled"
            ):
                for role in roles_to_select:
                    users_page.select_role_in_row_edit_dialog(role)
                expect(users_page.get_selected_role_chips_locator()).to_have_count(
                    len(expected_roles)
                )
                assert set(users_page.get_selected_role_chip_values()) == expected_roles, (
                    f"Expected chips {sorted(expected_roles)}, got "
                    f"{sorted(users_page.get_selected_role_chip_values())}"
                )
                expect(users_page.row_edit_roles_save_button).to_be_enabled()

            with allure.step(
                "Step 6 — Click Save: the driving PUT resolves 200, the dialog closes "
                "and the users list re-fetches"
            ):
                put_response, refetch_response = users_page.save_row_edit_roles()
                assert put_response.status == 200, (
                    f"Expected 200 from the edit-roles PUT, got {put_response.status}"
                )
                assert refetch_response.status == 200, (
                    f"Expected 200 from the users-list refetch GET, got {refetch_response.status}"
                )
                expect(users_page.row_edit_roles_dialog).to_have_count(0)

            with allure.step(
                f"Step 7 — The seeded user's Role column now lists exactly {sorted(expected_roles)}"
            ):
                seeded_row = users_page.get_row_by_text(seeded_email)
                role_cell = users_page.get_role_cell_for_row(seeded_row)
                # Waiting assertion first: the pre-save value must be gone before
                # the set is snapshotted, so a slow re-render can never be read as
                # a wrong role set.
                expect(role_cell).not_to_have_text(SEEDED_ROLE, timeout=ROW_WAIT_TIMEOUT)
                assert users_page.get_row_role_set(seeded_row) == expected_roles, (
                    f"Expected the Role column to read {sorted(expected_roles)} after saving, got "
                    f"{sorted(users_page.get_row_role_set(seeded_row))}"
                )

            with allure.step(
                "Step 8 — Reload the page: the role assignment persists server-side"
            ):
                users_page.reload_and_wait()
                seeded_row = users_page.get_row_by_text(seeded_email)
                expect(seeded_row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                assert users_page.get_row_role_set(seeded_row) == expected_roles, (
                    f"Expected the Role column to still read {sorted(expected_roles)} after a "
                    f"reload, got {sorted(users_page.get_row_role_set(seeded_row))}"
                )

            with allure.step("Step 9 — No unexpected console errors across the flow"):
                # Known defect: #1971 — the project switch this page object performs
                # reopens EliteaUI's `toolkitTypes` project-id race, 404-ing on a
                # project-id-less URL. URL-keyed exclusion, never status-code-keyed.
                unexpected = exclude_known_defect_urls(
                    console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
                )
                assert not unexpected, f"Unexpected console errors: {unexpected}"
        finally:
            # Cleanup (not an AFS case step — mandatory, unwrapped, runs regardless
            # of outcome): this case seeds a real, persistent row in shared live
            # project data. Same per-row delete flow ELITEA-2304 established, with
            # a WAITING presence check rather than an immediate snapshot so a
            # transient refetch window can never be misread as "already gone".
            if seeded_row_present:
                try:
                    leftover = users_page.get_row_by_text(seeded_email)
                    expect(leftover).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
                    delete_response = users_page.delete_user_row(leftover)
                    logger.info(
                        "Cleanup: deleted seeded user %s (status %s)",
                        seeded_email,
                        delete_response.status,
                    )
                except Exception:
                    logger.exception("Cleanup FAILED for seeded user %s", seeded_email)
                    raise
