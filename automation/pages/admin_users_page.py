"""Users page object (Settings → Users, admin user management).

URL: /settings/users

Covers the page layout (header title, search input, batch Edit/Delete
buttons, invite "+" button) and the users table (``UsersTable.jsx``, built
on the shared ``grid-table`` components) — column headers, sort indicators,
select-all checkbox, and each user row's cell content + per-row action
icons.

Locator provenance (ELITEA-2292): ``users-page-title`` / ``users-search-input``
/ ``users-invite-button`` are call-site-only wiring of ``DrawerPageHeader``'s
already-threaded ``titleTestId`` / ``slotProps.searchInput.testId`` /
``slotProps.addButton.testId`` props. ``user-select-all-checkbox`` and
``user-column-header-*`` are call-site-only wiring of ``GridTableHeader``'s
already-threaded ``selectAllCheckboxTestId`` / ``columnTestIdPrefix`` props.
``user-row`` / ``user-row-checkbox`` / ``user-row-name`` are call-site-only
wiring of ``GridTableRow``'s already-threaded ``data-testid`` /
``checkboxTestId`` / ``nameCellTestId`` props. ``users-header-edit-button`` /
``users-header-delete-button`` (and the reused ``user-row-edit-button`` /
``user-row-delete-button`` per-row instances) are a NEW ``testId`` prop added
to ``EditUsersButton``/``DeleteUserButton`` (neither had any testid support
before this case). ``user-column-value-{email,last_login,roles}`` are a NEW
``dataCellTestIdPrefix`` prop threaded ``GridTableRow`` -> ``GridTableRowDataCell``,
mirroring ``GridTableHeader``'s existing ``columnTestIdPrefix`` ->
``{prefix}-column-header-{field}`` mechanism, applied to data cells instead
of header cells.

Live-discovered precondition (ELITEA-2292, implementer exploration): Settings
-> Users is hidden for the acting user's PRIVATE project — ``Settings.jsx``'s
``isPrivateProject`` guard effect redirects ``tab === 'users'`` to
``project-general`` once project data resolves (~2-3s after navigation). The
env's ``ELITEA_PROJECT_ID`` (399 in ``.env.test``) IS this test user's private
project, so a bare ``navigate("/settings/users")`` against it always loses the
race and lands on ``/settings/project-general`` instead. The AFS's own
Preconditions/Test Data section already named a different, TEAM project —
id 400 ("UI Testing") — as where the case's 2 users were confirmed live;
:meth:`navigate` switches to that project first (see
``settings.users_team_project_id``, sourced from ``USERS_TEAM_PROJECT_ID`` in
``.env.test`` — see ``config.py`` for why this is a DISTINCT key from the
existing, unrelated ``ELITEA_TEAM_PROJECT_ID``) so the guard never fires.
"""

import logging

from playwright.sync_api import Page, Response

from config import settings

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.admin_users")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substrings shared by the two page-mount GETs the table depends on
# (`useUserListQuery` / `useRoleListQuery`) — used to wait for both to
# resolve before asserting on the rendered table/columns.
USERS_LIST_URL_SUBSTRING = "/admin/users/default/"
ROLES_LIST_URL_SUBSTRING = "/admin/roles/default/"


