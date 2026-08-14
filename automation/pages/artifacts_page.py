"""Artifacts Page Object for Elitea artifact storage.

Handles: /artifacts and /artifacts?bucket={bucket_name}

The Artifacts page has two panels:
- Left panel: bucket list (stored at Elitea S3 storage or external)
- Right panel: file list for the selected bucket

Actions:
- Navigate to artifacts
- Select a bucket by name
- List files in the selected bucket
- Check if a file exists
- Download a file (triggers browser download)
- Wait for page/bucket to load
"""

import logging
from playwright.sync_api import Page, Download

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.artifacts")


class ArtifactsPage(BasePage):
    """Page object for the Artifacts section.

    Manages bucket navigation and file operations (list, download).
    The page splits into a left bucket-list panel and a right file-list panel.
    Selecting a bucket updates the URL to ``/artifacts?bucket={name}``
    and renders the file table on the right.

    URL: /artifacts, /artifacts?bucket={bucket_name}
    """

    # ------------------------------------------------------------------
    # Left panel — bucket list
    # ------------------------------------------------------------------

    create_bucket_button = LocatorDescriptor(
        testid="artifacts-create-bucket-button",
        fallback=lambda page: page.get_by_label("Create bucket").locator("button"),
        description="Create bucket button in the left panel header",
    )

    search_buckets_button = LocatorDescriptor(
        testid="artifacts-search-buckets-button",
        fallback=lambda page: page.get_by_role("button", name="Search buckets"),
        description="Search buckets button in the left panel header",
    )

    # ------------------------------------------------------------------
    # Right panel — file list toolbar
    # ------------------------------------------------------------------

    file_search_input = LocatorDescriptor(
        testid="artifacts-file-search-input",
        fallback=lambda page: page.locator('main [role="main"] ~ * input[placeholder="Search"], '
                                           'main input[placeholder="Search"]').last,
        description="Search input in the right-panel file list toolbar",
    )

    upload_files_button = LocatorDescriptor(
        testid="artifacts-upload-files-button",
        fallback=lambda page: page.get_by_role("button", name="Upload files").last,
        description="Upload files button in the right-panel toolbar",
    )

    download_files_button = LocatorDescriptor(
        testid="artifacts-download-files-button",
        fallback=lambda page: page.get_by_label("Download files").locator("button"),
        description="Download selected files button (enabled after selecting files)",
    )

    # ------------------------------------------------------------------
    # Right panel — file table
    # ------------------------------------------------------------------

    empty_state_label = LocatorDescriptor(
        testid="artifacts-empty-state",
        fallback=lambda page: page.locator('main').get_by_text("No files in this bucket").last,
        description="Empty-state label shown when the selected bucket has no files",
    )

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to Artifacts")
    def navigate_to_artifacts(self) -> None:
        """Navigate to the Artifacts landing page and wait for it to load.

        Navigates to ``/artifacts`` and waits for the bucket list to render.
        """
        super().navigate("/artifacts")
        self.wait_for_page_load()
        logger.info("Navigated to Artifacts page")

    @action("Navigate to bucket")
    def navigate_to_bucket(self, bucket_name: str, timeout: int = 15000) -> None:
        """Navigate directly to a specific bucket via URL and wait for it to load.

        Sets ``?bucket={bucket_name}`` in the query string. This is more
        reliable than clicking the bucket in the list because it avoids the
        left-panel scroll and click-interception issues.

        Args:
            bucket_name: Exact name of the bucket (case-sensitive).
            timeout: Maximum wait time in milliseconds.
        """
        super().navigate(f"/artifacts?bucket={bucket_name}")
        self._wait_for_bucket_panel(bucket_name, timeout=timeout)
        logger.info("Navigated to bucket '%s'", bucket_name)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000) -> None:
        """Wait for the Artifacts page to finish loading.

        Waits for the left panel's ``Buckets`` heading and network idle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        self.page.get_by_test_id("artifacts-buckets-heading").wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Artifacts page loaded")

    def _wait_for_bucket_panel(self, bucket_name: str, timeout: int = 15000) -> None:
        """Wait for the right panel to show the named bucket.

        Looks for the bucket name text in the right-panel header, which
        appears once the bucket is selected and its file list loads.

        Args:
            bucket_name: Name of the selected bucket.
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        # The right-panel header shows the bucket name as plain text
        self.page.locator("main").get_by_text(bucket_name).first.wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Bucket panel loaded for '%s'", bucket_name)

    # ------------------------------------------------------------------
    # Bucket operations (left panel)
    # ------------------------------------------------------------------

    @action("Select bucket")
    def select_bucket(self, bucket_name: str, timeout: int = 10000) -> None:
        """Click a bucket by name in the left panel to open it.

        LOCATOR: Buckets are ``cursor=pointer`` generic containers in the
        left-panel list, each containing an icon and a text label.  The
        locator matches the text inside the left-panel bucket list items.

        Args:
            bucket_name: Exact name of the bucket to select.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting bucket '%s'", bucket_name)
        bucket_item = self.page.locator(
            f'main [cursor="pointer"]:has-text("{bucket_name}"), '
            f'main *[class*="bucket"]:has-text("{bucket_name}")'
        ).first
        # Fallback: text-based locator in the left panel
        if bucket_item.count() == 0:
            bucket_item = self.page.locator("main").get_by_text(bucket_name, exact=True).first
        bucket_item.wait_for(state="visible", timeout=timeout)
        bucket_item.click()
        self._wait_for_bucket_panel(bucket_name, timeout=timeout)
        logger.info("Bucket '%s' selected", bucket_name)

    def bucket_exists(self, bucket_name: str, timeout: int = 5000) -> bool:
        """Check whether a bucket with the given name is visible in the left panel.

        Args:
            bucket_name: Name to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if the bucket appears in the list, False otherwise.
        """
        try:
            self.page.locator("main").get_by_text(bucket_name, exact=True).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # File list helpers (right panel)
    # ------------------------------------------------------------------

    def _file_rows(self):
        """Return a locator for all file rows in the right-panel table.

        Uses data-testid="artifacts-file-row" and data-testid="artifacts-folder-row"
        inside the data-testid="artifacts-file-list" container.

        Returns:
            Playwright Locator for the collection of file and folder row elements.
        """
        return self.page.get_by_test_id("artifacts-file-list").locator(
            '[data-testid="artifacts-file-row"], [data-testid="artifacts-folder-row"]'
        )

    def get_file_names(self, timeout: int = 10000) -> list[str]:
        """Return the names of all files visible on the current page of the bucket.

        Reads the text of the Name cell in each file row.  Only returns
        files on the *current pagination page* — call this after navigating
        to or selecting the desired bucket.

        Args:
            timeout: How long to wait for the first file to appear.

        Returns:
            List of file name strings (may be empty if bucket is empty).
        """
        # Wait for either a file row or the empty-state label
        try:
            self._file_rows().first.wait_for(state="visible", timeout=timeout)
        except Exception:
            # Bucket may be empty — return empty list
            return []

        rows = self._file_rows()
        count = rows.count()
        names: list[str] = []
        for i in range(count):
            row = rows.nth(i)
            # Name cell is the second child generic in the row (after checkbox cell)
            # Structure: [checkbox_cell] [name_cell: img + text] [type_cell] [size_cell]
            name_cell = row.locator("> *").nth(1)
            text = (name_cell.text_content() or "").strip()
            if text:
                names.append(text)
        logger.info("File names in bucket (%d found): %s", len(names), names)
        return names

    def get_file_count(self, timeout: int = 10000) -> int:
        """Return the number of files visible on the current pagination page.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Integer count of file rows currently displayed.
        """
        try:
            self._file_rows().first.wait_for(state="visible", timeout=timeout)
            count = self._file_rows().count()
            logger.info("File count in bucket: %d", count)
            return count
        except Exception:
            logger.info("No files found in bucket (empty or not loaded)")
            return 0

    def get_total_file_count_from_pagination(self) -> int:
        """Parse the total file count from the pagination info text.

        Reads the ``"1 - 10 of N"`` label at the bottom of the file table
        and returns N (the total across all pages).

        Returns:
            Total number of files in the bucket, or 0 if not found.
        """
        try:
            pagination = self.page.locator(
                'main *:has-text("of "):not(:has(*))'
            ).last
            text = (pagination.text_content() or "").strip()
            # Format: "1 - 10 of 53"
            if " of " in text:
                total = int(text.split(" of ")[1].strip())
                logger.info("Total file count from pagination: %d", total)
                return total
        except Exception as exc:
            logger.debug("Could not parse pagination text: %s", exc)
        return 0

    def file_exists(self, filename: str, timeout: int = 5000) -> bool:
        """Check whether a file with *filename* is visible in the current file list.

        Scoped to the artifacts-file-list container via data-testid for stability.

        Args:
            filename: File name (or path suffix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if the file appears in the visible list, False otherwise.
        """
        try:
            self.page.get_by_test_id("artifacts-file-list").get_by_text(filename).first.wait_for(
                state="visible", timeout=timeout
            )
            logger.info("File '%s' found in bucket", filename)
            return True
        except Exception:
            logger.info("File '%s' NOT found in bucket", filename)
            return False

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    @action("Download file")
    def download_file(self, filename: str, timeout: int = 10000) -> Download:
        """Click the Download menu item for a named file and return the Download object.

        Locates the file row by *filename* text, hovers to reveal the three-dot
        DotMenu trigger, opens the menu, then clicks the 'Download' menu item.
        Uses ``page.expect_download`` to capture the browser download event.

        LOCATOR: There is no standalone download button per row. Download lives
        inside a DotMenu (three-dot menu). The trigger button has
        ``aria-haspopup="true"`` and is hidden until the row is hovered. The
        'Download' menu item is identified by its visible text once the menu
        is open.

        Args:
            filename: Exact file name to download.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Playwright ``Download`` object (caller can use ``download.path()``
            or ``download.save_as()`` to access the downloaded file).

        Raises:
            TimeoutError: If the file row, dot-menu trigger, or Download item
            is not found within *timeout*.
        """
        logger.info("Downloading file '%s'", filename)

        # Find the file row by data-testid, filtered by filename text
        file_row = self.page.get_by_test_id("artifacts-file-row").filter(
            has_text=filename
        ).first
        file_row.wait_for(state="visible", timeout=timeout)

        # Hover to reveal the DotMenu trigger button
        file_row.scroll_into_view_if_needed()
        file_row.hover()
        self.page.wait_for_timeout(500)  # Wait for CSS hover transition

        # Open the three-dot DotMenu
        dot_menu_btn = file_row.locator('button[aria-haspopup="true"]').first
        dot_menu_btn.wait_for(state="visible", timeout=timeout)
        dot_menu_btn.click(force=True)

        # Click the 'Download' menu item and capture the download event
        download_item = self.page.get_by_role("menuitem", name="Download")
        download_item.wait_for(state="visible", timeout=timeout)

        with self.page.expect_download(timeout=timeout) as download_info:
            download_item.click()

        download = download_info.value
        logger.info(
            "Download started for '%s' → suggested filename: %s",
            filename, download.suggested_filename,
        )
        return download

    @action("Navigate into folder")
    def navigate_into_folder(self, folder_name: str, timeout: int = 10000) -> None:
        """Click a folder item in the left-panel bucket tree to navigate into it.

        The left panel renders the bucket hierarchy as an expandable tree.
        Clicking a folder node there updates the URL prefix and re-renders
        the right-panel file list with the folder's contents.

        LOCATOR: Left-panel tree items have no ``data-testid``.  The panel
        container carries ``data-tour="artifacts-buckets-panel"`` and each
        folder node is a plain ``Box`` (div) with the folder name as text.
        We scope the search to that container to avoid hitting the right-panel
        folder row (``data-testid="artifacts-folder-row"``), which does NOT
        trigger proper navigation.

        Args:
            folder_name: Name of the folder (without trailing slash).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Navigating into folder '%s' via left-panel tree", folder_name)
        left_panel = self.page.locator('[data-tour="artifacts-buckets-panel"]')
        folder_item = left_panel.get_by_text(folder_name, exact=True).first
        folder_item.wait_for(state="visible", timeout=timeout)
        folder_item.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Navigated into folder '%s'", folder_name)

    def is_bucket_empty(self, timeout: int = 5000) -> bool:
        """Check whether the currently selected bucket contains no files.

        Args:
            timeout: How long to wait for the empty-state label.

        Returns:
            True if the bucket is empty, False if files are present.
        """
        try:
            self.empty_state_label.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Bucket permissions management
    # ------------------------------------------------------------------

    @action("Open Manage Permissions modal")
    def open_manage_permissions(self, bucket_name: str, timeout: int = 10000) -> None:
        """Open the Manage Permissions modal for a bucket via its DotMenu.

        LOCATOR: The bucket item has a DotMenu (three-dot button) that appears
        on hover. The "Manage permissions" menu item opens the modal.

        Args:
            bucket_name: Name of the bucket to manage permissions for.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening Manage Permissions for bucket '%s'", bucket_name)
        # Find the bucket item in the left panel
        left_panel = self.page.locator('[data-tour="artifacts-buckets-panel"]')
        bucket_item = left_panel.locator(f'div:has-text("{bucket_name}")').first
        bucket_item.wait_for(state="visible", timeout=timeout)

        # Hover to reveal DotMenu
        bucket_item.scroll_into_view_if_needed()
        bucket_item.hover()
        self.page.wait_for_timeout(500)

        # Click the DotMenu button
        dot_menu_btn = bucket_item.locator('button[aria-haspopup="menu"]').first
        dot_menu_btn.wait_for(state="visible", timeout=timeout)
        dot_menu_btn.click(force=True)
        self.page.wait_for_timeout(300)

        # Click "Manage permissions" menu item
        manage_perms_item = self.page.get_by_role("menuitem", name="Manage permissions")
        manage_perms_item.wait_for(state="visible", timeout=timeout)
        manage_perms_item.click()

        # Wait for modal to open
        self._wait_for_permissions_modal(timeout=timeout)
        logger.info("Manage Permissions modal opened for '%s'", bucket_name)

    def _wait_for_permissions_modal(self, timeout: int = 10000) -> None:
        """Wait for the Manage Permissions modal to be visible."""
        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')
        modal.wait_for(state="visible", timeout=timeout)

    @action("Add permission exception")
    def add_permission_exception(
        self,
        user_name_or_email: str,
        permission: str,
        timeout: int = 15000,
    ) -> None:
        """Add a user exception in the Manage Permissions modal.

        The modal must already be open (call open_manage_permissions first).

        LOCATOR: Two scenarios for "Add" button:
        - Empty exceptions list: "Add Exceptions" button (variant="special", with + icon)
        - Existing exceptions: Small + button with aria-label="Add exception"

        Args:
            user_name_or_email: User's name or email to search for.
            permission: Permission level - "Read-only" or "No access".
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Adding permission exception: user=%s, permission=%s",
                    user_name_or_email, permission)

        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')

        # Two button variants depending on whether exceptions exist:
        # 1. Empty list: "Add Exceptions" button (MuiButton-special with startIcon)
        # 2. Has exceptions: + button with aria-label="Add exception"
        add_exceptions_btn = modal.locator('button:has-text("Add Exceptions")')
        add_exception_btn = modal.locator('button[aria-label="Add exception"]')

        if add_exceptions_btn.count() > 0 and add_exceptions_btn.is_visible():
            add_exceptions_btn.click(force=True)
        elif add_exception_btn.count() > 0:
            add_exception_btn.click(force=True)
        else:
            raise Exception("Could not find Add Exceptions or Add exception button")

        self.page.wait_for_timeout(500)

        # Wait for Add exceptions dialog
        add_dialog = self.page.locator('[role="dialog"]:has-text("Add exceptions")')
        add_dialog.wait_for(state="visible", timeout=timeout)

        # Type user name in the autocomplete search (Users field)
        user_input = add_dialog.locator('input').first
        user_input.click()
        user_input.fill(user_name_or_email)
        self.page.wait_for_timeout(500)

        # Select user from dropdown
        user_option = self.page.locator(f'[role="option"]:has-text("{user_name_or_email}")').first
        user_option.wait_for(state="visible", timeout=timeout)
        user_option.click()
        self.page.wait_for_timeout(300)

        # Click on Permissions dropdown to open it
        # The dropdown shows "Permissions" label and has a combobox
        permissions_dropdown = add_dialog.locator('[role="combobox"]').first
        if permissions_dropdown.count() == 0:
            # Fallback: find by clicking on the Permissions section
            permissions_dropdown = add_dialog.locator('div:has-text("Permissions")').last
        permissions_dropdown.click()
        self.page.wait_for_timeout(300)

        # Select permission option from listbox
        perm_option = self.page.locator(f'[role="option"]:has-text("{permission}")').first
        perm_option.wait_for(state="visible", timeout=timeout)
        perm_option.click()
        self.page.wait_for_timeout(300)

        # Click Save button
        save_btn = add_dialog.get_by_role("button", name="Save")
        save_btn.click()

        # Wait for dialog to close
        add_dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("Added permission exception for '%s': %s", user_name_or_email, permission)

    @action("Edit permission exception")
    def edit_permission_exception(
        self,
        user_name_or_email: str,
        new_permission: str,
        timeout: int = 15000,
    ) -> None:
        """Edit an existing user exception in the Manage Permissions modal.

        The modal must already be open (call open_manage_permissions first).

        Args:
            user_name_or_email: User's name or email to edit.
            new_permission: New permission level - "Read/write (default)",
                "Read-only", or "No access".
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Editing permission exception: user=%s, new_permission=%s",
                    user_name_or_email, new_permission)

        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')

        # Find the user row and click edit button
        user_row = modal.locator(f'div:has-text("{user_name_or_email}")').first
        user_row.hover()
        self.page.wait_for_timeout(300)

        edit_btn = user_row.locator('button').filter(has=self.page.locator('svg')).last
        edit_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Wait for Edit dialog
        edit_dialog = self.page.locator('[role="dialog"]:has-text("Edit exception")')
        edit_dialog.wait_for(state="visible", timeout=timeout)

        # Select new permission
        permission_select = edit_dialog.locator('[role="combobox"], select').first
        if permission_select.count() == 0:
            permission_select = edit_dialog.get_by_label("Permissions")
        permission_select.click()
        self.page.wait_for_timeout(300)

        # Select permission option
        perm_option = self.page.locator(f'[role="option"]:has-text("{new_permission}")').first
        perm_option.wait_for(state="visible", timeout=timeout)
        perm_option.click()
        self.page.wait_for_timeout(300)

        # Click Save button
        save_btn = edit_dialog.get_by_role("button", name="Save")
        save_btn.click()

        # Wait for dialog to close
        edit_dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("Edited permission for '%s' to: %s", user_name_or_email, new_permission)

    @action("Remove permission exception")
    def remove_permission_exception(
        self,
        user_name_or_email: str,
        timeout: int = 15000,
    ) -> None:
        """Remove a user exception from the Manage Permissions modal.

        The modal must already be open (call open_manage_permissions first).
        Removing an exception restores the user to default permissions (Read & Write).

        Args:
            user_name_or_email: User's name or email to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing permission exception for user=%s", user_name_or_email)

        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')

        # Find the user row by checkbox (select user first)
        # The table has rows with: Checkbox, Name, Email, Permission, Actions
        user_row = modal.locator(f'tr:has-text("{user_name_or_email}")').first
        if user_row.count() == 0:
            # Try finding in a different structure (div-based table)
            user_row = modal.locator(f'div:has-text("{user_name_or_email}")').first

        user_row.wait_for(state="visible", timeout=timeout)

        # Select the user by clicking their checkbox
        checkbox = user_row.locator('input[type="checkbox"]').first
        if checkbox.count() == 0:
            checkbox = user_row.locator('[role="checkbox"]').first
        checkbox.click()
        self.page.wait_for_timeout(300)

        # Click Delete button in the toolbar (appears after selecting)
        delete_btn = modal.locator('button[aria-label="Delete"], button:has-text("Delete")').first
        delete_btn.wait_for(state="visible", timeout=timeout)
        delete_btn.click()
        self.page.wait_for_timeout(500)

        # Confirm deletion if there's a confirmation dialog
        confirm_dialog = self.page.locator('[role="dialog"]:has-text("Delete")')
        if confirm_dialog.count() > 0 and confirm_dialog.is_visible():
            confirm_btn = confirm_dialog.get_by_role("button", name="Delete")
            confirm_btn.click()
            confirm_dialog.wait_for(state="hidden", timeout=timeout)

        self.page.wait_for_timeout(500)
        logger.info("Removed permission exception for '%s'", user_name_or_email)

    @action("Close Manage Permissions modal")
    def close_manage_permissions_modal(self, timeout: int = 5000) -> None:
        """Close the Manage Permissions modal by clicking the X button."""
        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')
        close_btn = modal.locator('button[aria-label="close"], button:has-text("×")').first
        if close_btn.count() == 0:
            # Try clicking outside the modal or pressing Escape
            self.page.keyboard.press("Escape")
        else:
            close_btn.click()
        modal.wait_for(state="hidden", timeout=timeout)
        logger.info("Manage Permissions modal closed")
