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
import urllib.parse
from playwright.sync_api import Page, Download, expect

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

    bucket_search_input = LocatorDescriptor(
        testid="artifacts-bucket-search-input",
        description="Bucket search input, revealed after clicking the search "
        "icon in the left panel header (ELITEA-1809) — native MUI InputBase "
        "on BucketsPanel.jsx, filters client-side with a 300ms debounce",
    )

    bucket_search_clear_button = LocatorDescriptor(
        testid="artifacts-bucket-search-clear-button",
        description="Clear/close (X) button next to the bucket search input "
        "(ELITEA-1809) — clears the query AND closes the search box in one "
        "action (BucketsPanel.jsx's handleSearchClear)",
    )

    # ------------------------------------------------------------------
    # "New Bucket" form — /artifacts/create-bucket (ELITEA-1808)
    # ------------------------------------------------------------------

    bucket_name_input = LocatorDescriptor(
        testid="artifacts-bucket-name-input",
        description="Name field on the 'New Bucket' form — pre-filled with the "
        "literal 'new-bucket' on a fresh (non-edit) load (CreateBucket.jsx)",
    )

    bucket_retention_measure_combobox = LocatorDescriptor(
        testid="artifacts-bucket-retention-measure-select-combobox",
        description="Retention-measure select's clickable combobox on the 'New "
        "Bucket' form — the shared SingleSelect component auto-derives this "
        "'-combobox' suffix from the root 'artifacts-bucket-retention-measure-select' "
        "testid (SingleSelect.jsx); defaults to 'Years'",
    )

    bucket_retention_value_input = LocatorDescriptor(
        testid="artifacts-bucket-retention-value-input",
        description="Retention-value numeric input on the 'New Bucket' form — "
        "defaults to '1'",
    )

    bucket_save_button = LocatorDescriptor(
        testid="artifacts-bucket-save-button",
        description="Save button on the 'New Bucket' form — submits bucket creation",
    )

    # ------------------------------------------------------------------
    # Bucket-row 3-dot menu (left panel, ELITEA-1808)
    # ------------------------------------------------------------------

    # Dynamic testid template — the bucket row container itself, used as the
    # hover target that reveals the dot-menu trigger below (BucketItem.jsx's
    # menuContainer is `display:none` until the row is hovered; the trigger
    # itself has no bounding box to hover directly until then).
    BUCKET_ROW = '[data-testid="artifacts-bucket-row-{}"]'

    # Prefix (any-bucket) variant of BUCKET_ROW — matches EVERY currently
    # rendered bucket row regardless of name. Same `[data-testid^="…"]`
    # pattern already established elsewhere in this codebase (e.g.
    # agent_detail_page.py's SKILL_CARD_ANY_SELECTOR,
    # chat_page.py's MENTION_SKILL_ITEM_PREFIX). Used by
    # :meth:`get_visible_bucket_count` (ELITEA-1809) to prove the
    # bucket-search filter narrows the rendered list — the count-based
    # equivalent of a total-buckets footer read, without needing a testid on
    # BucketFooter.jsx (which no case step touches directly).
    BUCKET_ROW_ANY_SELECTOR = '[data-testid^="artifacts-bucket-row-"]'

    # Dynamic testid template — dot-menu trigger for a given bucket row.
    # Fixed live for ELITEA-1808 (was previously a single STATIC, non-unique
    # testid shared by every bucket in the project — see the AFS's Concrete
    # Handles table); now templated with the bucket's own name.
    BUCKET_MENU_BUTTON = '[data-testid="bucket-menu-{}-menu-button"]'

    # Dynamic testid template — the bucket-row dot-menu's WHOLE dropdown
    # container (ELITEA-1817). Same templated-`id` provenance as
    # BUCKET_MENU_BUTTON above (DotMenu.jsx's
    # `<Menu data-testid={id ? `${id}-menu` : undefined}>`). Used to read
    # the full 4-item dropdown text in one shot — "Rename"/"Pin to top"
    # have no per-item testid (out of scope, see :attr:`bucket_menu_delete_menuitem`
    # below), so the whole-container text read is this page object's
    # established alternative (same pattern as :meth:`get_file_row_text`).
    BUCKET_MENU_CONTAINER = '[data-testid="bucket-menu-{}-menu"]'

    bucket_menu_upload_files_menuitem = LocatorDescriptor(
        testid="bucket-menu-upload-files-menuitem",
        description="'Upload files' item inside a bucket row's dot-menu dropdown "
        "(ELITEA-1808) — testid is static (not bucket-parameterized): the menu "
        "item's key ('bucket-menu-upload-files') is fixed regardless of which "
        "bucket's menu is currently open",
    )

    bucket_menu_delete_menuitem = LocatorDescriptor(
        testid="bucket-menu-delete-menuitem",
        description="'Delete' item inside a bucket row's dot-menu dropdown "
        "(ELITEA-1817) — testid added live to BucketItem.jsx's menuItems array "
        "(a `key: 'bucket-menu-delete'` field, same mechanism as the sibling "
        "'bucket-menu-upload-files' key) and pushed to automation/testids "
        "(EliteaAI/EliteaUI@457f5f44). Static (not bucket-parameterized), same "
        "shape as :attr:`bucket_menu_upload_files_menuitem`. Clicking it opens "
        "the shared DeleteEntityModal (:attr:`delete_confirm_dialog`) — the "
        "SAME component ELITEA-1847 already testid'd for the file/folder "
        "bulk-delete flow, reused here from the bucket dot-menu entry point.",
    )

    # Dynamic testid template — left-panel tree node for a file/folder, keyed
    # by its full relative path (e.g. 'test.txt', or 'a1/sample.txt' when
    # nested in a subfolder). FileTreeItem.jsx.
    ARTIFACTS_TREE_ITEM = '[data-testid="artifacts-tree-item-{}"]'

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
    # Main-panel breadcrumb header (ELITEA-1824)
    # ------------------------------------------------------------------

    breadcrumb_bucket_label = LocatorDescriptor(
        testid="artifacts-breadcrumb-bucket-label",
        description="Bucket-name label in the main-panel toolbar header "
        "(ArtifactTableToolbar.jsx) — always present once a bucket is "
        "selected, regardless of folder depth",
    )

    breadcrumb_folder_label = LocatorDescriptor(
        testid="artifacts-breadcrumb-folder-label",
        description="Per-crumb folder-name label rendered by "
        "BreadcrumbNavigation.jsx — CONDITIONALLY present: absent at bucket "
        "root, one element per folder level once navigated into a "
        "subfolder (same conditional-rendering shape as ARTIFACTS_TREE_ITEM, "
        "not a state-toggled testid). Static (non-parameterized) testid — "
        "use .first/.count()/text_content() to read a specific crumb, same "
        "shape as artifacts-file-row/artifacts-folder-row.",
    )

    # ------------------------------------------------------------------
    # Right panel — file table
    # ------------------------------------------------------------------

    empty_state_label = LocatorDescriptor(
        testid="artifacts-empty-state",
        fallback=lambda page: page.locator('main').get_by_text("No files in this bucket").last,
        description="Empty-state label shown when the selected bucket has no files",
    )

    upload_files_empty_state_button = LocatorDescriptor(
        testid="artifacts-upload-files-empty-state-button",
        description="CENTER 'Upload files' button shown inside the empty-state "
        "panel (ArtifactTableNoFiles.jsx) — a DIFFERENT element from the "
        "toolbar's upload_files_button (different class/position, confirmed "
        "live via DOM inspection during AFS exploration, ELITEA-1824)",
    )

    # ------------------------------------------------------------------
    # "Upload files to ..." dialog (ELITEA-1832)
    # ------------------------------------------------------------------

    upload_path_dialog = LocatorDescriptor(
        testid="artifacts-upload-path-dialog",
        description="'Upload files to ...' dialog root — opens after selecting files "
        "in the native file picker; Path field pre-filled with the bucket name",
    )

    upload_path_input = LocatorDescriptor(
        testid="artifacts-upload-path-input",
        description="Path field inside the 'Upload files to ...' dialog — shows the "
        "bucket/prefix as a read-only startAdornment before the editable textbox",
    )

    # ELITEA-1824 implementer note: `upload_path_input` above resolves to the
    # MuiFormControl-root WRAPPER (label + read-only startAdornment), NOT the
    # editable native <input> — its text_content() never reflects what the
    # user has typed (confirmed live: native inputs don't expose value via
    # textContent). Use `upload_path_input_field` below to read/assert the
    # typed value.
    upload_path_input_field = LocatorDescriptor(
        testid="artifacts-upload-path-input-field",
        description="The actual editable native <input> inside the Path field "
        "(ELITEA-1824) — added via slotProps.htmlInput since the TextField-level "
        "testid above lands on the wrapper, not this element (UploadPathDialog.jsx). "
        "Use .input_value() here for the user-typed subfolder suffix; the "
        "read-only bucket/currentPrefix prefix itself is only ever readable via "
        ":attr:`upload_path_input`'s text_content() (:meth:`get_upload_path_prefix_text`).",
    )

    upload_path_upload_button = LocatorDescriptor(
        testid="artifacts-upload-path-upload-button",
        description="'Upload' button inside the 'Upload files to ...' dialog — triggers "
        "client-side duplicate detection against the bucket's already-fetched listing",
    )

    # ------------------------------------------------------------------
    # "Resolve duplicates" dialog (ELITEA-1832)
    # ------------------------------------------------------------------

    resolve_duplicates_dialog = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-dialog",
        description="'Resolve duplicates' dialog root — shown when uploaded files "
        "collide with existing bucket contents",
    )

    resolve_duplicates_filename = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-filename",
        description="Duplicate filename row inside the 'Resolve duplicates' dialog — "
        "one per colliding file (matches multiple elements when several duplicates)",
    )

    resolve_duplicates_cancel_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-cancel-button",
        description="'Cancel' button inside the 'Resolve duplicates' dialog — aborts "
        "the ENTIRE upload operation, including any non-duplicate files in the batch",
    )

    # ------------------------------------------------------------------
    # Success toast (app-wide generic component, reused across features —
    # see skills_list_page.SkillsListPage.import_success_toast_message)
    # ------------------------------------------------------------------

    success_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Generic app-wide success toast. ELITEA-1832 confirmed its "
        "ABSENCE on the client-side-only duplicate-upload path; ELITEA-1826 "
        "independently confirmed its PRESENCE with the exact text 'Your file(s) "
        "have been successfully uploaded!' on the successful (no-duplicates) "
        "multi-file upload path — both live-verified, not mutually exclusive.",
    )

    # ------------------------------------------------------------------
    # File row actions dot-menu (ELITEA-1839)
    # ------------------------------------------------------------------

    # Dynamic testid template — dot-menu trigger for a given file row.
    # The parameter is the file's BASE name only (row.id = item.name in
    # ArtifactTable.jsx), even for files nested in a subfolder.
    ARTIFACT_ACTIONS_MENU_BUTTON = '[data-testid="artifact-actions-{}-menu-button"]'

    download_menu_item = LocatorDescriptor(
        testid="artifacts-file-download-menuitem",
        description="'Download' item inside a file row's dot-menu dropdown",
    )

    delete_menu_item = LocatorDescriptor(
        testid="artifacts-file-delete-menuitem",
        description="'Delete' item inside a file row's dot-menu dropdown — "
        "visibility-only in ELITEA-1839, never clicked",
    )

    zip_download_progress_dialog = LocatorDescriptor(
        testid="artifacts-zip-download-progress-dialog",
        description="'Preparing ...zip' progress dialog — architecturally "
        "unreachable from the single-file dropdown download path "
        "(ArtifactTable.jsx onDownload never calls startZipDownload); used "
        "to assert its ABSENCE as a defensive/regression guard (ELITEA-1839)",
    )

    # ------------------------------------------------------------------
    # Per-row checkbox + ZIP-download progress dialog internals (ELITEA-1840)
    # ------------------------------------------------------------------

    # Dynamic testid template — checkbox for a given file/folder row. The
    # parameter is the row's BASE name (row.id = item.name in
    # ArtifactTable.jsx) — same identity semantics as
    # ARTIFACT_ACTIONS_MENU_BUTTON above. Threaded via GridTableRow's new
    # caller-supplied `checkboxTestId` prop (shared component — only wired
    # at ArtifactTable.jsx's call site, per the AFS's shared-component
    # testid ruling).
    ARTIFACT_FILE_CHECKBOX = '[data-testid="artifacts-file-checkbox-{}"]'

    zip_download_progress_title = LocatorDescriptor(
        testid="artifacts-zip-download-progress-title",
        description="'Preparing {bucket}.zip' title inside the ZIP-download "
        "progress dialog (ELITEA-1840)",
    )

    zip_download_progress_bar = LocatorDescriptor(
        testid="artifacts-zip-download-progress-bar",
        description="Determinate MUI LinearProgress bar inside the ZIP-download "
        "progress dialog (ELITEA-1840) — assert via its 'aria-valuenow' "
        "attribute, not visual width",
    )

    zip_download_progress_counter = LocatorDescriptor(
        testid="artifacts-zip-download-progress-counter",
        description="'{current} of {total} files' counter inside the "
        "ZIP-download progress dialog (ELITEA-1840)",
    )

    zip_download_progress_current_file = LocatorDescriptor(
        testid="artifacts-zip-download-progress-current-file",
        description="'Current: {full-relative-key}' label inside the "
        "ZIP-download progress dialog (ELITEA-1840) — conditionally rendered, "
        "absent from the DOM until the first file is in flight "
        "(progress.filename truthy)",
    )

    zip_download_progress_cancel_button = LocatorDescriptor(
        testid="artifacts-zip-download-progress-cancel-button",
        description="'Cancel' button inside the ZIP-download progress dialog "
        "(ELITEA-1840) — visibility-only in this case, never clicked "
        "(Cancel-flow testing is out of scope)",
    )

    # ------------------------------------------------------------------
    # Bulk delete flow (ELITEA-1847)
    # ------------------------------------------------------------------

    delete_files_button = LocatorDescriptor(
        testid="artifacts-delete-files-button",
        description="Toolbar 'Delete selected/all files' icon button wrapper "
        "(ELITEA-1847 — new testid, threaded via DeleteEntityButton.jsx's "
        "caller-supplied `testId` prop, wired only at ArtifactTableToolbar.jsx's "
        "call site). MUI clones the Tooltip's dynamic title ('Delete selected "
        "files' / 'Delete all files', depending on whether every row is "
        "currently selected) onto this wrapping <Box component=\"span\"> as a "
        "static aria-label; the inner IconButton itself carries a FIXED, "
        "non-dynamic aria-label='delete entity' and has no testid of its own. "
        "Confirmed live (ELITEA-1847): the wrapper's bounding box is "
        "pixel-identical to the inner button's, so clicking this locator "
        "directly fires the button's own onClick — no `.locator(\"button\")` "
        "chaining needed for either the tooltip-text read or the click.",
    )

    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Delete-confirmation modal root (DeleteEntityModal.jsx, "
        "shared component, already testid'd) — reused here (ELITEA-1847) to "
        "confirm deletion of selected artifacts files/folders.",
    )

    delete_confirm_message = LocatorDescriptor(
        testid="delete-confirm-message",
        description="Delete-confirmation modal's message text (ELITEA-1847 — "
        "new testid added directly to DeleteEntityModal.jsx's existing "
        "id='alert-dialog-description' Typography, which is kept for a11y). "
        "Implementer correction to the AFS's own suggestion (reading the "
        "message via the bare '#alert-dialog-description' id, chained off the "
        "testid'd dialog root): this project's locator policy requires scoped "
        "sub-selectors to themselves be data-testid-based (established "
        "ELITEA-1840 precedent, same reasoning that produced the ZIP dialog's "
        "own -title/-counter/-current-file testids rather than raw tag "
        "selectors) — so a testid was added instead of chaining a raw id "
        "selector off :attr:`delete_confirm_dialog`.",
    )

    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="'Delete' (confirm) button inside the delete-confirmation "
        "modal (DeleteEntityModal.jsx) — do not confuse with "
        ":attr:`delete_files_button`, the toolbar icon that OPENS this modal.",
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
    def navigate_to_bucket(
        self, bucket_name: str, timeout: int = 15000, _retry: bool = True
    ) -> None:
        """Navigate directly to a specific bucket via URL and wait for it to load.

        Sets ``?bucket={bucket_name}`` in the query string. This is more
        reliable than clicking the bucket in the list because it avoids the
        left-panel scroll and click-interception issues.

        **Known product race (issue #638), same guard as
        :meth:`navigate_to_bucket_folder`:** on a FRESH page load, EliteaUI's
        ``Artifacts.jsx`` can still be resolving the selected project id from
        Redux when this navigation lands, silently stripping the ``bucket``
        URL param and falling back to the most-recently-used bucket with NO
        error shown. ``_wait_for_bucket_panel`` doesn't catch this: it
        loose-matches *any* text in ``main``, including the target bucket's
        own name still sitting in the left-panel list even while a DIFFERENT
        bucket is the one actually selected (confirmed live via PR #661's
        independent re-run — the failure screenshot showed bucket "aa" open
        instead of the seeded target). ELITEA-1847's original diagnosis
        attributed the resulting empty-file-table symptom to a separate
        "S3-listing-fetch lag" race and added :meth:`wait_for_file_count` to
        poll for it — but with the WRONG bucket loaded, that locator is
        stably (not transiently) empty and can never converge no matter the
        timeout. This method re-checks the LIVE URL's ``bucket`` query param
        after settling and retries the navigation once if it was stripped —
        by the second attempt the project id is already resolved from the
        first, so the race window is gone. :meth:`wait_for_file_count`
        remains a legitimate condition-based wait for the file table to
        settle (harmless if no fetch lag exists), it just isn't a substitute
        for loading the correct bucket in the first place.

        Args:
            bucket_name: Exact name of the bucket (case-sensitive).
            timeout: Maximum wait time in milliseconds.

        Raises:
            AssertionError: If the ``bucket`` URL param is still wrong after
                one retry (i.e. the race fired twice in a row).
        """
        super().navigate(f"/artifacts?bucket={bucket_name}")
        self._wait_for_bucket_panel(bucket_name, timeout=timeout)

        live_bucket_param = urllib.parse.parse_qs(
            urllib.parse.urlparse(self.page.url).query
        ).get("bucket", [None])[0]
        if live_bucket_param != bucket_name:
            if not _retry:
                raise AssertionError(
                    f"Navigation to bucket '{bucket_name}' did not stick "
                    f"after a retry — URL's bucket param is "
                    f"{live_bucket_param!r} instead (known product race, "
                    f"issue #638)"
                )
            logger.warning(
                "Bucket param lost after navigating to '%s' (URL now has %r) "
                "— retrying once (known product race, issue #638)",
                bucket_name, live_bucket_param,
            )
            self.navigate_to_bucket(bucket_name, timeout=timeout, _retry=False)
            return

        logger.info("Navigated to bucket '%s'", bucket_name)

    @action("Navigate to bucket subfolder")
    def navigate_to_bucket_folder(
        self, bucket_name: str, folder: str, timeout: int = 15000, _retry: bool = True
    ) -> None:
        """Navigate directly into a bucket's subfolder via URL, in one step.

        New sibling method (ELITEA-1839) — :meth:`navigate_to_bucket` has 3
        merged callers, so it stays byte-identical rather than growing an
        optional ``folder`` kwarg (additive-only on shared-caller files).

        Sets ``?bucket={bucket_name}&folder={folder}`` in the query string.
        Confirmed live: the ``folder`` param composes with ``bucket`` in a
        single navigation, reaching the same subfolder state as a bucket
        click + a left-panel-tree folder click (:meth:`navigate_into_folder`)
        without either UI interaction — faster and avoids left-panel
        scroll/click-interception issues for callers that already know the
        target subfolder path.

        **Known product race, confirmed live 2/5 local runs (ELITEA-1839
        exploration; filed as
        https://github.com/EliteaAI/elitea-testing-public/issues/638):** on a
        FRESH page load, EliteaUI's
        ``Artifacts.jsx`` can still be resolving the selected project id from
        Redux when this navigation lands. If that resolution completes a
        render *after* mount, a ``selectedProjectId !== queryParams.projectId``
        effect fires and calls ``setSearchParams({})`` — silently stripping
        the ``bucket``/``folder`` params from the URL — before the
        auto-select-bucket effect ever reads them. The app then falls back to
        the most-recently-used bucket with NO error shown (not even the
        'Bucket not found' dialog the app has for the normal not-found case,
        since by then the URL param is simply gone). ``_wait_for_bucket_panel``
        doesn't catch this: it loose-matches *any* text in ``main``, including
        the target bucket's own (untruncated) name still sitting in the
        left-panel list even while a DIFFERENT bucket is the one actually
        selected. This method re-checks the LIVE URL's ``bucket`` query param
        after settling and retries the navigation once if it was stripped —
        by the second attempt the project id is already resolved from the
        first, so the race window is gone.

        Args:
            bucket_name: Exact name of the bucket (case-sensitive).
            folder: Subfolder path to deep-link directly into (e.g. ``"a1"``).
            timeout: Maximum wait time in milliseconds.

        Raises:
            AssertionError: If the ``bucket`` URL param is still wrong after
                one retry (i.e. the race fired twice in a row).
        """
        super().navigate(f"/artifacts?bucket={bucket_name}&folder={folder}")
        self._wait_for_bucket_panel(bucket_name, timeout=timeout)

        live_bucket_param = urllib.parse.parse_qs(
            urllib.parse.urlparse(self.page.url).query
        ).get("bucket", [None])[0]
        if live_bucket_param != bucket_name:
            if not _retry:
                raise AssertionError(
                    f"Navigation to bucket '{bucket_name}' folder '{folder}' "
                    f"did not stick after a retry — URL's bucket param is "
                    f"{live_bucket_param!r} instead (known product race, "
                    f"issue #638)"
                )
            logger.warning(
                "Bucket param lost after navigating to '%s' (URL now has %r) "
                "— retrying once (known product race, issue #638)",
                bucket_name, live_bucket_param,
            )
            self.navigate_to_bucket_folder(
                bucket_name, folder, timeout=timeout, _retry=False
            )
            return

        logger.info("Navigated to bucket '%s', folder '%s'", bucket_name, folder)

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
    # Bucket search (left panel, ELITEA-1809)
    # ------------------------------------------------------------------

    # BucketsPanel.jsx's useDebounceValue(searchQuery, 300) is a hardcoded
    # product constant, not network latency — one of the few places in this
    # codebase where a short fixed wait is defensible (AFS § Automation
    # Hints); padded above the 300ms interval itself, same margin the
    # project already uses for MUI debounce waits elsewhere
    # (agent_form_page.py).
    BUCKET_SEARCH_DEBOUNCE_WAIT_MS = 500

    @action("Open bucket search")
    def open_bucket_search(self, timeout: int = 10000) -> None:
        """Click the search icon and wait for the search input to appear.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.search_buckets_button.click()
        self.bucket_search_input.wait_for(state="visible", timeout=timeout)
        logger.info("Bucket search opened")

    @action("Search buckets")
    def search_buckets(self, query: str) -> None:
        """Type *query* into the open bucket search input and wait for the
        client-side filter's debounce window to elapse.

        Call :meth:`open_bucket_search` first — this method does not open
        the search box itself.

        Args:
            query: Search text (e.g. ``"buck"``).
        """
        self.bucket_search_input.click()
        self.bucket_search_input.type(query)
        self.page.wait_for_timeout(self.BUCKET_SEARCH_DEBOUNCE_WAIT_MS)
        logger.info("Typed '%s' into bucket search", query)

    @action("Close bucket search")
    def close_bucket_search(self, timeout: int = 10000) -> None:
        """Click the clear/X button to clear the query and close the search box.

        Confirmed live (ELITEA-1809 AFS): a single click both clears
        ``searchQuery`` and sets ``isSearchActive`` to ``False``
        (``BucketsPanel.jsx``'s ``handleSearchClear``), so the search input
        itself unmounts immediately — wait for it to become hidden as the
        first completion condition.

        **Implementer finding (ELITEA-1809):** unmounting the input is NOT
        sufficient on its own — ``filteredBuckets`` derives from
        ``debouncedSearchQuery`` (``useDebounceValue(searchQuery, 300)``),
        which lags the ``searchQuery`` state by the SAME 300ms debounce even
        when clearing it to ``''``. Confirmed live: reading the bucket list
        immediately after the input disappears can still catch the stale
        filtered set. Also waits out :attr:`BUCKET_SEARCH_DEBOUNCE_WAIT_MS`
        so the full (unfiltered) list has actually re-rendered before
        returning.

        Args:
            timeout: Maximum wait time in milliseconds for the search input
                to disappear.
        """
        self.bucket_search_clear_button.click()
        self.bucket_search_input.wait_for(state="hidden", timeout=timeout)
        self.page.wait_for_timeout(self.BUCKET_SEARCH_DEBOUNCE_WAIT_MS)
        logger.info("Bucket search closed")

    def count_bucket_rows(self, bucket_name: str) -> int:
        """Return the number of DOM rows matching *bucket_name*'s dynamic testid.

        Primary duplicate-detection mechanism (ELITEA-1809): a real
        duplicate bucket, if one had been created, would render a SECOND
        DOM element sharing the identical dynamic
        ``artifacts-bucket-row-{name}`` testid — a stronger, DOM-level proof
        than eyeballing a search-filtered list.

        Args:
            bucket_name: Exact bucket name.

        Returns:
            Number of matching DOM elements (0, 1, or more).
        """
        return self.page.locator(self.BUCKET_ROW.format(bucket_name)).count()

    def get_visible_bucket_count(self) -> int:
        """Return the number of bucket rows currently rendered (any bucket).

        Uses the shared testid PREFIX (:attr:`BUCKET_ROW_ANY_SELECTOR`), not
        one bucket's exact testid — proves the bucket-search filter actually
        narrows the rendered DOM list (ELITEA-1809 case steps 5/7), and
        gives a filter-scoped, environment-count-independent way to confirm
        no new bucket appeared across two search passes (case steps 17/18),
        without needing a testid on the untested ``BucketFooter.jsx`` total
        count (which no case step reads directly).

        Returns:
            Count of currently-visible bucket row elements.
        """
        return self.page.locator(self.BUCKET_ROW_ANY_SELECTOR).count()

    # ------------------------------------------------------------------
    # 'New Bucket' form flow (ELITEA-1808)
    # ------------------------------------------------------------------

    @action("Click '+ Artifact Bucket' button")
    def click_create_bucket_button(self, timeout: int = 15000) -> None:
        """Click '+ Artifact Bucket' and wait for the 'New Bucket' form to render.

        Confirmed live (ELITEA-1808 AFS): this is a full PAGE navigation to
        ``/artifacts/create-bucket``, not a modal — the caller can assert
        ``self.page.url`` for that after this returns.

        Args:
            timeout: Maximum wait time in milliseconds for the Name field
                to become visible.
        """
        self.create_bucket_button.click()
        self.bucket_name_input.wait_for(state="visible", timeout=timeout)
        logger.info("'New Bucket' form opened")

    @action("Fill bucket name field")
    def fill_bucket_name(self, name: str) -> None:
        """Replace the Name field's pre-filled default with *name*.

        The field is pre-filled with the literal ``"new-bucket"`` on a
        fresh (non-edit) form load (``CreateBucket.jsx``). MUI/React field —
        a bare ``fill()`` would not trigger ``formik.handleChange``
        (``.claude/rules/mui-patterns.md``). ``press("Control+a")`` was
        tried first (per the AFS's original hint) but confirmed live NOT to
        select-all on this field — it moves the caret to position 0 without
        selecting, so subsequent typing PREPENDS instead of replacing
        (leaving a mangled ``"{name}ew-bucket"`` value). Uses
        ``select_text()`` + ``type()`` instead, which sets the DOM
        selection directly — the same established workaround already used
        for this exact MUI quirk in ``credential_form_fields.py``'s
        ``set_display_name()``.

        Args:
            name: Bucket name to type. Must satisfy the form's validation
                (start with a letter; letters, numbers, hyphens only; max 56
                characters).
        """
        self.bucket_name_input.click()
        self.bucket_name_input.select_text()
        self.bucket_name_input.type(name)
        logger.info("Filled bucket name field with '%s'", name)

    def is_bucket_name_invalid(self, timeout: int = 5000) -> bool:
        """Return whether the Name field is currently flagged invalid (ELITEA-1817).

        Reads the ``aria-invalid`` attribute of the already testid-anchored
        :attr:`bucket_name_input` — confirmed live: MUI/formik renders NO
        helper-text DOM element at all when ``formik.errors.name`` is
        falsy, so there is nothing to assert "invisible", only the input's
        own validity state. Same "read an attribute of an existing
        testid-anchored locator" shape already established by
        :meth:`is_bucket_selected`/:meth:`is_tree_item_selected` — no new
        testid needed.

        Args:
            timeout: Maximum wait time in milliseconds for the field itself
                to be visible before reading its attribute.

        Returns:
            True if ``aria-invalid="true"``, False otherwise (including
            ``"false"`` or the attribute being absent).
        """
        self.bucket_name_input.wait_for(state="visible", timeout=timeout)
        return self.bucket_name_input.get_attribute("aria-invalid") == "true"

    @action("Click bucket Save button")
    def click_bucket_save_button(self, timeout: int = 15000):
        """Click Save on the 'New Bucket' form and return the creation response.

        Wraps the click in ``page.expect_response`` (the same idiom already
        used elsewhere in this page object, e.g.
        :meth:`CredentialDetailPage`-style pin toggling) rather than relying
        on :meth:`capture_requests_matching`'s async listener alone —
        confirmed live the listener-populated ``status`` can still read
        ``None`` immediately after the click resolves (a request/response
        pairing race, not a product issue); ``expect_response`` blocks until
        the matching response actually lands.

        Args:
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            Playwright ``Response`` object for the bucket-creation POST.
        """
        with self.page.expect_response(
            lambda r: "artifacts/buckets" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as response_info:
            self.bucket_save_button.click()
        return response_info.value

    def wait_for_bucket_in_list(self, bucket_name: str, timeout: int = 15000) -> None:
        """Wait for a bucket to appear in the left-panel bucket list.

        Waits on the CONDITION that the bucket's own dynamic
        ``artifacts-bucket-row-{name}`` testid becomes visible — **not** a
        fixed sleep, and **not** an assertion taken immediately after the
        Save click. Confirmed live (ELITEA-1808 AFS): a snapshot taken
        immediately after the Save-triggered navigation can catch the
        bucket list mid-refetch (a transient stale "no buckets" render that
        self-corrects within ~1-2s once the list refetch completes) — this
        condition wait absorbs that race entirely.

        **Implementer correction:** the AFS originally suggested waiting on
        the bucket's dot-menu button testid instead — confirmed live this
        does NOT work as a wait condition, because that button is
        hover-gated (``display:none`` until the row is hovered, see
        :meth:`open_bucket_menu`) and so never reaches Playwright's
        "visible" state on a row nobody has hovered yet. The row container
        itself (:attr:`BUCKET_ROW`) has no such gating and is the correct
        condition.

        Args:
            bucket_name: Exact name of the bucket to wait for.
            timeout: Maximum wait time in milliseconds.
        """
        self.page.locator(self.BUCKET_ROW.format(bucket_name)).wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Bucket '%s' visible in the bucket list", bucket_name)

    def wait_for_bucket_removed_from_list(
        self, bucket_name: str, timeout: int = 15000
    ) -> None:
        """Wait for a bucket to disappear from the left-panel bucket list (ELITEA-1817).

        Symmetric counterpart to :meth:`wait_for_bucket_in_list` — the same
        "list mid-refetch" race that method's docstring documents for a
        bucket's *appearance* plausibly applies to its *removal* too (both
        are driven by the same post-mutation list refetch). Uses
        Playwright's own auto-retrying ``expect(...).to_have_count(0)`` on
        the bucket's own dynamic :attr:`BUCKET_ROW` testid, the same
        auto-retrying idiom :meth:`wait_for_file_count` already established
        in this page object — never a bare, single-instant
        :meth:`count_bucket_rows` read right after a delete-confirm click.

        Args:
            bucket_name: Exact name of the bucket expected to be gone.
            timeout: Maximum wait time in milliseconds.
        """
        expect(self.page.locator(self.BUCKET_ROW.format(bucket_name))).to_have_count(
            0, timeout=timeout
        )
        logger.info("Bucket '%s' no longer in the bucket list", bucket_name)

    def is_bucket_selected(self, bucket_name: str, timeout: int = 10000) -> bool:
        """Return whether *bucket_name*'s left-panel row is the selected one.

        Reads the ``data-selected`` attribute (ELITEA-1824) on the already
        testid-anchored :attr:`BUCKET_ROW` locator — the ONLY compliant
        state signal per ``.agents/testing.md`` § Locator policy (state via
        a ``data-*`` attribute on a stable testid, never a CSS-class read).
        Same "read an attribute of an existing testid-anchored locator"
        shape already established by :meth:`is_file_checkbox_checked`
        (ELITEA-1840).

        Args:
            bucket_name: Exact name of the bucket row to check.
            timeout: Maximum wait time in milliseconds for the row itself
                to be visible before reading its attribute.

        Returns:
            True if the row currently carries ``data-selected="true"``.
        """
        row = self.page.locator(self.BUCKET_ROW.format(bucket_name))
        row.wait_for(state="visible", timeout=timeout)
        return row.get_attribute("data-selected") == "true"

    @action("Click bucket row (left panel)")
    def click_bucket_row(self, bucket_name: str, timeout: int = 10000) -> None:
        """Click *bucket_name*'s own row in the left-panel tree, via its testid.

        New sibling to :meth:`select_bucket` (ELITEA-1824) — that legacy
        method's own locator predates the testid-only policy (a generic
        ``[cursor="pointer"]:has-text(...)`` CSS match) and always waits for
        ``_wait_for_bucket_panel`` afterward, which assumes the click is a
        *navigate to a possibly-different bucket* action. This method is for
        the narrower, testid-anchored case: clicking the ALREADY-selected
        bucket's own row to exercise its expand/collapse **toggle**
        (confirmed live, CLARIFICATION
        https://github.com/EliteaAI/elitea-testing-public/issues/651 — a
        single click on an already-active bucket row toggles rather than
        unconditionally expands) or to re-select the bucket root after
        navigating into one of its subfolders. Does not itself wait for any
        follow-on state — callers needing deterministic toggle sequencing
        should check the expected post-click condition (e.g. a tree-item's
        visibility) and click again if it did not yet flip, per the AFS's
        own guidance.

        Args:
            bucket_name: Exact name of the bucket row to click.
            timeout: Maximum wait time in milliseconds for the row itself
                to be visible before clicking.
        """
        row = self.page.locator(self.BUCKET_ROW.format(bucket_name))
        row.wait_for(state="visible", timeout=timeout)
        row.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked bucket row '%s'", bucket_name)

    # ------------------------------------------------------------------
    # Bucket-row dot-menu flow (ELITEA-1808)
    # ------------------------------------------------------------------

    @action("Open bucket row's actions dot-menu")
    def open_bucket_menu(self, bucket_name: str, timeout: int = 10000) -> None:
        """Hover a bucket row and click its 3-dot actions menu trigger.

        Unlike the file-row dot-menu (:meth:`open_file_actions_menu`), the
        bucket-row trigger is ``display:none`` until the row is hovered
        (confirmed live via ``BucketItem.jsx``'s ``menuContainer`` style) —
        hovering the row (:attr:`BUCKET_ROW`) first is required; the
        trigger has no bounding box to hover directly before that.

        Waits for the 'Upload files' item to render as proof the dropdown
        actually opened (this case's own scope — see the AFS's Concrete
        Handles table: 'Rename' / 'Pin to top' / 'Delete' have no testid
        added, out of scope for this case).

        Args:
            bucket_name: Exact name of the bucket whose menu to open.
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the row, the trigger, or the opened menu's
                'Upload files' item is not visible within *timeout*.
        """
        logger.info("Opening actions dot-menu for bucket '%s'", bucket_name)
        row = self.page.locator(self.BUCKET_ROW.format(bucket_name))
        row.wait_for(state="visible", timeout=timeout)
        row.hover()

        trigger = self.page.locator(self.BUCKET_MENU_BUTTON.format(bucket_name))
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()

        self.bucket_menu_upload_files_menuitem.wait_for(state="visible", timeout=timeout)
        logger.info("Actions dot-menu open for bucket '%s'", bucket_name)

    def get_bucket_menu_items_text(self, bucket_name: str, timeout: int = 10000) -> str:
        """Return the open bucket-menu dropdown's FULL text content (ELITEA-1817).

        Call :meth:`open_bucket_menu` first. Reads the whole testid'd
        dropdown container (:attr:`BUCKET_MENU_CONTAINER`) rather than
        per-item testids — "Rename"/"Pin to top" carry no ``key`` field in
        ``BucketItem.jsx``'s ``menuItems`` array (confirmed live), so this
        is the compliant way to verify all 4 items' presence/label/order
        without a raw selector chained off a testid'd parent. Same "read
        the whole testid'd container's text" pattern already established
        by :meth:`get_file_row_text`.

        Args:
            bucket_name: Exact name of the bucket whose (already-open) menu
                to read.
            timeout: Maximum wait time in milliseconds for the container to
                be visible.

        Returns:
            The dropdown's full stripped text content, e.g.
            ``"Upload filesRenamePin to topDelete"``.
        """
        container = self.page.locator(self.BUCKET_MENU_CONTAINER.format(bucket_name))
        container.wait_for(state="visible", timeout=timeout)
        text = (container.text_content() or "").strip()
        logger.info("Bucket-menu items text for '%s': %r", bucket_name, text)
        return text

    @action("Click bucket-menu 'Delete' item")
    def click_bucket_menu_delete_item(self, timeout: int = 10000) -> None:
        """Click the open bucket-menu's 'Delete' item, to open the confirm modal.

        Call :meth:`open_bucket_menu` first — same "caller opens, this
        clicks" division of responsibility as
        :meth:`click_bucket_menu_upload_files_item` (that method's own
        docstring: "Call open_bucket_menu first"; it does not re-open the
        menu itself). Not re-invoking :meth:`open_bucket_menu` here matters
        for this case specifically: Test Step 10 reads the dropdown's full
        text (:meth:`get_bucket_menu_items_text`) while the SAME open menu
        from Test Step 9 is still showing — re-clicking the hover-gated
        trigger a second time would risk toggling the already-open menu
        closed instead of clicking Delete.

        Args:
            timeout: Maximum wait time in milliseconds for the
                delete-confirmation modal to become visible after the click.
        """
        self.bucket_menu_delete_menuitem.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Clicked 'Delete' in the open bucket-menu")

    @action("Select files via bucket-menu 'Upload files'")
    def click_bucket_menu_upload_files_item(
        self, file_paths: list[str], timeout: int = 15000
    ) -> None:
        """Click the open bucket-menu's 'Upload files' item and select files.

        Call :meth:`open_bucket_menu` first. This is a second, fresh entry
        point into the SAME "Upload files to ..." dialog :meth:`upload_files`
        already drives from the right-panel toolbar — confirmed live
        (ELITEA-1808 AFS) both converge on the identical modal/endpoint.
        Waits for the file-chooser modal state to fire (confirmed live: no
        loading delay, same immediacy as the toolbar upload button per
        ELITEA-1832's precedent), then sets the given file paths in one
        call — the click, the chooser firing, and the file selection are
        one mechanically inseparable Playwright action (matches the AFS's
        own folding of case steps 9-12). Does not wait for the follow-on
        "Upload files to ..." dialog — call :meth:`wait_for_upload_path_dialog`
        next.

        Args:
            file_paths: Absolute paths of the file(s) to select.
            timeout: Maximum wait time for the file chooser, in milliseconds.
        """
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.bucket_menu_upload_files_menuitem.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_paths)
        logger.info(
            "Selected %d file(s) for upload via bucket-menu: %s",
            len(file_paths), file_paths,
        )

    def wait_for_file_in_tree(self, file_name: str, timeout: int = 15000) -> None:
        """Wait for a file/folder to appear in the left-panel bucket tree (ELITEA-1808).

        Waits on the CONDITION that the item's own dynamic
        ``artifacts-tree-item-{file_name}`` testid becomes visible — same
        condition-wait discipline as :meth:`wait_for_bucket_in_list`, never a
        fixed sleep and never an assertion built on a raw ``page.locator(...)``
        constructed at the call site (locators stay class-level fields on the
        page object per ``.claude/rules/page-objects.md``).

        Args:
            file_name: Full relative path of the file/folder, keyed the same
                way as the tree node itself (e.g. ``"test.txt"``, or
                ``"a1/sample.txt"`` when nested in a subfolder).
            timeout: Maximum wait time in milliseconds.
        """
        self.page.locator(self.ARTIFACTS_TREE_ITEM.format(file_name)).wait_for(
            state="visible", timeout=timeout
        )
        logger.info("File '%s' visible in the left-panel tree", file_name)

    def is_tree_item_visible(self, item_key: str, timeout: int = 5000) -> bool:
        """Return whether a left-panel tree node is currently visible (ELITEA-1824).

        Non-raising sibling to :meth:`wait_for_file_in_tree` (which raises
        on timeout) — same "poll a short window, return bool" shape as
        :meth:`is_bucket_empty`/:meth:`bucket_exists`/:meth:`file_exists`.
        Used for the deterministic toggle-click sequencing case step 37/38
        (CLARIFICATION https://github.com/EliteaAI/elitea-testing-public/issues/651
        requires) — check the expected post-click state without failing the
        test if the toggle hasn't flipped yet on the first click.

        Args:
            item_key: Full relative path of the file/folder, keyed the same
                way as the tree node itself (e.g. ``"a1/"`` for a folder).
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the node is visible within *timeout*, False otherwise.
        """
        try:
            self.page.locator(self.ARTIFACTS_TREE_ITEM.format(item_key)).wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    @action("Click tree item (left panel)")
    def click_tree_item(self, item_key: str, timeout: int = 10000) -> None:
        """Click a left-panel tree node by its full relative key (ELITEA-1824).

        Testid-anchored sibling to :meth:`navigate_into_folder` (which
        locates via a raw ``[data-tour="artifacts-buckets-panel"]`` +
        text-match, predating the testid-only policy) — this method uses
        the already-established :attr:`ARTIFACTS_TREE_ITEM` template
        directly, consistent with :meth:`wait_for_file_in_tree` and
        :meth:`is_tree_item_selected`.

        Args:
            item_key: Full relative path of the file/folder, keyed the same
                way as the tree node itself (e.g. ``"a1/"`` for a folder —
                note the trailing slash on folder keys — or
                ``"sample.txt"`` for a file, no trailing slash).
            timeout: Maximum wait time in milliseconds.
        """
        item = self.page.locator(self.ARTIFACTS_TREE_ITEM.format(item_key))
        item.wait_for(state="visible", timeout=timeout)
        item.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked tree item '%s'", item_key)

    def is_tree_item_selected(self, item_key: str, timeout: int = 10000) -> bool:
        """Return whether a left-panel tree node is the selected one.

        Reads the ``data-selected`` attribute (ELITEA-1824) on the already
        testid-anchored :attr:`ARTIFACTS_TREE_ITEM` locator — same
        attribute-read shape as :meth:`is_bucket_selected` and the
        established :meth:`is_file_checkbox_checked` precedent (ELITEA-1840).

        Args:
            item_key: Full relative path of the file/folder, keyed the same
                way as the tree node itself (e.g. ``"a1/"`` for a folder —
                note the trailing slash on folder keys — or
                ``"sample.txt"`` for a file, no trailing slash).
            timeout: Maximum wait time in milliseconds for the node itself
                to be visible before reading its attribute.

        Returns:
            True if the node currently carries ``data-selected="true"``.
        """
        item = self.page.locator(self.ARTIFACTS_TREE_ITEM.format(item_key))
        item.wait_for(state="visible", timeout=timeout)
        return item.get_attribute("data-selected") == "true"

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

    def wait_for_file_count(self, expected_count: int, timeout: int = 15000) -> None:
        """Wait until the file table shows exactly *expected_count* rows.

        Condition-based wait for the file table to settle after navigation.
        ELITEA-1847's original diagnosis (3/8 exploratory runs) attributed
        the empty-table symptom this guards against to a standalone
        "S3-listing-fetch lag" race — independent of the bucket-name text
        :meth:`navigate_to_bucket`'s ``_wait_for_bucket_panel()`` waits on —
        and added this method to poll past it. PR #661's independent re-run
        (2/5 clean-process runs) showed that diagnosis was WRONG: the
        failure screenshot had an unrelated bucket ("aa") open instead of
        the seeded target, i.e. the already-known issue #638 URL-param-loss
        race, which :meth:`navigate_to_bucket` now retries around directly
        (same guard as :meth:`navigate_to_bucket_folder`). With the correct
        bucket loaded, this method remains a legitimate, harmless
        condition-based wait for any residual render lag in the file table
        — it just isn't a substitute for loading the correct bucket, since
        a stably-wrong-bucket empty table can never converge here no matter
        the timeout. Uses Playwright's own auto-retrying
        ``expect(...).to_have_count()`` on the same row locator
        :meth:`get_file_names`/:meth:`get_file_count` already use — never a
        fixed sleep.

        Args:
            expected_count: The exact number of file/folder rows to wait for.
            timeout: Maximum wait time in milliseconds.
        """
        expect(self._file_rows()).to_have_count(expected_count, timeout=timeout)
        logger.info("File table settled at %d row(s)", expected_count)

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

    def get_file_row_text(self, filename: str, timeout: int = 10000) -> str:
        """Return a file row's full rendered text, by exact file name (ELITEA-1808).

        Reads the WHOLE row's text content via the existing testid-anchored
        row locator + ``.filter(has_text=...)`` (the same pattern the
        legacy :meth:`download_file` already uses to locate a row by name)
        rather than indexing into individual cells: ``ArtifactTable.jsx``
        renders columns through a shared, generic grid component
        (``GridTableRowDataCell``) with no per-cell testid, so cell-position
        indexing would require a new non-testid selector. Reading the whole
        row's text is sufficient to substring-check a column's rendered
        value (e.g. the file-type label or the formatted size string) —
        used for Test Step 16 (Name/Type/Size) without introducing one.

        Args:
            filename: Exact file name to look up (matches the Name cell's
                text).
            timeout: How long to wait for the row to appear.

        Returns:
            The row's full text content, stripped.
        """
        row = self.page.get_by_test_id("artifacts-file-row").filter(has_text=filename).first
        row.wait_for(state="visible", timeout=timeout)
        text = (row.text_content() or "").strip()
        logger.info("Row text for '%s': %r", filename, text)
        return text

    # ------------------------------------------------------------------
    # Per-row checkbox selection (ELITEA-1840)
    # ------------------------------------------------------------------

    @action("Select file checkbox")
    def select_file_checkbox(self, filename: str, timeout: int = 10000) -> None:
        """Click the checkbox for a given file/folder row, by base name.

        Args:
            filename: Exact base file name (e.g. ``"sample.txt"``) — the
                checkbox testid uses the base name only (``row.id``), even
                for files nested in a subfolder.
            timeout: Maximum wait time in milliseconds.
        """
        checkbox = self.page.locator(self.ARTIFACT_FILE_CHECKBOX.format(filename))
        checkbox.wait_for(state="visible", timeout=timeout)
        checkbox.click()
        logger.info("Clicked checkbox for '%s'", filename)

    def is_file_checkbox_checked(self, filename: str, timeout: int = 10000) -> bool:
        """Return whether a given file/folder row's checkbox is checked.

        **Implementer finding (ELITEA-1840):** the checkbox's ``data-testid``
        (threaded via ``BaseCheckbox``'s ``...restProps`` passthrough) lands
        on the MUI ``ButtonBase``/``MuiCheckbox-root`` wrapping ``<span>``,
        NOT on the nested ``<input type="checkbox">`` — confirmed live via
        DOM query. Playwright's ``Locator.is_checked()`` requires the
        element itself to be an input/role=checkbox and raises ``"Not a
        checkbox or radio button"`` on the span, so this reads the MUI
        ``Mui-checked`` CSS class instead — confirmed live to toggle in
        lockstep with the underlying input's ``checked`` property on every
        click. This reads an ATTRIBUTE of the already testid-anchored
        locator (like reading the progress bar's ``aria-valuenow``), not a
        new chained/raw selector — no separate testid needed on the input.

        Args:
            filename: Exact base file name of the row to check.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the row's checkbox is currently checked.
        """
        checkbox = self.page.locator(self.ARTIFACT_FILE_CHECKBOX.format(filename))
        checkbox.wait_for(state="visible", timeout=timeout)
        class_attr = checkbox.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def get_checkbox_states(self, timeout: int = 10000) -> dict[str, bool]:
        """Return ``{filename: checked}`` for every visible file/folder row.

        Queries EVERY visible row's checkbox independently (not just the
        ones a caller just clicked) — needed for case step 6's "remaining
        unchecked" verification, which must hold for rows the test never
        touched, not merely the ones it selected.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Dict mapping each visible row's base file name to its checkbox's
            checked state.
        """
        names = self.get_file_names(timeout=timeout)
        states = {name: self.is_file_checkbox_checked(name, timeout=timeout) for name in names}
        logger.info("Checkbox states: %s", states)
        return states

    # ------------------------------------------------------------------
    # Bulk delete flow (ELITEA-1847)
    # ------------------------------------------------------------------

    def get_delete_button_tooltip_text(self, timeout: int = 10000) -> str:
        """Return the toolbar delete icon's tooltip text.

        Reads the STATIC aria-label MUI's Tooltip clones onto
        :attr:`delete_files_button`'s wrapping element — no hover or
        ``role="tooltip"`` popper wait needed, same no-hover-required
        technique already established for other MUI tooltips in this
        codebase (ELITEA-1809 memory). The text reflects "Delete selected
        files" or "Delete all files" depending on whether every currently
        rendered row is selected.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The tooltip text, e.g. ``"Delete selected files"``.
        """
        self.delete_files_button.wait_for(state="visible", timeout=timeout)
        return self.delete_files_button.get_attribute("aria-label") or ""

    @action("Click toolbar 'Delete files' button")
    def click_delete_files_button(self, timeout: int = 10000) -> None:
        """Click the toolbar delete icon to open the delete-confirmation modal.

        Confirmed live (ELITEA-1847): :attr:`delete_files_button` resolves to
        the wrapping ``<Box component="span">``, whose bounding box is
        pixel-identical to the inner (testid-less) ``IconButton`` — clicking
        the wrapper directly fires the button's own ``onClick``, no
        ``.locator("button")`` chaining required.

        Args:
            timeout: Maximum wait time in milliseconds for the button to
                become visible before clicking.
        """
        self.delete_files_button.wait_for(state="visible", timeout=timeout)
        self.delete_files_button.click()
        logger.info("Clicked toolbar 'Delete files' button")

    def get_delete_confirm_message_text(self, timeout: int = 10000) -> str:
        """Return the delete-confirmation modal's message text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The message's stripped text content, e.g.
            ``"Are you sure to delete the selected files?"``.
        """
        self.delete_confirm_message.wait_for(state="visible", timeout=timeout)
        return (self.delete_confirm_message.text_content() or "").strip()

    @action("Confirm delete (delete-confirmation modal)")
    def confirm_delete(self, timeout: int = 15000):
        """Click 'Delete' in the confirmation modal and return the DELETE response.

        Wraps the click in ``page.expect_response`` (the same idiom already
        used elsewhere in this page object, e.g.
        :meth:`click_bucket_save_button`), matching the artifacts DELETE
        endpoint. Confirmed live (ELITEA-1847) this fires exactly one request
        per confirm click, whose ``fname[]`` params are the selected
        folder(s)' fully-expanded underlying file keys (never a bare folder
        key) — see ``ArtifactTable.jsx``'s
        ``expandFoldersToAllItems()``/``getItemsUnderFolder()``.

        Args:
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            Playwright ``Response`` object for the matching DELETE request.
        """
        with self.page.expect_response(
            lambda r: "artifacts/artifacts" in r.url and r.request.method == "DELETE",
            timeout=timeout,
        ) as response_info:
            self.delete_confirm_button.click()
        return response_info.value

    @action("Confirm delete bucket (delete-confirmation modal)")
    def confirm_delete_bucket(self, timeout: int = 15000):
        """Click 'Delete' in the confirmation modal and return the bucket-DELETE response.

        Sibling to :meth:`confirm_delete` (ELITEA-1847) — that method's
        response-wait is scoped to ``"artifacts/artifacts" in r.url``, the
        FILE/FOLDER delete endpoint, which never fires for a bucket-level
        delete (confirmed live, ELITEA-1817): the bucket dot-menu's
        "Delete" reuses the identical shared ``DeleteEntityModal`` root, but
        drives ``DELETE .../artifacts/buckets/default/{project_id}?name=...``
        instead — a QUERY-PARAMETER shape, notably different from
        ``ArtifactAPI.delete_bucket()``'s path-segment shape. Same
        ``expect_response`` idiom as :meth:`confirm_delete`, different URL
        substring; reuses :attr:`delete_confirm_button` as-is.

        Args:
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            Playwright ``Response`` object for the matching bucket DELETE.
        """
        with self.page.expect_response(
            lambda r: "artifacts/buckets" in r.url and r.request.method == "DELETE",
            timeout=timeout,
        ) as response_info:
            self.delete_confirm_button.click()
        return response_info.value

    # Note (ELITEA-1847): the AFS's Axis-2 "cancel-path regression guard"
    # (select a row, open the modal, click Cancel, confirm zero network +
    # item still present) was verified live during analyst exploration via
    # a getByRole("button", {name: "Cancel"}) lookup — explicitly flagged in
    # the AFS as an exploratory aside outside this case's asserted scope,
    # not a handle to ship. DeleteEntityModal.jsx's Cancel button carries no
    # testid (confirmed absent, out of this case's required-elements list
    # per the AFS's Concrete Handles table) and this project's locator
    # policy forbids a non-testid `get_by_role` addition in a page object
    # regardless of scope — so no `cancel_delete()` method is added here.
    # A future case that needs to assert/drive Cancel specifically should
    # add a testid via `add-data-testid` first (same AFS guidance).

    # ------------------------------------------------------------------
    # Upload flow (ELITEA-1832 — duplicate handling)
    # ------------------------------------------------------------------

    @action("Select files via native file picker")
    def upload_files(self, file_paths: list[str], timeout: int = 15000) -> None:
        """Click the upload button and select files via the native file chooser.

        Waits for the file-chooser modal state to fire (confirmed live: it
        fires the instant the upload button is clicked, no loading delay),
        then sets the given file paths in one call. Does not wait for the
        follow-on "Upload files to ..." dialog — call
        :meth:`wait_for_upload_path_dialog` next.

        Args:
            file_paths: Absolute paths of the file(s) to select.
            timeout: Maximum wait time for the file chooser, in milliseconds.
        """
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.upload_files_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_paths)
        logger.info("Selected %d file(s) for upload: %s", len(file_paths), file_paths)

    @action("Select files via native file picker (empty-state entry point)")
    def upload_files_via_empty_state(self, file_paths: list[str], timeout: int = 15000) -> None:
        """Click the CENTER empty-state 'Upload files' button and select files.

        A separate entry point from :meth:`upload_files` (the toolbar
        button) — :attr:`upload_files_empty_state_button` is a DIFFERENT
        DOM element (ELITEA-1824), only rendered while the selected bucket
        is empty (``ArtifactTableNoFiles.jsx``). Same
        click → file-chooser → ``set_files()`` shape as :meth:`upload_files`
        (confirmed live: no loading delay, same immediacy).

        Args:
            file_paths: Absolute paths of the file(s) to select.
            timeout: Maximum wait time for the file chooser, in milliseconds.
        """
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.upload_files_empty_state_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_paths)
        logger.info(
            "Selected %d file(s) for upload via empty-state button: %s",
            len(file_paths), file_paths,
        )

    def wait_for_upload_path_dialog(self, timeout: int = 10000) -> None:
        """Wait for the 'Upload files to ...' dialog to become visible.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.upload_path_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("'Upload files to ...' dialog visible")

    @action("Close upload-path dialog (abandon this upload attempt)")
    def close_upload_path_dialog(self, timeout: int = 10000) -> None:
        """Close the 'Upload files to ...' dialog without uploading (ELITEA-1824).

        Uses Escape rather than clicking "Cancel" — confirmed via source
        (``UploadPathDialog.jsx``) the Cancel button carries no testid, and
        the dialog's ``BaseModal`` wires ``onClose`` (the SAME handler
        Cancel calls) to the standard MUI Escape-key behavior. Escape needs
        no locator/selector at all, so it fully respects this project's
        testid-only locator policy without requiring a new testid for a
        button whose only use is closing this one dialog.

        Used for the ELITEA-1824 bucket-menu-upload defect (#649) workaround
        — the buggy Path pre-fill lives in the read-only
        bucket/currentPrefix ``startAdornment`` (confirmed live: NOT
        editable — 10x Backspace on the input produces zero change), so the
        only way to get a clean pre-fill is to abandon this dialog, return
        to bucket root, and re-open the SAME upload flow from there.

        Args:
            timeout: Maximum wait time in milliseconds for the dialog to
                become hidden after Escape.
        """
        self.page.keyboard.press("Escape")
        self.upload_path_dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("'Upload files to ...' dialog closed via Escape")

    def get_upload_path_prefix_text(self) -> str:
        """Return the visible text of the Path field in the upload dialog.

        Includes the read-only bucket/prefix ``startAdornment`` segment
        (e.g. ``"{bucket_name}/"``) — used to assert the Path field is
        pre-filled with the target bucket's name (case step 7).

        Returns:
            The Path field's combined visible text, stripped.
        """
        return (self.upload_path_input.text_content() or "").strip()

    def get_upload_path_normalized_prefix(self) -> str:
        """Return the read-only bucket/currentPrefix segment, label-stripped (ELITEA-1824).

        :meth:`get_upload_path_prefix_text`'s raw ``text_content()`` read
        includes the MUI floating label text ("Path") plus zero-width-space
        (U+200B) padding characters alongside the actual prefix value —
        confirmed live via DOM inspection: the field's testid'd wrapper's
        text content is ``"Path" + U+200B + <prefix> + U+200B``, not just
        ``<prefix>``. This strips both so callers can assert the prefix
        value directly (e.g. ``"{bucket_name}/"`` or ``"{bucket_name}/a1/"``).

        Returns:
            The prefix value alone, e.g. ``"{bucket_name}/"``.
        """
        raw = self.get_upload_path_prefix_text()
        return raw.replace("Path", "", 1).replace("​", "").strip()

    def get_upload_path_typed_value(self, timeout: int = 5000) -> str:
        """Return the Path field's user-typed value (ELITEA-1824).

        The read-only prefix (:meth:`get_upload_path_normalized_prefix`)
        and the editable, user-typed suffix are two SEPARATE DOM elements
        (``UploadPathDialog.jsx``'s read-only ``InputAdornment`` vs. its
        native ``<input>``) — a native ``<input>``'s value is never part of
        its own or any ancestor's ``text_content()``, confirmed live.
        Reads :attr:`upload_path_input_field` (the dedicated testid on the
        actual ``<input>``, added for this case) via ``.input_value()``.

        Args:
            timeout: Maximum wait time in milliseconds for the field to be
                visible before reading its value.

        Returns:
            The exact string currently typed into the editable input (e.g.
            ``"a1"``), or ``""`` if nothing has been typed.
        """
        self.upload_path_input_field.wait_for(state="visible", timeout=timeout)
        return self.upload_path_input_field.input_value()

    def get_upload_path_combined_text(self) -> str:
        """Return the FULL path a human sees: prefix + typed suffix (ELITEA-1824).

        Concatenates :meth:`get_upload_path_normalized_prefix` (the
        read-only bucket/currentPrefix segment) with
        :meth:`get_upload_path_typed_value` (whatever the user has typed) —
        the same combined value the case's own steps describe (e.g.
        ``"{bucket_name}/a1"`` after appending ``"a1"`` to a root-only
        prefix).

        Returns:
            The prefix and typed value concatenated, e.g.
            ``"{bucket_name}/a1"``.
        """
        return self.get_upload_path_normalized_prefix() + self.get_upload_path_typed_value()

    @action("Confirm upload (triggers client-side duplicate detection)")
    def click_upload_path_upload_button(self) -> None:
        """Click 'Upload' in the 'Upload files to ...' dialog.

        Triggers the app's client-side duplicate check against the bucket's
        already-fetched file listing — confirmed live (ELITEA-1832) to fire
        NO network request when a duplicate is present; the "Resolve
        duplicates" dialog opens purely from local state.
        """
        self.upload_path_upload_button.click()

    def click_upload_path_upload_button_and_capture_response(self, timeout: int = 15000):
        """Click 'Upload' and return the matching PUT response (ELITEA-1808).

        Additive sibling to :meth:`click_upload_path_upload_button` — that
        method stays unmodified (ELITEA-1832 relies on it firing ZERO
        network requests when a duplicate exists; wrapping a response-wait
        there would time out on that legitimate no-request outcome). This
        variant is for callers who know the click WILL fire a network PUT
        (no duplicates possible, e.g. a freshly created, empty bucket) and
        want to assert on the response directly — confirmed live that
        deriving the status from :meth:`capture_requests_matching`'s async
        listener alone can still read ``None`` immediately after the click
        resolves (a request/response pairing race).

        Args:
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            Playwright ``Response`` object for the matching upload PUT.
        """
        with self.page.expect_response(
            lambda r: "artifacts/s3" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.click_upload_path_upload_button()
        return response_info.value

    def wait_for_resolve_duplicates_dialog(self, timeout: int = 10000) -> None:
        """Wait for the 'Resolve duplicates' dialog to become visible.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.resolve_duplicates_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("'Resolve duplicates' dialog visible")

    def get_resolve_duplicates_filenames(self) -> list[str]:
        """Return the duplicate filenames listed in the 'Resolve duplicates' dialog.

        Each row renders the filename split across two adjacent spans (base
        name + extension); this reads the combined text of every row.

        Returns:
            List of filename strings, one per duplicate row.
        """
        rows = self.resolve_duplicates_filename
        count = rows.count()
        names = [(rows.nth(i).text_content() or "").strip() for i in range(count)]
        logger.info("Duplicate filenames listed: %s", names)
        return names

    @action("Cancel duplicate resolution (aborts entire upload)")
    def click_resolve_duplicates_cancel_button(self) -> None:
        """Click 'Cancel' in the 'Resolve duplicates' dialog.

        Aborts the ENTIRE upload operation, including any non-duplicate
        files selected in the same batch — confirmed live (ELITEA-1832,
        2/2 runs): fires no network request, closes the dialog, and leaves
        bucket contents unchanged.
        """
        self.resolve_duplicates_cancel_button.click()

    def wait_for_resolve_duplicates_dialog_closed(self, timeout: int = 10000) -> None:
        """Wait for the 'Resolve duplicates' dialog to be hidden/removed after Cancel.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.resolve_duplicates_dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("'Resolve duplicates' dialog closed")

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

    @action("Open file actions dot-menu")
    def open_file_actions_menu(self, filename: str, timeout: int = 10000) -> None:
        """Click the dot-menu trigger for *filename* to open its actions dropdown.

        Testid-compliant replacement for the legacy :meth:`download_file`'s
        own hover-reveal + raw-CSS trigger lookup — retained as-is there for
        ELITEA-1327's own signature/behavior, not copied here. Confirmed live
        (ELITEA-1839, 2/2 runs): the trigger button is visible WITHOUT
        hovering the row first in the current app — no hover-then-500ms-wait
        sequence is needed.

        Args:
            filename: Exact base file name (e.g. ``"sample.txt"``) — the
                dot-menu trigger testid uses the base name only, even for
                files nested in a subfolder.
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the trigger or the opened menu's 'Download' item
            is not visible within *timeout*.
        """
        logger.info("Opening actions dot-menu for '%s'", filename)
        trigger = self.page.locator(self.ARTIFACT_ACTIONS_MENU_BUTTON.format(filename))
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()
        # Wait for the menu to actually render before returning control —
        # 'Download' is always present for a file row (ArtifactRowActions.jsx).
        self.download_menu_item.wait_for(state="visible", timeout=timeout)
        logger.info("Actions dot-menu open for '%s'", filename)

    @action("Click 'Download' menu item")
    def click_download_menu_item(self, timeout: int = 5000) -> Download:
        """Click the open dropdown's 'Download' item and capture the download.

        Wraps the click in ``page.expect_download`` with a deliberately
        SHORT default timeout (ELITEA-1839): a genuinely blocking ZIP-prep
        flow would exceed it, so the timeout itself doubles as a meaningful
        immediacy assertion rather than just a wait.

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object (caller can use ``download.path()``
            to access the downloaded file's bytes).

        Raises:
            TimeoutError: If no download event fires within *timeout*.
        """
        with self.page.expect_download(timeout=timeout) as download_info:
            self.download_menu_item.click()

        download = download_info.value
        logger.info(
            "Download started via dropdown → suggested filename: %s",
            download.suggested_filename,
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
    # Main-panel breadcrumb header helpers (ELITEA-1824)
    # ------------------------------------------------------------------

    def get_breadcrumb_bucket_text(self, timeout: int = 10000) -> str:
        """Return the bucket-name label's text in the main-panel header.

        Always present once a bucket is selected, regardless of folder
        depth (:attr:`breadcrumb_bucket_label`).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The bucket-name label's stripped text content.
        """
        self.breadcrumb_bucket_label.wait_for(state="visible", timeout=timeout)
        return (self.breadcrumb_bucket_label.text_content() or "").strip()

    def get_breadcrumb_folder_names(self, timeout: int = 3000) -> list[str]:
        """Return the currently rendered breadcrumb folder-crumb texts.

        :attr:`breadcrumb_folder_label` is CONDITIONALLY present — empty
        list when the selected bucket is at its root (no folder crumbs
        rendered), one entry per folder level once navigated into a
        subfolder.

        Args:
            timeout: Short wait — used only to let a just-triggered
                navigation settle; absence is a normal (root) state, not
                an error, so this does not raise on timeout.

        Returns:
            List of folder-crumb text strings, in breadcrumb order
            (outermost first). Empty list at bucket root.
        """
        try:
            self.breadcrumb_folder_label.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []
        labels = self.breadcrumb_folder_label
        count = labels.count()
        names = [(labels.nth(i).text_content() or "").strip() for i in range(count)]
        logger.info("Breadcrumb folder crumbs: %s", names)
        return names