class AdminUsersPage(BasePage):
    """Settings → Users page (page layout + users table)."""

    page_title = LocatorDescriptor(
        testid="users-page-title",
        description='Page header title — exact text "Users"',
    )
    search_input = LocatorDescriptor(
        testid="users-search-input",
        description='Users search input — placeholder "Search " (trailing space)',
    )
    header_edit_button = LocatorDescriptor(
        testid="users-header-edit-button",
        description="Header batch-Edit (pencil) button — disabled with no rows selected",
    )
    header_delete_button = LocatorDescriptor(
        testid="users-header-delete-button",
        description="Header batch-Delete (trash) button — disabled with no rows selected",
    )
    invite_button = LocatorDescriptor(
        testid="users-invite-button",
        description='Invite-users "+" button, top-right of the header',
    )
    select_all_checkbox = LocatorDescriptor(
        testid="user-select-all-checkbox",
        description="Table header select-all checkbox",
    )
    user_row = LocatorDescriptor(
        testid="user-row",
        description="User table row (repeatable, one per visible row)",
    )
    column_header_name = LocatorDescriptor(
        testid="user-column-header-name",
        description='Table column header — "Name" (sortable)',
    )
    column_header_email = LocatorDescriptor(
        testid="user-column-header-email",
        description='Table column header — "Email" (sortable)',
    )
    column_header_last_login = LocatorDescriptor(
        testid="user-column-header-last_login",
        description='Table column header — "Last login" (sortable)',
    )
    column_header_roles = LocatorDescriptor(
        testid="user-column-header-roles",
        description='Table column header — "Role" (non-sortable)',
    )
    column_header_actions = LocatorDescriptor(
        testid="user-column-header-actions",
        description='Table column header — "Actions" (non-sortable)',
    )

    # Sidebar project-selector combobox — pre-existing testid, duplicated
    # here (not cross-imported from ChatPage) per the project's page-object
    # convention (same shape as ToolkitDetailPage.SELECT_OPTION). Needed as
    # a navigation precondition — see the module docstring's "Live-discovered
    # precondition" note.
    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger-combobox",
        description="Sidebar project selector combobox trigger.",
    )

    # Scoped sub-selectors — count/prefix assertions and per-row cell lookups,
    # per .agents/testing.md § Locator policy (UPPER_CASE class constants).
    # Row-cell testids repeat once per row (not row-unique), so every getter
    # below chains off `self.user_row.first` — the sanctioned "locating
    # within an already-testid-scoped element" pattern.
    COLUMN_HEADER_PREFIX_SELECTOR = '[data-testid^="user-column-header-"]'
    USER_ROW_CHECKBOX_SELECTOR = '[data-testid="user-row-checkbox"]'
    USER_ROW_NAME_SELECTOR = '[data-testid="user-row-name"]'
    USER_COLUMN_VALUE_EMAIL_SELECTOR = '[data-testid="user-column-value-email"]'
    USER_COLUMN_VALUE_LAST_LOGIN_SELECTOR = '[data-testid="user-column-value-last_login"]'
    USER_COLUMN_VALUE_ROLES_SELECTOR = '[data-testid="user-column-value-roles"]'
    USER_ROW_EDIT_BUTTON_SELECTOR = '[data-testid="user-row-edit-button"]'
    USER_ROW_DELETE_BUTTON_SELECTOR = '[data-testid="user-row-delete-button"]'
    # Project-selector dropdown options — same shared select-option-{value}
    # family (SingleSelectMenuItem.jsx) as ChatPage.SELECT_OPTION /
    # ToolkitDetailPage.SELECT_OPTION — reuse the pattern, don't invent a new one.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_users_list_response(self, response: Response) -> bool:
        """True for the user-list GET (`useUserListQuery`)."""
        return (
            USERS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def _is_roles_list_response(self, response: Response) -> bool:
        """True for the role-list GET (`useRoleListQuery`)."""
        return (
            ROLES_LIST_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def ensure_team_project_selected(
        self, project_id: str = settings.users_team_project_id, timeout: int = NAVIGATION_TIMEOUT
    ) -> None:
        """Switch the sidebar's active project to *project_id*.

        Precondition for reaching Settings -> Users at all — see the module
        docstring's "Live-discovered precondition" note. Every fresh test
        browser context starts on this user's default (private) project, so
        this always performs the switch rather than checking first —
        re-selecting an already-active project is a safe no-op click.
        """
        self.project_selector_trigger.click()
        option = self.page.locator(self.SELECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=timeout)

    def navigate(self) -> tuple[Response, Response]:
        """Ensure the team project is selected, navigate to /settings/users,
        and wait for the first user row to become visible.

        Two-hop navigation: Settings -> Users is hidden/redirected away for
        the acting user's PRIVATE project (see module docstring), so this
        first lands on the always-reachable `/settings/project-general` tab,
        switches the active project, THEN navigates to `/settings/users` —
        by which point the guard's `isPrivateProject` check is already false
        and never fires.

        Waiting on the row (not just DOM visibility of the page shell)
        confirms the populated table path was reached rather than the
        `GridTableContainer` empty-state (`emptyMessage="No users"`) — per
        the AFS's precondition proof (step 1).

        Returns the (users-list, roles-list) driving GET responses so the
        caller can assert both resolved 200 OK (AFS step 7).
        """
        super().navigate("/settings/project-general")
        self.ensure_team_project_selected()

        with self.page.expect_response(
            self._is_users_list_response, timeout=NAVIGATION_TIMEOUT
        ) as users_resp_info, self.page.expect_response(
            self._is_roles_list_response, timeout=NAVIGATION_TIMEOUT
        ) as roles_resp_info:
            super().navigate("/settings/users")
        self.user_row.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        return users_resp_info.value, roles_resp_info.value

    def get_column_header_count(self) -> int:
        """Return the number of rendered table column-header elements
        (matched by the shared ``user-column-header-`` prefix)."""
        return self.page.locator(self.COLUMN_HEADER_PREFIX_SELECTOR).count()

    def get_column_sort_icon_count(self, column_header) -> int:
        """Return the number of ``<svg>`` sort-indicator icons rendered
        inside *column_header* (a Locator for one of the
        ``column_header_*`` fields above — sanctioned chaining off an
        already-testid-scoped element)."""
        return column_header.locator("svg").count()

    def is_select_all_checked(self) -> bool:
        """Return whether the select-all checkbox is checked.

        The ``user-select-all-checkbox`` testid lands on the MUI Checkbox
        ROOT ``<span>`` (SwitchBase), not the nested ``<input>`` —
        ``is_checked()`` raises "Not a checkbox or radio button" on it.
        Same workaround as ``NotificationCenterPage``: read the class list
        and check for ``Mui-checked``.
        """
        class_attr = self.select_all_checkbox.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def get_first_row_checkbox(self):
        """Return the row-checkbox Locator for the FIRST user row (scoped
        chaining off :attr:`user_row`)."""
        return self.user_row.first.locator(self.USER_ROW_CHECKBOX_SELECTOR)

    def get_first_row_name_cell(self):
        """Return the Name-cell Locator for the FIRST user row."""
        return self.user_row.first.locator(self.USER_ROW_NAME_SELECTOR)

    def get_first_row_email_cell(self):
        """Return the Email-cell Locator for the FIRST user row."""
        return self.user_row.first.locator(self.USER_COLUMN_VALUE_EMAIL_SELECTOR)

    def get_first_row_last_login_cell(self):
        """Return the Last-login-cell Locator for the FIRST user row."""
        return self.user_row.first.locator(self.USER_COLUMN_VALUE_LAST_LOGIN_SELECTOR)

    def get_first_row_role_cell(self):
        """Return the Role-cell Locator for the FIRST user row."""
        return self.user_row.first.locator(self.USER_COLUMN_VALUE_ROLES_SELECTOR)

    def get_first_row_edit_button(self):
        """Return the row-level Edit (pencil) icon Locator for the FIRST
        user row."""
        return self.user_row.first.locator(self.USER_ROW_EDIT_BUTTON_SELECTOR)

    def get_first_row_delete_button(self):
        """Return the row-level Delete (trash) icon Locator for the FIRST
        user row."""
        return self.user_row.first.locator(self.USER_ROW_DELETE_BUTTON_SELECTOR)
