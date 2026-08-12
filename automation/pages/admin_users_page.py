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

    # --- Invite-users dialog (ELITEA-2304 — batch-edit-roles seed step) ---
    # `emailsInputTestId` / `roleSelectTestId` / `confirmButtonTestId` newly
    # threaded through InviteUserDialog -> Users.jsx's call site
    # (EliteaAI/EliteaUI@ed2ddbb9) — the dialog previously had ZERO testids
    # wired despite the case's AFS assuming otherwise; confirmed live during
    # implementer exploration. Cancel is intentionally NOT wired — this
    # case's steps never click it (canon ruling #511 scope discipline).
    invite_emails_input = LocatorDescriptor(
        testid="users-invite-emails-input",
        description="Invite-users dialog — comma-separated emails textarea",
    )
    invite_role_select_combobox = LocatorDescriptor(
        testid="users-invite-role-select-combobox",
        description="Invite-users dialog — Roles multi-select combobox trigger",
    )
    invite_confirm_button = LocatorDescriptor(
        testid="users-invite-confirm-button",
        description='Invite-users dialog — "Invite" confirm button',
    )
    # `emailsErrorTestId` newly threaded through InviteUserDialog ->
    # Users.jsx's call site (ELITEA-2307, EliteaAI/EliteaUI@8bda203c) — the
    # dialog's inline email-validation `<FormHelperText>` previously had NO
    # testid support at all. Renders only while `error` is true (blur-gated,
    # see `type_invalid_email_and_blur()` below), so presence itself is the
    # error-state signal.
    invite_emails_error_text = LocatorDescriptor(
        testid="users-invite-emails-error-text",
        description='Invite-users dialog — inline "Invalid email: {email}" validation error text',
    )

    # --- Edit roles dialog (header batch-edit — ELITEA-2304) ---
    # `dialogTestId` / `titleTestId` / `roleSelectTestId` / `saveButtonTestId`
    # newly threaded through EditUserRolesDialog -> Users.jsx's HEADER
    # (isBatchEdit) call site only (EliteaAI/EliteaUI@435ff111) — never at
    # the per-row call site, which this case never opens. Cancel likewise
    # not wired (never clicked by this case).
    edit_roles_dialog = LocatorDescriptor(
        testid="users-edit-roles-dialog",
        description="Batch-edit 'Edit roles' dialog root",
    )
    edit_roles_dialog_title = LocatorDescriptor(
        testid="users-edit-roles-title",
        description='Batch-edit dialog title — exact text "Edit roles"',
    )
    edit_roles_select_combobox = LocatorDescriptor(
        testid="users-edit-roles-select-combobox",
        description="Batch-edit dialog — Roles multi-select combobox trigger",
    )
    edit_roles_save_button = LocatorDescriptor(
        testid="users-edit-roles-save-button",
        description="Batch-edit dialog — Save button (disabled until a role changes)",
    )

    # --- Delete-confirmation dialog (generic Modal.DeleteEntityModal) ---
    # Pre-existing shared component testid (also used by
    # PersonalTokensPage's cleanup flow) — reused as-is, not newly added.
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Delete-confirmation dialog — Delete button",
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
    # Sort-indicator icon on a sortable column header — dynamic testid,
    # component-level addition to GridTableHeader.jsx mirroring its existing
    # `columnTestIdPrefix` mechanism (EliteaAI/EliteaUI@52582fe3, ELITEA-2292
    # fix round 2). Rendered only when the column is sortable, so presence
    # (count 1 vs 0) is itself the sortable/non-sortable signal — no raw
    # `svg` chaining needed. Deliberately NOT prefixed `user-column-header-`
    # (unlike the header-cell testid) — that prefix is also matched by
    # COLUMN_HEADER_PREFIX_SELECTOR above, and a sort-icon testid sharing it
    # would double-count in get_column_header_count() for every sortable
    # column (caught live: 8 vs expected 5 on first run).
    COLUMN_SORT_ICON_SELECTOR = '[data-testid="user-sort-icon-{}"]'

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

    def _is_users_post_response(self, response: Response) -> bool:
        """True for the invite-users POST (ELITEA-2304 — confirmed live:
        `POST /admin/users/default/{project}`, 200 OK)."""
        return (
            USERS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "POST"
        )

    def _is_users_put_response(self, response: Response) -> bool:
        """True for the batch-edit-roles PUT (AFS step 7 — 200 OK,
        `{"msg": "roles updated"}`)."""
        return (
            USERS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "PUT"
        )

    def _is_users_delete_response(self, response: Response) -> bool:
        """True for the per-user delete DELETE (cleanup — 204 No Content)."""
        return (
            USERS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "DELETE"
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

    def get_column_sort_icon_count(self, column_field: str) -> int:
        """Return the count of the sort-indicator icon testid element for
        *column_field* (the raw column key, e.g. ``"name"``, ``"roles"`` —
        NOT the ``column_header_*`` attribute name). 1 for a sortable
        column, 0 for a non-sortable one — see
        ``COLUMN_SORT_ICON_SELECTOR``."""
        return self.page.locator(self.COLUMN_SORT_ICON_SELECTOR.format(column_field)).count()

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

    # --- Row lookup by visible text (ELITEA-2304) ---
    def get_row_by_text(self, text: str):
        """Return the user-row Locator filtered by row text match on *text*
        (sanctioned chaining off the already-testid-scoped :attr:`user_row`,
        same pattern as ``PersonalTokensPage.get_row_by_name``).

        Used both for pre-existing users (match on Name, e.g. "Levon
        Dadayan") and for seeded/invited users (match on email — an
        invited-but-not-yet-logged-in row renders an EMPTY Name cell
        (``user-row-name``), with the invited address only in the Email
        column; live-confirmed during ELITEA-2304 implementer exploration,
        contradicting the AFS's original "Name = the email itself"
        assumption, which was amended)."""
        return self.user_row.filter(has_text=text)

    def is_row_checkbox_checked(self, row) -> bool:
        """Return whether *row*'s own checkbox is checked.

        Same ``Mui-checked`` class-list workaround as
        :meth:`is_select_all_checked` — the ``user-row-checkbox`` testid
        lands on the MUI Checkbox ROOT ``<span>``, not the nested
        ``<input>``."""
        checkbox = row.locator(self.USER_ROW_CHECKBOX_SELECTOR)
        class_attr = checkbox.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def select_user_row(self, row) -> None:
        """Check *row*'s own checkbox (a Locator returned by
        :meth:`get_row_by_text`) — never select-all."""
        row.locator(self.USER_ROW_CHECKBOX_SELECTOR).click()

    def get_role_cell_for_row(self, row):
        """Return the Role-cell Locator scoped within *row*."""
        return row.locator(self.USER_COLUMN_VALUE_ROLES_SELECTOR)

    # --- Invite-users dialog flow (ELITEA-2304 seed step) ---
    def open_invite_dialog(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the '+' Invite-users button and wait for the dialog's
        emails input to become visible."""
        self.invite_button.click()
        self.invite_emails_input.wait_for(state="visible", timeout=timeout)

    def type_email_in_invite_dialog(self, email: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Type *email* into the Invite dialog's Emails field WITHOUT
        blurring it (ELITEA-2307).

        Deliberately does NOT reuse :meth:`invite_users` — that method
        fills, selects a role, and clicks Invite, awaiting the resulting
        POST; this case never reaches that request (the Invite button
        stays disabled on an invalid-email error). Split from
        :meth:`blur_invite_emails_field` (rather than one combined
        fill-and-blur helper) because validation is blur-gated, not
        live-as-you-type (confirmed via ``InviteUserDialog.jsx`` source +
        live re-check: ``onChange`` only updates local state, ``onBlur`` is
        what calls ``parseEmails`` and sets ``error``/``helperText``) — a
        caller must be able to assert "no error yet" in between the two
        calls.
        """
        self.invite_emails_input.fill(email, timeout=timeout)

    def blur_invite_emails_field(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Blur the Invite dialog's Emails field (Tab) to trigger
        validation — see :meth:`type_email_in_invite_dialog`."""
        self.invite_emails_input.press("Tab", timeout=timeout)

    def _select_multi_select_role_and_close(self, combobox, role: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Select *role* in *combobox*'s currently-closed Roles multi-select,
        then close the opened listbox.

        Both the Invite-users and Edit-roles dialogs use a `multiple` MUI
        Select (``Select.SingleSelect`` with ``multiple`` + ``showBorder`` —
        selecting an option does NOT auto-close the popover, unlike a
        single-select. Same pattern as
        ``PipelineDetailPage._select_multi_select_option_and_close``: close
        via Escape (consumed by the MUI Menu's own handler before it can
        bubble to the dialog's Escape-closes-dialog handler — confirmed
        live, the Edit-roles dialog stays open)."""
        combobox.click(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(role))
        option.wait_for(state="visible", timeout=timeout)
        option.click(timeout=timeout)
        self.page.keyboard.press("Escape")

    def select_role_in_invite_dialog(self, role: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Open the Invite dialog's Roles select and choose *role*."""
        self._select_multi_select_role_and_close(self.invite_role_select_combobox, role, timeout=timeout)

    def invite_users(self, emails: list[str], role: str, timeout: int = NAVIGATION_TIMEOUT) -> Response:
        """Fill the emails textarea, select *role*, and click Invite.

        Returns the driving invite POST response (confirmed live:
        ``POST /admin/users/default/{project}``, 200 OK).
        """
        self.invite_emails_input.fill(",".join(emails))
        self.select_role_in_invite_dialog(role, timeout=timeout)
        with self.page.expect_response(self._is_users_post_response, timeout=timeout) as post_info:
            self.invite_confirm_button.click()
        return post_info.value

    # --- Edit-roles dialog flow (header batch-edit — ELITEA-2304) ---
    def open_edit_roles_dialog(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the header batch-Edit button and wait for the "Edit roles"
        dialog to open."""
        self.header_edit_button.click()
        self.edit_roles_dialog.wait_for(state="visible", timeout=timeout)

    def select_role_in_edit_dialog(self, role: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Open the Edit-roles dialog's Roles select and choose *role*."""
        self._select_multi_select_role_and_close(self.edit_roles_select_combobox, role, timeout=timeout)

    def save_edit_roles(self, timeout: int = NAVIGATION_TIMEOUT) -> tuple[Response, Response]:
        """Click Save in the Edit-roles dialog and return the (PUT, refetch
        GET) driving responses (AFS step 7 — PUT 200 OK with body
        ``{"msg": "roles updated"}``, and the users list re-fetches)."""
        with self.page.expect_response(
            self._is_users_put_response, timeout=timeout
        ) as put_info, self.page.expect_response(
            self._is_users_list_response, timeout=timeout
        ) as refetch_info:
            self.edit_roles_save_button.click()
        return put_info.value, refetch_info.value

    # --- Cleanup: row-level delete (ELITEA-2304 — mandatory teardown) ---
    def delete_user_row(self, row, timeout: int = NAVIGATION_TIMEOUT) -> Response:
        """Click *row*'s Delete icon, confirm in the delete-confirmation
        dialog, and return the driving DELETE response (204 No Content)."""
        row.locator(self.USER_ROW_DELETE_BUTTON_SELECTOR).click()
        self.delete_confirm_button.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(self._is_users_delete_response, timeout=timeout) as delete_info:
            self.delete_confirm_button.click()
        return delete_info.value
