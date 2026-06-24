"""Artifacts Page Object for Elitea artifact storage.

Handles: /app/artifacts and /app/artifacts?bucket={bucket_name}

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
    Selecting a bucket updates the URL to ``/app/artifacts?bucket={name}``
    and renders the file table on the right.

    URL: /app/artifacts, /app/artifacts?bucket={bucket_name}
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

        Navigates to ``/app/artifacts`` and waits for the bucket list to render.
        """
        super().navigate("/app/artifacts")
        self.wait_for_page_load()
        logger.info("Navigated to Artifacts page")

    @action("Navigate to bucket")
    def navigate_to_bucket(self, bucket_name: str, timeout: int = 15000) -> None:
        """Navigate directly to a specific bucket via URL and wait for it to load.

        Sets ``?bucket={bucket_name}`` in the query string.  This is more
        reliable than clicking the bucket in the list because it avoids the
        left-panel scroll and click-interception issues.

        Args:
            bucket_name: Exact name of the bucket (case-sensitive).
            timeout: Maximum wait time in milliseconds.
        """
        super().navigate(f"/app/artifacts?bucket={bucket_name}")
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
        self.page.get_by_text("Buckets").first.wait_for(
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

        LOCATOR: Each file row is a ``generic`` child of the file list
        container inside the right panel.  Rows contain a checkbox cell,
        a name cell (with icon + filename text), a type cell, a size cell,
        and an (initially empty) actions cell.

        The selector targets the scrollable list container's direct children,
        excluding the header row and pagination footer.

        Returns:
            Playwright Locator for the collection of file row elements.
        """
        # The right-panel file list has a header row and then data rows.
        # Both are rendered as ``generic`` divs.  We scope to the data
        # container which sits below the column-header row.
        # Strategy: find the container that holds "Name", "Type", "Size", "Actions"
        # headers, then grab its next sibling which is the data rows container.
        right_panel = self.page.locator("main").last
        # The file rows container is the second generic inside the file table
        # (first generic = header row, second = data rows wrapper)
        return right_panel.locator(
            'div:has(> div:has(input[type="checkbox"])) > div'
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

        Uses partial text matching so ``"file1.txt"`` matches a cell showing
        ``"file1.txt"`` exactly or as part of a path like ``"output/file1.txt"``.

        Args:
            filename: File name (or path suffix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if the file appears in the visible list, False otherwise.
        """
        try:
            self.page.locator("main").get_by_text(filename).first.wait_for(
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
        """Click the download action for a named file and return the Download object.

        Locates the file row by *filename* text, hovers to reveal the action
        buttons, then clicks the download icon.  Uses ``page.expect_download``
        to capture the browser download event.

        LOCATOR: The download button in each row has ``aria-label="download"``
        or is the first icon-button in the row's Actions cell (last cell).
        It is hidden by default and only visible on row hover.

        Args:
            filename: Exact file name to download.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Playwright ``Download`` object (caller can use ``download.path()``
            or ``download.save_as()`` to access the downloaded file).

        Raises:
            TimeoutError: If the file row or download button is not found.
        """
        logger.info("Downloading file '%s'", filename)

        # Find the file row containing this filename
        file_row = self.page.locator("main").locator(
            f'div:has(> *:has-text("{filename}"))'
        ).first
        file_row.wait_for(state="visible", timeout=timeout)

        # Scroll into view and hover to reveal the action buttons
        file_row.scroll_into_view_if_needed()
        file_row.hover()
        self.page.wait_for_timeout(500)  # Wait for CSS transition

        # The download button is in the Actions cell of the row.
        # Try aria-label first, then fall back to the first button in the row
        # that appears after hover (the action buttons are hidden by default).
        download_btn = file_row.locator('button[aria-label="download"], button[aria-label="Download"]')
        if download_btn.count() == 0:
            # Fallback: any button that became visible in this row after hover
            download_btn = file_row.locator("button").last

        download_btn.wait_for(state="visible", timeout=timeout)

        with self.page.expect_download(timeout=timeout) as download_info:
            download_btn.click(force=True)

        download = download_info.value
        logger.info(
            "Download started for '%s' → suggested filename: %s",
            filename, download.suggested_filename,
        )
        return download

    @action("Navigate into folder")
    def navigate_into_folder(self, folder_name: str, timeout: int = 10000) -> None:
        """Click a folder row in the file list to navigate into it.

        When an agent creates files under a sub-path (e.g. ``output/``), the
        bucket file list shows the prefix as a folder row.  Clicking it updates
        the right panel to show the files inside that folder.

        LOCATOR: Folder rows look like file rows but their Name cell ends with
        a ``/`` character or the row has a folder icon.  We match by the exact
        folder name text in the right panel and click it.

        Args:
            folder_name: Name of the folder (without trailing slash).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Navigating into folder '%s'", folder_name)
        folder_row = self.page.locator("main").get_by_text(folder_name, exact=False).first
        folder_row.wait_for(state="visible", timeout=timeout)
        folder_row.click()
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
