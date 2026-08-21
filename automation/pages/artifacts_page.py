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
from playwright.sync_api import Download, Locator, Page, expect

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

    Inherits from BasePage:
    - project_selector_trigger, SELECT_OPTION, switch_project() for project switching
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

    bucket_name_helper_text = LocatorDescriptor(
        testid="artifacts-bucket-name-helper-text",
        description="Inline validation helper-text under the Name field on the "
        "'New Bucket' form (ELITEA-1811/1814 — new testid, implementer). Renders "
        "the yup schema's error message once the field is touched/invalid; "
        "empty/absent while the field is valid. Wired via CreateBucket.jsx's "
        "TextField `FormHelperTextProps={{'data-testid': ...}}`, alongside its "
        "existing `inputProps`-based name-input testid — MUI v5 supports both "
        "prop shapes on the same TextField.",
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

    download_files_tooltip = LocatorDescriptor(
        testid="artifacts-download-files-tooltip",
        description="'Download files' Tooltip's wrapping <Box component=\"span\"> "
        "(ELITEA-1841 — new testid, implementer Phase-2 amendment). A DIFFERENT DOM "
        "node from :attr:`download_files_button` — that testid resolves to the INNER "
        "<button>, while MUI's Tooltip clones its static aria-label onto this "
        "WRAPPING span one level up (confirmed live: the inner button carries no "
        "aria-label of its own). ArtifactTableToolbar.jsx is page-local/single-"
        "consumer (not shared), so the testid is hardcoded directly in JSX — no "
        "caller-prop threading needed, unlike :attr:`select_all_checkbox` below.",
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

    # ELITEA-1835: separate description Typography (distinct DOM node from
    # upload_path_input above) — reads a GENERIC, bucket-name-free string at
    # bucket root and only interpolates the bucket name once a subfolder is
    # active (UploadPathDialog.jsx's descriptionMessage useMemo). No adjacent
    # read-only adornment pollutes this element's own text_content() the way
    # upload_path_input's does, so no "normalized" companion method is needed.
    upload_path_description_text = LocatorDescriptor(
        testid="artifacts-upload-path-description-text",
        description="'Upload files to ...' dialog's description line, above the "
        "Path field — a separate element from upload_path_input; text content "
        "varies by whether a subfolder (currentPrefix) is active",
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

    resolve_duplicates_message_text = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-message-text",
        description="'Resolve duplicates' dialog's message line (DuplicateDialogContent.jsx) — "
        "text is singular ('This file already exists...') for exactly 1 duplicate, plural "
        "('{N} files already exist...') for more than 1 (ELITEA-1828).",
    )

    resolve_duplicates_cancel_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-cancel-button",
        description="'Cancel' button inside the 'Resolve duplicates' dialog — aborts "
        "the ENTIRE upload operation, including any non-duplicate files in the batch",
    )

    resolve_duplicates_skip_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-skip-button",
        description="'Skip' button inside the 'Resolve duplicates' dialog — uploads only "
        "the non-duplicate file(s) in the batch, leaves the duplicate entirely untouched "
        "(ELITEA-1828/1829).",
    )

    resolve_duplicates_replace_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-replace-button",
        description="'Replace' button inside the 'Resolve duplicates' dialog — "
        "visibility-only as of ELITEA-1828; no cluster case exercises it yet.",
    )

    resolve_duplicates_keep_both_button = LocatorDescriptor(
        testid="artifacts-resolve-duplicates-keep-both-button",
        description="'Keep both' button inside the 'Resolve duplicates' dialog — uploads "
        "the new file under a renamed '{baseName} - Copy{extension}' key, leaves the "
        "original untouched (ELITEA-1828/1831).",
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

    # Prefix+suffix (any-row) variant of ARTIFACT_ACTIONS_MENU_BUTTON — every
    # rendered file-row actions trigger, regardless of row id (ELITEA-1803).
    ARTIFACT_ACTIONS_MENU_BUTTON_ANY_SELECTOR = (
        '[data-testid^="artifact-actions-"][data-testid$="-menu-button"]'
    )

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

    # Prefix (any-row) variant of ARTIFACT_FILE_CHECKBOX — every rendered
    # file-row selection checkbox, regardless of row id. Same
    # `[data-testid^="…"]` shape already established by
    # :attr:`BUCKET_ROW_ANY_SELECTOR`. Used by ELITEA-1803 to assert that a
    # file row carries its checkbox without needing to know the row's
    # server-assigned id.
    ARTIFACT_FILE_CHECKBOX_ANY_SELECTOR = '[data-testid^="artifacts-file-checkbox-"]'

    select_all_checkbox = LocatorDescriptor(
        testid="artifacts-select-all-checkbox",
        description="Table-header 'Select all' checkbox (ELITEA-1841 — new testid, "
        "implementer). GridTableHeader.jsx is a shared component (7 consumers) — "
        "threaded via a new caller-supplied `selectAllCheckboxTestId` prop, wired "
        "ONLY at ArtifactTable.jsx's <GridTableHeader ...> call site, same "
        "shared-component-prop shape ELITEA-1840 already established for "
        ":attr:`ARTIFACT_FILE_CHECKBOX`'s per-row `checkboxTestId`. Same "
        "'testid lands on the MUI wrapping <span>, not the nested <input>' "
        "shape as the per-row checkboxes — read state via the `class` attribute "
        "(:meth:`is_select_all_checkbox_checked` / "
        ":meth:`is_select_all_checkbox_indeterminate`), not `is_checked()`.",
    )

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
    # File preview/edit editor panel (ELITEA-1851/1852/1856)
    # ------------------------------------------------------------------

    # Dynamic testid template — per-row "View/Edit file" icon button
    # (ArtifactRowActions.jsx). Parameter is the row's full displayed name
    # (row.name), same identity semantics as ARTIFACT_ACTIONS_MENU_BUTTON.
    ARTIFACT_FILE_PREVIEW_BUTTON = '[data-testid="artifacts-file-preview-button-{}"]'

    # Static testid on every file row — the row itself is name-agnostic;
    # identity comes from filtering by displayed text (`.filter(has_text=...)`),
    # same disambiguation approach as :attr:`_file_rows`. Kept as a class
    # constant (not a plain string literal in methods) so the selector stays
    # in the greppable testid inventory (`.agents/testing.md` § Locator policy).
    ARTIFACT_FILE_ROW = '[data-testid="artifacts-file-row"]'

    file_preview_close_button = LocatorDescriptor(
        testid="artifacts-preview-close-button",
        description="X (close) icon in the editor panel header "
        "(ELITEA-1851 — new testid, implementer, PreviewHeader.jsx).",
    )

    file_preview_file_path = LocatorDescriptor(
        testid="artifacts-preview-file-path",
        description="Editor panel header's full file-path Typography "
        "(ELITEA-1851 — new testid, implementer, PreviewHeader.jsx's "
        "`canvasTitle` element). Renders 'bucket/file.ext', or a truncated "
        "'bucket/ ... /folder/file.ext' form for deeply nested paths.",
    )

    file_preview_language_select = LocatorDescriptor(
        testid="artifacts-preview-language-select",
        description="Language label + dropdown in the editor panel header "
        "(ELITEA-1851 — new testid, implementer). Select.SingleSelect "
        "already supported a `data-testid` passthrough prop; just not wired "
        "at this call site before now.",
    )

    file_preview_code_editor = LocatorDescriptor(
        testid="artifacts-preview-code-editor",
        description="Wrapping container Box around the CodeMirror editor "
        "for non-markdown/html/mdx/image/docx files (ELITEA-1851 — new "
        "testid, implementer, PreviewContent.jsx's CODE branch). Line "
        "numbers (`.cm-lineNumbers`) are CodeMirror-internal DOM scoped "
        "under this testid'd parent — sanctioned #579 exception (third-party "
        "editor library internal render nodes); never extended beyond that "
        "gutter.",
    )

    # Scoped sub-selector for CodeMirror's own internal line-number gutter —
    # #579 sanctioned exception, MUST stay chained off file_preview_code_editor.
    CM_LINE_NUMBERS = ".cm-lineNumbers"

    file_preview_code_content = LocatorDescriptor(
        testid="artifacts-preview-code-content",
        description="The actual editable `.cm-content` DOM node CodeMirror "
        "renders internally (ELITEA-1851/1852 — wired via "
        "`Field.CodeMirrorEditor`'s existing `contentTestId` prop, which "
        "sets `data-testid` directly via `EditorView.contentAttributes` — a "
        "first-party extension point that already existed, just wasn't "
        "wired at this call site). Use this, not :attr:`file_preview_code_editor` "
        "(the outer wrapper), for click/keyboard-nav targeting and content "
        "read/verify.",
    )

    file_preview_save_button = LocatorDescriptor(
        testid="artifacts-preview-save-button",
        description="'Save' button in the editor panel header (ELITEA-1851 "
        "— new testid, implementer, PreviewHeader.jsx). Present but DISABLED "
        "until an edit is made (`disabled={isSaving || !hasUnsavedChanges}`) "
        "— case text describing it as 'active/blue' on open is stale; see "
        "the ELITEA-1851 AFS's Coverage Map clarification "
        "(EliteaAI/elitea-testing-public#1108).",
    )

    file_preview_discard_button = LocatorDescriptor(
        testid="artifacts-preview-discard-button",
        description="'Discard' button in the editor panel header (ELITEA-1851 "
        "— new testid, implementer, wired via `Button.DiscardButton`'s "
        "existing `dataTestId` prop). Same disabled-until-edit gating as "
        ":attr:`file_preview_save_button`.",
    )

    file_preview_overflow_menu_button = LocatorDescriptor(
        testid="file-preview-overflow-menu-menu-button",
        description="3-dot (ellipsis) actions-menu trigger in the editor "
        "panel header — EXISTS, pre-dating this case (`DotMenu` "
        "`id=\"file-preview-overflow-menu\"` in PreviewHeader.jsx). A "
        "DIFFERENT DotMenu instance from the row-level "
        "ARTIFACT_ACTIONS_MENU_BUTTON (`id=\"artifact-actions-{row.id}\"`, "
        "ELITEA-1839) — this one has Copy Content + Download + Delete; the "
        "row-level one has only Download + Delete. Don't conflate the two.",
    )

    file_preview_overflow_menu_container = LocatorDescriptor(
        testid="file-preview-overflow-menu-menu",
        description="The editor panel's 3-dot dropdown's WHOLE MUI Menu "
        "container — EXISTS, same `${id}-menu` DotMenu convention as "
        ":attr:`file_preview_overflow_menu_button`. Used to scope "
        ":attr:`EDITOR_MENU_ITEM_SELECTOR` and read the three menu items "
        "in DOM (render) order.",
    )

    # Scoped sub-selector — the three per-item testid'd MenuItems inside the
    # editor panel's dropdown. A comma-separated CSS selector list returns
    # matches in DOM (document) order regardless of the order the individual
    # `[data-testid="…"]` clauses are written in, which is exactly what
    # :meth:`get_file_preview_menu_item_labels` needs to read the dropdown's
    # actual render order.
    EDITOR_MENU_ITEM_SELECTOR = (
        '[data-testid="artifacts-preview-copy-content-menuitem"], '
        '[data-testid="artifacts-preview-download-menuitem"], '
        '[data-testid="artifacts-preview-delete-menuitem"]'
    )

    file_preview_copy_content_menuitem = LocatorDescriptor(
        testid="artifacts-preview-copy-content-menuitem",
        description="'Copy Content' item inside the editor panel's 3-dot "
        "dropdown (ELITEA-1856 — new testid, implementer). PreviewHeader.jsx's "
        "`menuItems` array had no `key` field before this case, so DotMenu's "
        "`testId: item.key` → `undefined` → no `data-testid` ever rendered; "
        "added `key: 'artifacts-preview-copy-content'`, which flows through "
        "the existing `BasicMenuItem` `data-testid={`${testId}-menuitem`}` "
        "mechanism unchanged.",
    )

    file_preview_download_menuitem = LocatorDescriptor(
        testid="artifacts-preview-download-menuitem",
        description="'Download' item inside the editor panel's 3-dot dropdown "
        "(ELITEA-1856 — new testid, implementer, same `key` mechanism as "
        ":attr:`file_preview_copy_content_menuitem`). Do not confuse with "
        ":attr:`download_menu_item` (the ROW-level dropdown's Download item, "
        "ELITEA-1839, a different DotMenu instance).",
    )

    file_preview_delete_menuitem = LocatorDescriptor(
        testid="artifacts-preview-delete-menuitem",
        description="'Delete' item inside the editor panel's 3-dot dropdown "
        "(ELITEA-1856 — new testid, implementer, same `key` mechanism as "
        ":attr:`file_preview_copy_content_menuitem`). Do not confuse with "
        ":attr:`delete_menu_item` (the ROW-level dropdown's Delete item, "
        "ELITEA-1839, a different DotMenu instance). Clicking opens the "
        "shared :attr:`delete_confirm_dialog` (same component ELITEA-1847 "
        "already testid'd for the bulk-delete flow).",
    )

    # ------------------------------------------------------------------
    # File preview/edit — markdown mode toggle + image preview
    # (ELITEA-1857/1858/1862)
    # ------------------------------------------------------------------

    file_preview_mode_toggle_group = LocatorDescriptor(
        testid="artifacts-preview-mode-toggle-group",
        description="Render-mode ToggleButtonGroup in the editor panel "
        "header (ELITEA-1857 — new testid, implementer, PreviewHeader.jsx). "
        "Present only for markdown/html/mdx/data/mermaid files "
        "(`modeTogglerAvailable` gate); absent for image/code/docx files — "
        "assert `.to_have_count(0)` for those (ELITEA-1862).",
    )

    file_preview_mode_toggle_rendered = LocatorDescriptor(
        testid="artifacts-preview-mode-toggle-rendered",
        description="'Rendered' mode ToggleButton inside "
        ":attr:`file_preview_mode_toggle_group` (ELITEA-1857 — new testid, "
        "implementer). Named by the stable `value=\"rendered\"` prop, NOT "
        "the visible label — the label text is state-conditional ('Preview' "
        "for markdown/html/mdx, 'Table' for CSV/TSV, 'Diagram' for "
        "Mermaid), which the locator policy forbids naming by. State read "
        "via `aria-pressed` chained off this testid'd element.",
    )

    file_preview_mode_toggle_code = LocatorDescriptor(
        testid="artifacts-preview-mode-toggle-code",
        description="'Code' (always labeled 'Raw') mode ToggleButton "
        "inside :attr:`file_preview_mode_toggle_group` (ELITEA-1857 — new "
        "testid, implementer). Same `aria-pressed` state-read pattern as "
        ":attr:`file_preview_mode_toggle_rendered`.",
    )

    file_preview_markdown_content = LocatorDescriptor(
        testid="artifacts-preview-markdown-content",
        description="Rendered Markdown content wrapper (ELITEA-1857 — new "
        "testid, implementer, PreviewContent.jsx's MARKDOWN branch — "
        "`<Box><Markdown>{fileContent}</Markdown></Box>`). Headings/bold/"
        "bullets verified via `.text_content()`/`.inner_html()` scoped "
        "under this testid, not a new raw selector; also the click target "
        "for the no-input-accepted negative check (ELITEA-1857 step 9).",
    )

    file_preview_image = LocatorDescriptor(
        testid="artifacts-preview-image",
        description="Rendered `<img>` element for an image file "
        "(ELITEA-1862 — new testid, implementer, PreviewContent.jsx's "
        "IMAGE branch). Only renders when `isImageFileType` — no mode "
        "toggle, no language select, no CodeMirror editor coexist with it.",
    )

    # Scoped sub-selector for CodeMirror's own internal per-line render
    # nodes — #579 sanctioned exception, MUST stay chained off
    # file_preview_code_content (whose `.cm-content` node is these lines'
    # direct parent). Used to target ONE specific known line for editing
    # (ELITEA-1858) rather than blind Control+Home-based nav.
    CM_LINE = ".cm-line"

    # ------------------------------------------------------------------
    # Landing-page chrome — left-panel storage selector + footer
    # (ELITEA-1803/1804/1805)
    # ------------------------------------------------------------------

    buckets_panel_toggle_button = LocatorDescriptor(
        testid="artifacts-buckets-panel-toggle-button",
        description="The BUCKETS left panel's collapse/expand control in the "
        "panel header (BucketHeader.jsx). ONE element whose icon flips "
        "between '<<' (expanded) and '>>' (collapsed); the icons are "
        "untagged SVGs, so the state rides a `data-collapsed=\"true|false\"` "
        "attribute on this same element per .agents/testing.md § Locator "
        "policy (PR #581 ruling). Collapsing UNMOUNTS the heading, the "
        "storage selector and the footer (all gated on `!collapsed`) while "
        "the bucket ROWS merely become invisible "
        "(`display: collapsed ? 'none' : 'flex'`). Testid added for "
        "ELITEA-1807 (EliteaAI/EliteaUI@9062dff0).",
    )

    buckets_heading = LocatorDescriptor(
        testid="artifacts-buckets-heading",
        description="'Buckets' heading in the left-panel header. The DOM text "
        "is 'Buckets' — case texts writing 'BUCKETS' describe the CSS "
        "text-transform, not the content. (The testid itself is pre-existing "
        "and already used inline by :meth:`wait_for_page_load`; this field is "
        "the class-level handle ELITEA-1803 asserts the TEXT through.)",
    )

    storage_selector = LocatorDescriptor(
        testid="artifacts-storage-selector",
        description="Storage-provider row above the bucket list "
        "(BucketStorageSelector.jsx) — reads the active storage's name, "
        "'Elitea S3 storage' on this environment. New testid added for "
        "ELITEA-1803 (EliteaAI/EliteaUI@6449a5c4).",
    )

    storage_selector_arrow = LocatorDescriptor(
        testid="artifacts-storage-selector-arrow",
        description="Dropdown (chevron) icon inside the storage-provider row "
        "— a DIFFERENT node from :attr:`storage_selector` (the row's own "
        "container). ELITEA-1803 step 3 asserts both.",
    )

    buckets_footer_count = LocatorDescriptor(
        testid="artifacts-buckets-footer-count",
        description="'Buckets: N' stat in the left-panel footer "
        "(BucketFooter.jsx). NOTE: label and value are two sibling "
        "<Typography> nodes inside this Box, so text_content() has NO space "
        "between them ('Buckets:757') — match with r'Buckets:\\s*(\\d+)'. "
        "The number is not stable across runs (leaked autotest buckets, "
        "#636) — cross-check it against "
        ":meth:`ArtifactsPage.get_rendered_bucket_names` (the panel's own "
        "DISTINCT rendered rows). An ArtifactAPI.list_buckets() cross-check "
        "was tried first and measured racy: the buckets listing is "
        "eventually consistent.",
    )

    buckets_footer_size = LocatorDescriptor(
        testid="artifacts-buckets-footer-size",
        description="'Size: X MB' stat in the left-panel footer "
        "(BucketFooter.jsx) — same two-Typography shape as "
        ":attr:`buckets_footer_count`.",
    )

    # ------------------------------------------------------------------
    # Main-panel bucket-info tooltip (ELITEA-1805)
    # ------------------------------------------------------------------

    bucket_info_button = LocatorDescriptor(
        testid="artifacts-bucket-info-button",
        description="Info (i) icon next to the bucket name in the MAIN-panel "
        "toolbar (BucketInfoTooltip.jsx via ArtifactTableToolbar.jsx). This — "
        "not the left-panel bucket name — is what reveals the Retention "
        "Policy / Number of files tooltip; the left-panel name only carries a "
        "conditional overflow tooltip repeating the name (case-text "
        "CLARIFICATION #1617). Opens on HOVER, not click (same activation as "
        "the toolkit-form field tooltip, #669).",
    )

    bucket_info_tooltip_content = LocatorDescriptor(
        testid="artifacts-bucket-info-tooltip-content",
        description="Content box of the bucket-info tooltip — renders "
        "'Retention Policy: <value>' and 'Number of files: <n>'. Labels and "
        "values are sibling <Typography> nodes, so text_content() reads "
        "'Retention Policy:1 YearNumber of files:0' (no separating "
        "whitespace).",
    )

    # ------------------------------------------------------------------
    # File-table column headers + pagination (ELITEA-1803/1804/1805)
    # ------------------------------------------------------------------

    # Dynamic testid template — one per column, keyed by the column's FIELD
    # name (not its visible label): name / fileType / size / modified /
    # actions. 'modified' is the "Last update" column — the field key is NOT
    # 'lastUpdate'. Wired via the shared GridTableHeader's pre-existing
    # `columnTestIdPrefix` prop (ArtifactTable.jsx), so no feature-scoped
    # testid is hardcoded in the shared component.
    FILE_TABLE_COLUMN_HEADER = '[data-testid="artifacts-file-table-column-header-{}"]'

    # Prefix (any-column) variant of FILE_TABLE_COLUMN_HEADER — matches every
    # rendered column header. Used to prove the file TABLE itself is absent
    # for an empty bucket (ELITEA-1805 step 7), which "no file rows" alone
    # does not.
    FILE_TABLE_COLUMN_HEADER_ANY = '[data-testid^="artifacts-file-table-column-header-"]'

    # Dynamic testid template — the "No files in this bucket" label rendered
    # in the LEFT-panel tree under an expanded, empty bucket
    # (BucketContent.jsx). Bucket-parameterized by necessity: BucketContent is
    # a SIBLING of the bucket row (BucketItem), inside an untagged wrapper, so
    # it cannot be scoped under artifacts-bucket-row-{name}; and several
    # buckets can be expanded at once (/artifacts auto-selects and expands one
    # on landing), so a page-wide count is never 0.
    BUCKET_TREE_EMPTY_LABEL = '[data-testid="artifacts-bucket-tree-empty-label-{}"]'

    pagination_page_info = LocatorDescriptor(
        testid="artifacts-pagination-page-info",
        description="'{start} - {end} of {total}' counter at the bottom of the "
        "file table (shared GridTablePagination's pageInfoTestId prop, wired "
        "from ArtifactTable.jsx). ABSENT entirely when the bucket has no files "
        "— GridTablePagination returns null at totalRows === 0.",
    )

    pagination_prev_button = LocatorDescriptor(
        testid="artifacts-pagination-prev-button",
        description="Previous-page arrow. Carries a real `disabled` attribute "
        "on the first page — assert with is_disabled(), never by CSS opacity.",
    )

    pagination_next_button = LocatorDescriptor(
        testid="artifacts-pagination-next-button",
        description="Next-page arrow. Carries a real `disabled` attribute on "
        "the last page (and on a single-page bucket).",
    )

    pagination_page_size_combobox = LocatorDescriptor(
        testid="artifacts-pagination-page-size-select-combobox",
        description="'Rows per page' select's clickable combobox — the shared "
        "SingleSelect derives this '-combobox' suffix from the root "
        "'artifacts-pagination-page-size-select' testid (same shape as "
        ":attr:`bucket_retention_measure_combobox`). Defaults to '10'.",
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

    @action("Click bucket Save button (invalid name — no request expected)")
    def click_bucket_save_button_expect_no_request(self) -> None:
        """Click Save on the 'New Bucket' form for an INVALID name — no wait on a response.

        Sibling to :meth:`click_bucket_save_button` for the invalid-name path
        (ELITEA-1811/1814): the yup schema blocks ``formik.handleSubmit``
        entirely client-side for an invalid name, so no
        ``POST .../artifacts/buckets`` ever fires. Wrapping this click in
        :meth:`click_bucket_save_button`'s ``page.expect_response`` would hang
        for its full timeout and then raise — confirmed live during AFS
        exploration. This is a plain click; callers assert the absence of the
        network call themselves (e.g. via a short-lived
        ``page.expect_response`` that is expected to time out) if that
        guarantee is part of the case.
        """
        self.bucket_save_button.click()
        logger.info("Clicked bucket Save button (invalid-name path, no response expected)")

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
    # Header "Select all" checkbox (ELITEA-1841)
    # ------------------------------------------------------------------

    @action("Click header 'Select all' checkbox")
    def click_select_all_checkbox(self, timeout: int = 10000) -> None:
        """Click the table-header 'Select all' checkbox.

        Checks/unchecks every currently visible row as a side effect of a
        SINGLE click (``ArtifactTable.jsx``'s ``handleSelectAll``) — a
        different code path from :meth:`select_file_checkbox`'s per-row
        ``onChange`` (ELITEA-1841).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.select_all_checkbox.wait_for(state="visible", timeout=timeout)
        self.select_all_checkbox.click()
        logger.info("Clicked header 'Select all' checkbox")

    def is_select_all_checkbox_checked(self, timeout: int = 10000) -> bool:
        """Return whether the header 'Select all' checkbox is fully checked.

        Same "read the `Mui-checked` CSS class off the testid-anchored MUI
        wrapping `<span>`" technique already established by
        :meth:`is_file_checkbox_checked` (ELITEA-1840) — the testid lands on
        the wrapper, not the nested ``<input>``, so ``Locator.is_checked()``
        is not usable here either.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the header checkbox currently carries ``Mui-checked``.
        """
        self.select_all_checkbox.wait_for(state="visible", timeout=timeout)
        class_attr = self.select_all_checkbox.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def is_select_all_checkbox_indeterminate(self, timeout: int = 10000) -> bool:
        """Return whether the header 'Select all' checkbox is in the indeterminate state.

        Reads the ``MuiCheckbox-indeterminate`` CSS class off the same
        testid-anchored locator as :meth:`is_select_all_checkbox_checked` —
        confirmed live (ELITEA-1841 AFS, via an exploratory partial-deselect)
        that MUI adds this class only for a PARTIAL selection, distinct from
        both the fully-checked and fully-unchecked states — a real 3-state
        signal, not a cosmetic no-op.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the header checkbox currently carries
            ``MuiCheckbox-indeterminate``.
        """
        self.select_all_checkbox.wait_for(state="visible", timeout=timeout)
        class_attr = self.select_all_checkbox.get_attribute("class") or ""
        return "MuiCheckbox-indeterminate" in class_attr

    def get_download_button_tooltip_text(self, timeout: int = 10000) -> str:
        """Return the toolbar 'Download files' button's tooltip text.

        Reads the STATIC ``aria-label`` MUI's Tooltip clones onto
        :attr:`download_files_tooltip`'s wrapping element (ELITEA-1841) — a
        DIFFERENT DOM node from :attr:`download_files_button` (that testid
        resolves to the inner ``<button>``, which carries no aria-label of
        its own; confirmed live). Same no-hover-required technique already
        established by :meth:`get_delete_button_tooltip_text`. Unlike the
        delete button's tooltip (which varies with selection completeness),
        this text is invariant — always ``"Download files"`` regardless of
        partial vs. full selection (ELITEA-1841 case step 7).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The tooltip text, e.g. ``"Download files"``.
        """
        self.download_files_tooltip.wait_for(state="visible", timeout=timeout)
        return self.download_files_tooltip.get_attribute("aria-label") or ""

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

    def get_upload_path_description_text(self, timeout: int = 10000) -> str:
        """Return the upload dialog's description line text (ELITEA-1835).

        Mirrors :meth:`get_upload_path_normalized_prefix`'s shape but reads a
        DIFFERENT, simpler element: :attr:`upload_path_description_text` (a
        plain ``<Typography>``) has no adjacent read-only adornment polluting
        its ``text_content()`` the way the Path field's wrapper does, so no
        label-stripping is needed here — the raw stripped text IS the full
        description string.

        Args:
            timeout: Maximum wait time in milliseconds for the element to be
                visible before reading its text.

        Returns:
            The description line's stripped text content — a GENERIC,
            bucket-name-free string at bucket root, or a bucket-naming
            string once a subfolder is the active upload target (see
            ``UploadPathDialog.jsx``'s ``descriptionMessage``).
        """
        self.upload_path_description_text.wait_for(state="visible", timeout=timeout)
        return (self.upload_path_description_text.text_content() or "").strip()

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

    @action("Skip duplicate resolution (uploads only the non-duplicate file(s))")
    def click_resolve_duplicates_skip_button(self) -> None:
        """Click 'Skip' in the 'Resolve duplicates' dialog.

        Uploads only the non-duplicate file(s) selected in the same batch —
        confirmed live (ELITEA-1829): fires exactly one PUT per non-duplicate
        file and none for the duplicate, leaving the duplicate's content and
        metadata (including its 'lastModified' timestamp) untouched.
        """
        self.resolve_duplicates_skip_button.click()

    @action("Keep both duplicate resolution (uploads the new file under a renamed key)")
    def click_resolve_duplicates_keep_both_button(self) -> None:
        """Click 'Keep both' in the 'Resolve duplicates' dialog.

        Uploads the new file under a renamed key,
        ``{baseName} - Copy{extension}`` (confirmed live, ELITEA-1831 —
        space, hyphen, space, capitalized "Copy", original extension
        preserved). Fires exactly one PUT for the renamed key; the original
        duplicate's path is never re-touched.
        """
        self.resolve_duplicates_keep_both_button.click()

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
    # Bucket permissions management
    # ------------------------------------------------------------------

    # Dynamic testid templates for bucket row and menu button
    BUCKET_ROW_TESTID = '[data-testid="artifacts-bucket-row-{}"]'
    BUCKET_MENU_BUTTON_TESTID = '[data-testid="bucket-menu-{}-menu-button"]'

    @action("Open Manage Permissions modal")
    def open_manage_permissions(self, bucket_name: str, timeout: int = 10000) -> None:
        """Open the Manage Permissions modal for a bucket via its DotMenu.

        LOCATOR: The bucket row has testid 'artifacts-bucket-row-{name}'.
        The menu button appears on hover with testid 'bucket-menu-{name}-menu-button'.

        Args:
            bucket_name: Name of the bucket to manage permissions for.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening Manage Permissions for bucket '%s'", bucket_name)

        # Find the bucket row by testid
        bucket_row = self.page.locator(self.BUCKET_ROW_TESTID.format(bucket_name))
        bucket_row.wait_for(state="attached", timeout=timeout)

        # Scroll into view and hover to reveal DotMenu
        bucket_row.scroll_into_view_if_needed()
        bucket_row.hover()
        self.page.wait_for_timeout(500)

        # Click the DotMenu button (appears on hover)
        menu_btn = self.page.locator(self.BUCKET_MENU_BUTTON_TESTID.format(bucket_name))
        menu_btn.wait_for(state="visible", timeout=timeout)
        menu_btn.click(force=True)
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
        modal.wait_for(state="visible", timeout=timeout)

        # Wait for modal content to fully render
        self.page.wait_for_timeout(1000)

        # Two button variants depending on whether exceptions exist:
        # 1. Empty list: "Add Exceptions" button (MuiButton-special with startIcon)
        # 2. Has exceptions: + button with aria-label="Add exception"
        add_exceptions_btn = modal.locator('button:has-text("Add Exceptions")')
        add_exception_btn = modal.locator('button[aria-label="Add exception"]')

        if add_exceptions_btn.count() > 0:
            add_exceptions_btn.first.scroll_into_view_if_needed()
            self.page.wait_for_timeout(300)
            add_exceptions_btn.first.click(force=True)
        elif add_exception_btn.count() > 0:
            add_exception_btn.first.scroll_into_view_if_needed()
            self.page.wait_for_timeout(300)
            add_exception_btn.first.click(force=True)
        else:
            raise Exception("Could not find Add Exceptions or Add exception button")

        self.page.wait_for_timeout(500)

        # Wait for Add exceptions dialog
        # Use exact text match for heading to distinguish from parent modal's button
        add_dialog = self.page.locator('[role="dialog"]').filter(
            has=self.page.locator('span:text-is("Add exceptions")')
        )
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

        # Click on dialog header to close user dropdown before opening Permissions
        dialog_header = add_dialog.locator('h2').first
        dialog_header.click()
        self.page.wait_for_timeout(300)

        # Click on Permissions dropdown to open it
        # The combobox has id="simple-select-Permissions"
        permissions_dropdown = add_dialog.locator('#simple-select-Permissions')
        permissions_dropdown.click()
        self.page.wait_for_timeout(300)

        # Map permission display names to testid values
        # Options: select-option-read ("Read-only"), select-option-no_access ("No access"),
        #          select-option-read_write ("Read/write (default)")
        permission_testid_map = {
            "Read-only": "select-option-read",
            "No access": "select-option-no_access",
            "Read/write (default)": "select-option-read_write",
        }
        testid = permission_testid_map.get(permission)
        if not testid:
            raise ValueError(f"Unknown permission '{permission}'. Valid: {list(permission_testid_map.keys())}")

        # Select permission option by testid
        perm_option = self.page.locator(f'[data-testid="{testid}"]')
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
        """Remove a user exception by setting their permission to Read/write (default).

        The modal must already be open (call open_manage_permissions first).
        This effectively restores the user to default permissions.

        Flow:
        1. Find the user row and click Edit exception (pencil icon)
        2. In the edit dialog, select "Read/write (default)" permission
        3. Click Save

        Args:
            user_name_or_email: User's name or email to restore to default.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Restoring default permission for user=%s", user_name_or_email)

        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')
        modal.wait_for(state="visible", timeout=timeout)

        # Find the user row in exceptions table
        user_row = modal.locator(f'tr:has-text("{user_name_or_email}")').first
        if user_row.count() == 0:
            user_row = modal.locator(f'div:has-text("{user_name_or_email}")').first

        user_row.wait_for(state="visible", timeout=timeout)

        # Click Edit exception button (pencil icon with aria-label="Edit exception")
        edit_btn = user_row.locator('button').filter(
            has=self.page.locator('svg')
        ).first
        # Or find by parent span with aria-label
        edit_wrapper = user_row.locator('[aria-label="Edit exception"] button').first
        if edit_wrapper.count() > 0:
            edit_wrapper.click()
        else:
            edit_btn.click()
        self.page.wait_for_timeout(500)

        # Wait for Edit exception dialog
        edit_dialog = self.page.locator('[role="dialog"]').filter(
            has=self.page.locator('span:text-is("Edit exception")')
        )
        edit_dialog.wait_for(state="visible", timeout=timeout)

        # Click on Permissions dropdown
        permissions_dropdown = edit_dialog.locator('#simple-select-Permissions')
        permissions_dropdown.click()
        self.page.wait_for_timeout(300)

        # Select "Read/write (default)" option by testid
        read_write_option = self.page.locator('[data-testid="select-option-read_write"]')
        read_write_option.wait_for(state="visible", timeout=timeout)
        read_write_option.click()
        self.page.wait_for_timeout(300)

        # Click Save button
        save_btn = edit_dialog.get_by_role("button", name="Save")
        save_btn.click()

        # Wait for dialog to close
        edit_dialog.wait_for(state="hidden", timeout=timeout)
        self.page.wait_for_timeout(500)
        logger.info("Restored default permission for '%s'", user_name_or_email)

    def user_has_exception(self, user_name_or_email: str) -> bool:
        """Check if user already has an exception in the open Manage Permissions modal."""
        modal = self.page.locator('[role="dialog"]:has-text("Manage Permissions")')
        user_row = modal.locator(f':text("{user_name_or_email}")')
        return user_row.count() > 0

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

    # ------------------------------------------------------------------
    # File preview/edit editor panel (ELITEA-1851/1852/1856)
    # ------------------------------------------------------------------

    def get_file_row(self, filename: str) -> Locator:
        """Return a locator for a single file row, filtered by displayed name.

        Built from the class-level :attr:`ARTIFACT_FILE_ROW` testid constant
        rather than an inline ``page.get_by_test_id(...)`` call, so the
        selector stays a page-object field per
        `.claude/rules/page-objects.md` (dynamic-identity pattern — the
        testid itself is static, filename filtering supplies the identity,
        same shape as :meth:`get_skill_card_by_id` in `agent_detail_page.py`).
        Callers needing hover/click use this method or one of the existing
        higher-level helpers; test/spec files never build this locator
        themselves.

        Args:
            filename: Exact file name to match via ``.filter(has_text=...)``.

        Returns:
            Locator scoped to the first matching row.
        """
        return self.page.locator(self.ARTIFACT_FILE_ROW).filter(has_text=filename).first

    @action("Hover file row")
    def hover_file_row(self, filename: str, timeout: int = 10000) -> None:
        """Hover a file row (scrolling it into view first).

        NOTE: the "View/Edit file" preview icon is visible on the row
        unconditionally — it is NOT hover-gated (confirmed against
        ``ArtifactRowActions.jsx``: the Preview ``IconButton`` renders
        whenever ``row.canPreview`` is true, with no opacity/visibility/
        display CSS tied to a hover state; only a background-color hover
        highlight applies to the button itself. Same "always visible, not
        hover-gated" pattern as case-text-drift clarification
        EliteaAI/elitea-testing-public#994). This method still exists
        because some flows scroll-then-click through it; it is not a
        precondition for the preview icon to appear.

        Args:
            filename: Exact file name whose row to hover.
            timeout: Maximum wait time in milliseconds.
        """
        file_row = self.get_file_row(filename)
        file_row.wait_for(state="visible", timeout=timeout)
        file_row.scroll_into_view_if_needed()
        file_row.hover()

    def is_file_preview_button_visible(self, filename: str, timeout: int = 5000) -> bool:
        """Return whether the 'View/Edit file' icon is visible for *filename*'s row.

        Safe to call with or without a prior :meth:`hover_file_row` — the
        icon is visible unconditionally, not hover-gated (see
        :meth:`hover_file_row`'s docstring / EliteaAI/elitea-testing-public#994).

        Args:
            filename: Exact file name (matches the dynamic
                ``artifacts-file-preview-button-{filename}`` testid).
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if visible within *timeout*, False otherwise.
        """
        trigger = self.page.locator(self.ARTIFACT_FILE_PREVIEW_BUTTON.format(filename))
        try:
            trigger.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Open file in preview/edit editor")
    def open_file_in_editor(self, filename: str, timeout: int = 10000) -> None:
        """Hover the file row and click its 'View/Edit file' icon to open the editor.

        Shared open-flow helper for ELITEA-1851/1852/1856 (AFS Automation
        Hints — factored once rather than duplicated per spec).

        Args:
            filename: Exact file name whose row to open (matches the
                dynamic ``artifacts-file-preview-button-{filename}`` testid).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening '%s' in the preview/edit editor", filename)
        self.hover_file_row(filename, timeout=timeout)

        trigger = self.page.locator(self.ARTIFACT_FILE_PREVIEW_BUTTON.format(filename))
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()

        # The editor is "open" once its Save button renders — present
        # (though disabled pre-edit) as soon as canPreview is true.
        self.file_preview_save_button.wait_for(state="visible", timeout=timeout)
        # Also wait for the file's CONTENT to have actually loaded — the
        # editor panel's 'Copy Content' menu item is conditionally rendered
        # on `fileContent` being truthy (PreviewHeader.jsx's `menuItems`
        # `show` clause), which can still be fetching when the Save button
        # first renders (separate loading state). Waiting here (once, in the
        # shared open-flow) avoids every caller needing its own race guard
        # before opening the 3-dot menu.
        #
        # Exactly ONE of three mutually-exclusive content surfaces renders,
        # depending on file type/render-mode: CodeMirror content (code
        # files, or a markdown/html/mdx file switched to Raw mode),
        # the rendered Markdown wrapper (a markdown/html/mdx file's default
        # Preview mode, ELITEA-1857), or the <img> element (image files,
        # ELITEA-1862 — which never render CodeMirror or the mode toggle at
        # all). Waiting on whichever one actually applies (extended
        # ELITEA-1857/1858/1862; the CodeMirror-only wait was the original
        # ELITEA-1851/1852/1856 shape) keeps this shared open-flow helper
        # correct for every file type the suite exercises, without every
        # caller needing its own type-specific race guard.
        content_ready = self.file_preview_code_content.or_(self.file_preview_image).or_(
            self.file_preview_markdown_content
        )
        content_ready.wait_for(state="visible", timeout=timeout)
        logger.info("Editor open for '%s'", filename)

    @action("Close file preview editor")
    def close_file_preview(self, timeout: int = 10000) -> None:
        """Click the X (close) icon to close the editor panel.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_close_button.click()
        self.file_preview_close_button.wait_for(state="hidden", timeout=timeout)
        logger.info("Editor closed")

    def get_file_preview_path_text(self, timeout: int = 10000) -> str:
        """Return the editor panel header's full file-path text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The stripped text of :attr:`file_preview_file_path`
            (e.g. ``"autotest-bucket-123/machine_learning.py"``).
        """
        self.file_preview_file_path.wait_for(state="visible", timeout=timeout)
        return (self.file_preview_file_path.text_content() or "").strip()

    def get_file_preview_language_text(self, timeout: int = 10000) -> str:
        """Return the editor panel's language-label text (e.g. 'Python (detected)').

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The stripped text of :attr:`file_preview_language_select`.
        """
        self.file_preview_language_select.wait_for(state="visible", timeout=timeout)
        return (self.file_preview_language_select.text_content() or "").strip()

    def is_code_editor_line_numbers_visible(self, timeout: int = 10000) -> bool:
        """Return whether CodeMirror's line-number gutter is visible.

        LOCATOR: ``.cm-lineNumbers`` is CodeMirror-internal render DOM —
        sanctioned #579 exception (third-party editor library internal
        render node), scoped under the testid'd :attr:`file_preview_code_editor`
        parent per policy; never used as a free-floating page-level selector.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the gutter is visible within *timeout*, False otherwise.
        """
        gutter = self.file_preview_code_editor.locator(self.CM_LINE_NUMBERS)
        try:
            gutter.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_file_preview_save_enabled(self, timeout: int = 10000) -> bool:
        """Return whether the editor panel's Save button becomes enabled.

        Polls via Playwright's auto-retrying ``expect(...).to_be_enabled()``
        (not a single synchronous read) — React's ``hasUnsavedChanges`` state
        update lags the CodeMirror keystroke by a frame or two, so a bare
        ``is_enabled()`` taken immediately after typing can observe the
        pre-update (disabled) state. Use this AFTER an edit, to confirm the
        disabled -> enabled transition; for the pre-edit disabled check, use
        :meth:`is_file_preview_save_disabled` instead (resolves immediately
        rather than polling the full *timeout* for a transition that never
        happens).

        Args:
            timeout: Maximum wait time in milliseconds for the button to
                become enabled.

        Returns:
            True if Save became enabled within *timeout*, False otherwise.
        """
        try:
            expect(self.file_preview_save_button).to_be_enabled(timeout=timeout)
            return True
        except AssertionError:
            return False

    def is_file_preview_save_disabled(self, timeout: int = 5000) -> bool:
        """Return whether the editor panel's Save button is (still) disabled.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if Save is disabled within *timeout*, False otherwise.
        """
        try:
            expect(self.file_preview_save_button).to_be_disabled(timeout=timeout)
            return True
        except AssertionError:
            return False

    def is_file_preview_discard_enabled(self, timeout: int = 10000) -> bool:
        """Return whether the editor panel's Discard button becomes enabled.

        Same auto-retrying-poll rationale as :meth:`is_file_preview_save_enabled`.

        Args:
            timeout: Maximum wait time in milliseconds for the button to
                become enabled.

        Returns:
            True if Discard became enabled within *timeout*, False otherwise.
        """
        try:
            expect(self.file_preview_discard_button).to_be_enabled(timeout=timeout)
            return True
        except AssertionError:
            return False

    def is_file_preview_discard_disabled(self, timeout: int = 5000) -> bool:
        """Return whether the editor panel's Discard button is (still) disabled.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if Discard is disabled within *timeout*, False otherwise.
        """
        try:
            expect(self.file_preview_discard_button).to_be_disabled(timeout=timeout)
            return True
        except AssertionError:
            return False

    @action("Edit file preview content")
    def edit_file_preview_content(
        self, text: str, line_index: int = 0, timeout: int = 10000
    ) -> None:
        """Click into the CodeMirror content, navigate to a line, and append *text*.

        Keyboard-nav only (``Control+Home`` -> ``ArrowDown`` * N -> ``End`` ->
        type) — no character-offset math, per the AFS's "known, non-empty
        line" guidance (exact "line 17" from the case is flavor, not a fixed
        requirement). ``line_index=0`` (the default) targets the first
        content line for wait-free targeting.

        Args:
            text: Text to type at the end of the target line.
            line_index: 0-based line to target (default: first line).
            timeout: Maximum wait time in milliseconds for the editor to be ready.
        """
        editor = self.file_preview_code_content
        editor.wait_for(state="visible", timeout=timeout)
        editor.click()
        self.page.keyboard.press("Control+Home")
        for _ in range(line_index):
            self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("End")
        self.page.keyboard.type(text)
        logger.info("Typed %r at line %d in the preview editor", text, line_index)

    def get_file_preview_content_text(self, timeout: int = 10000) -> str:
        """Return the CodeMirror editable content's current text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The stripped text content of :attr:`file_preview_code_content`.
        """
        self.file_preview_code_content.wait_for(state="visible", timeout=timeout)
        return (self.file_preview_code_content.text_content() or "").strip()

    @action("Save file preview changes")
    def click_file_preview_save(self, timeout: int = 15000) -> None:
        """Click Save and wait for the ``createArtifact`` POST to resolve.

        Waits on the network response (not a fixed sleep), per
        ``.agents/testing.md``'s no-sleep rule. The RTK Query
        ``createArtifact`` mutation POSTs to
        ``/artifacts/artifacts/default/{project}/{bucket}`` (confirmed live
        via EliteaUI's ``src/api/artifacts.js``).

        Args:
            timeout: Maximum wait time in milliseconds for the response.
        """
        with self.page.expect_response(
            lambda r: "/artifacts/artifacts/default/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ):
            self.file_preview_save_button.click()
        logger.info("Save clicked, createArtifact response received")

    @action("Open editor panel actions menu")
    def open_file_preview_actions_menu(self, timeout: int = 10000) -> None:
        """Click the 3-dot menu trigger to open the editor panel's actions dropdown.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_overflow_menu_button.wait_for(state="visible", timeout=timeout)
        self.file_preview_overflow_menu_button.click()
        self.file_preview_overflow_menu_container.wait_for(state="visible", timeout=timeout)
        logger.info("Editor panel actions menu open")

    def get_file_preview_menu_item_labels(self, timeout: int = 10000) -> list[str]:
        """Return the editor panel's open dropdown's item labels, in DOM order.

        Scoped to :attr:`file_preview_overflow_menu_container` via
        :attr:`EDITOR_MENU_ITEM_SELECTOR` (a data-testid-suffix selector,
        not a raw CSS class) — reads all three per-item testid'd
        ``MenuItem``s in render order.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            List of the dropdown's visible label strings, in DOM order.
        """
        items = self.file_preview_overflow_menu_container.locator(self.EDITOR_MENU_ITEM_SELECTOR)
        items.first.wait_for(state="visible", timeout=timeout)
        count = items.count()
        labels = [(items.nth(i).text_content() or "").strip() for i in range(count)]
        logger.info("Editor panel actions menu items (in order): %s", labels)
        return labels

    @action("Click 'Copy Content' in editor panel menu")
    def click_file_preview_copy_content(self, timeout: int = 10000) -> None:
        """Click the open dropdown's 'Copy Content' item.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_copy_content_menuitem.wait_for(state="visible", timeout=timeout)
        self.file_preview_copy_content_menuitem.click()
        logger.info("'Copy Content' clicked")

    @action("Click 'Download' in editor panel menu")
    def click_file_preview_download(self, timeout: int = 10000) -> Download:
        """Click the open dropdown's 'Download' item and capture the download.

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object.
        """
        self.file_preview_download_menuitem.wait_for(state="visible", timeout=timeout)
        with self.page.expect_download(timeout=timeout) as download_info:
            self.file_preview_download_menuitem.click()
        download = download_info.value
        logger.info(
            "Download started from editor panel menu → suggested filename: %s",
            download.suggested_filename,
        )
        return download

    @action("Click 'Delete' in editor panel menu")
    def click_file_preview_delete(self, timeout: int = 10000) -> None:
        """Click the open dropdown's 'Delete' item, opening the confirm modal.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_delete_menuitem.wait_for(state="visible", timeout=timeout)
        self.file_preview_delete_menuitem.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Delete-confirmation modal opened from editor panel menu")

    @action("Confirm delete from editor panel")
    def confirm_file_preview_delete(self, timeout: int = 15000) -> None:
        """Click 'Delete' inside the confirmation modal and wait for the
        ``deleteArtifact`` DELETE request to resolve.

        Args:
            timeout: Maximum wait time in milliseconds for the response.
        """
        with self.page.expect_response(
            lambda r: "/artifacts/artifact/default/" in r.url and r.request.method == "DELETE",
            timeout=timeout,
        ):
            self.delete_confirm_button.click()
        logger.info("Delete confirmed, deleteArtifact response received")

    # ------------------------------------------------------------------
    # File preview/edit — markdown mode toggle + image preview
    # (ELITEA-1857/1858/1862)
    # ------------------------------------------------------------------

    def get_file_preview_mode_toggle_state(self, timeout: int = 10000) -> dict[str, str]:
        """Return the render-mode toggle's ``aria-pressed`` state for both buttons.

        Args:
            timeout: Maximum wait time in milliseconds for the toggle group
                to become visible.

        Returns:
            Dict ``{"rendered": "true"|"false", "code": "true"|"false"}``.
        """
        self.file_preview_mode_toggle_group.wait_for(state="visible", timeout=timeout)
        return {
            "rendered": self.file_preview_mode_toggle_rendered.get_attribute("aria-pressed") or "false",
            "code": self.file_preview_mode_toggle_code.get_attribute("aria-pressed") or "false",
        }

    @action("Switch render mode to Raw")
    def click_file_preview_mode_toggle_code(self, timeout: int = 10000) -> None:
        """Click the 'Raw' (code) mode toggle button and wait for it to become pressed.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_mode_toggle_code.click()
        expect(self.file_preview_mode_toggle_code).to_have_attribute(
            "aria-pressed", "true", timeout=timeout
        )
        logger.info("Render mode switched to Raw (code)")

    @action("Switch render mode to Preview")
    def click_file_preview_mode_toggle_rendered(self, timeout: int = 10000) -> None:
        """Click the 'Preview'/'Rendered' mode toggle button and wait for it to become pressed.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_mode_toggle_rendered.click()
        expect(self.file_preview_mode_toggle_rendered).to_have_attribute(
            "aria-pressed", "true", timeout=timeout
        )
        logger.info("Render mode switched to Preview (rendered)")

    def get_file_preview_markdown_content_text(self, timeout: int = 10000) -> str:
        """Return the rendered Markdown content wrapper's visible text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The stripped text of :attr:`file_preview_markdown_content`.
        """
        self.file_preview_markdown_content.wait_for(state="visible", timeout=timeout)
        return (self.file_preview_markdown_content.text_content() or "").strip()

    def get_file_preview_markdown_content_html(self, timeout: int = 10000) -> str:
        """Return the rendered Markdown content wrapper's inner HTML.

        Confirms actual rendered Markdown STRUCTURE (heading/bold/bullet
        elements), not raw hash/asterisk syntax — per the AFS's Concrete
        Handles guidance: ``.inner_html()`` scoped under the existing
        testid'd wrapper, not a new raw tag selector.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The inner HTML of :attr:`file_preview_markdown_content`.
        """
        self.file_preview_markdown_content.wait_for(state="visible", timeout=timeout)
        return self.file_preview_markdown_content.inner_html()

    @action("Attempt to type into the rendered Markdown preview")
    def attempt_type_in_markdown_preview(self, text: str, timeout: int = 10000) -> None:
        """Click the rendered Markdown content area and attempt to type *text*.

        The Markdown branch mounts a static ``<Markdown>`` render, not an
        editable CodeMirror instance — this method exists to PROVE no input
        is accepted (AFS ELITEA-1857 step 9), not to actually edit anything.
        Callers verify via ``page.content()`` (not a new locator) that
        *text* never appears anywhere on the page afterward.

        Args:
            text: Marker text to attempt typing.
            timeout: Maximum wait time in milliseconds.
        """
        self.file_preview_markdown_content.wait_for(state="visible", timeout=timeout)
        self.file_preview_markdown_content.click()
        self.page.keyboard.type(text)
        logger.info("Attempted to type %r into the Markdown preview (should have no effect)", text)

    def is_file_preview_image_visible(self, timeout: int = 20000) -> bool:
        """Return whether the rendered ``<img>`` preview becomes visible.

        A generous, condition-based wait — the image blob fetch can exceed
        ``networkidle`` timing on a busy shared DEV backend (AFS ELITEA-1862
        Axis 2 finding); never replace this with a fixed sleep.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if the image became visible within *timeout*, False otherwise.
        """
        try:
            expect(self.file_preview_image).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    @action("Edit a specific CodeMirror line by matching text")
    def edit_file_preview_line_containing(
        self, match_text: str, append_text: str, timeout: int = 10000
    ) -> None:
        """Click the specific ``.cm-line`` containing *match_text* and append
        *append_text* at its end.

        AFS-mandated targeting technique (ELITEA-1858) — filters
        ``.cm-line`` by exact target text rather than reusing
        :meth:`edit_file_preview_content`'s ``Control+Home``-based nav.
        Live-testing showed ``Control+Home`` does not reliably reach true
        document start in this CodeMirror instance (a plain click lands
        wherever the pointer's bounding-box center falls, and
        ``Control+Home`` failed to correct it) — filtering by exact line
        content is deterministic regardless of scroll position or click-
        target ambiguity. Use this for a SPECIFIC known line (e.g. a
        heading); :meth:`edit_file_preview_content` remains correct for
        "any known content line" callers (ELITEA-1852).

        LOCATOR: ``.cm-line`` is CodeMirror-internal render DOM — sanctioned
        #579 exception (third-party editor library internal render node),
        scoped under the testid'd :attr:`file_preview_code_content` parent
        (whose ``.cm-content`` node is these lines' direct parent).

        Args:
            match_text: Exact text of the target line to filter by.
            append_text: Text to append at the end of that line.
            timeout: Maximum wait time in milliseconds.
        """
        target_line = self.file_preview_code_content.locator(self.CM_LINE).filter(
            has_text=match_text
        ).first
        target_line.wait_for(state="visible", timeout=timeout)
        target_line.click()
        self.page.keyboard.press("End")
        self.page.keyboard.type(append_text)
        logger.info("Appended %r to the CodeMirror line containing %r", append_text, match_text)

    # ------------------------------------------------------------------
    # Landing-page chrome / pagination readers (ELITEA-1803/1804/1805)
    # ------------------------------------------------------------------

    def get_buckets_footer_count_text(self, timeout: int = 10000) -> str:
        """Return the left-panel footer's 'Buckets: N' text.

        Args:
            timeout: How long to wait for the footer stat.

        Returns:
            Raw text content, e.g. ``"Buckets:757"`` (no separating space —
            label and value are sibling Typography nodes).
        """
        self.buckets_footer_count.wait_for(state="visible", timeout=timeout)
        return (self.buckets_footer_count.text_content() or "").strip()

    def get_buckets_footer_size_text(self, timeout: int = 10000) -> str:
        """Return the left-panel footer's 'Size: X' text.

        Args:
            timeout: How long to wait for the footer stat.

        Returns:
            Raw text content, e.g. ``"Size:254.8 MB"``.
        """
        self.buckets_footer_size.wait_for(state="visible", timeout=timeout)
        return (self.buckets_footer_size.text_content() or "").strip()

    def column_header(self, field: str) -> Locator:
        """Return the file-table column header for *field*.

        Args:
            field: Column FIELD name — ``name``, ``fileType``, ``size``,
                ``modified`` (the "Last update" column) or ``actions``.

        Returns:
            Locator for that column's header cell.
        """
        return self.page.locator(self.FILE_TABLE_COLUMN_HEADER.format(field))

    def get_column_header_count(self) -> int:
        """Return how many file-table column headers are rendered.

        Zero means the file TABLE itself is not rendered (empty bucket), which
        is a stronger statement than "no file rows".

        Returns:
            Number of rendered column headers.
        """
        return self.page.locator(self.FILE_TABLE_COLUMN_HEADER_ANY).count()

    def bucket_tree_empty_label(self, bucket_name: str) -> Locator:
        """Return the left-tree "No files in this bucket" label for *bucket_name*.

        Args:
            bucket_name: Name of the bucket whose subtree is inspected.

        Returns:
            Locator for that bucket's own empty-tree label.
        """
        return self.page.locator(self.BUCKET_TREE_EMPTY_LABEL.format(bucket_name))

    def get_pagination_info_text(self, timeout: int = 10000) -> str:
        """Return the pagination counter text (e.g. ``"1 - 10 of 12"``).

        Args:
            timeout: How long to wait for the counter.

        Returns:
            Trimmed counter text.
        """
        self.pagination_page_info.wait_for(state="visible", timeout=timeout)
        return (self.pagination_page_info.text_content() or "").strip()

    def get_rows_per_page_value(self, timeout: int = 10000) -> str:
        """Return the current 'Rows per page' value (e.g. ``"10"``).

        Args:
            timeout: How long to wait for the combobox.

        Returns:
            Trimmed combobox text.
        """
        self.pagination_page_size_combobox.wait_for(state="visible", timeout=timeout)
        return (self.pagination_page_size_combobox.text_content() or "").strip()

    def any_bucket_row(self) -> Locator:
        """Return the first currently-rendered bucket row (any bucket).

        Uses the shared testid PREFIX (:attr:`BUCKET_ROW_ANY_SELECTOR`) — the
        caller cares only that the left panel is rendering a bucket list, not
        which bucket. Visibility, not count, is the meaningful check for a
        collapsed panel: the rows stay in the DOM behind ``display: none``
        (ELITEA-1807).

        Returns:
            Locator for the first matching bucket row.
        """
        return self.page.locator(self.BUCKET_ROW_ANY_SELECTOR).first

    def is_buckets_panel_collapsed(self) -> bool:
        """Return whether the BUCKETS left panel is currently collapsed.

        Reads the ``data-collapsed`` state attribute off
        :attr:`buckets_panel_toggle_button`, which the product renders from
        the same ``collapsed`` value that chooses the ``<<``/``>>`` icon.

        Returns:
            ``True`` when the panel is collapsed.
        """
        return self.buckets_panel_toggle_button.get_attribute("data-collapsed") == "true"

    @action("Toggle BUCKETS panel")
    def toggle_buckets_panel(self, timeout: int = 10000) -> bool:
        """Click the BUCKETS panel collapse/expand control and wait for the flip.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The panel's collapsed state AFTER the toggle.
        """
        toggle = self.buckets_panel_toggle_button
        toggle.wait_for(state="visible", timeout=timeout)
        expected = "false" if self.is_buckets_panel_collapsed() else "true"
        toggle.click()
        # Condition wait on the product's own state attribute — never a sleep.
        expect(toggle).to_have_attribute("data-collapsed", expected, timeout=timeout)
        logger.info("Toggled BUCKETS panel: collapsed=%s", expected)
        return expected == "true"

    @action("Go to next file page")
    def click_pagination_next(self, timeout: int = 10000) -> None:
        """Click the next-page arrow and wait for the table to re-render.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.pagination_next_button.wait_for(state="visible", timeout=timeout)
        self.pagination_next_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked pagination next")

    @action("Go to previous file page")
    def click_pagination_prev(self, timeout: int = 10000) -> None:
        """Click the previous-page arrow and wait for the table to re-render.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.pagination_prev_button.wait_for(state="visible", timeout=timeout)
        self.pagination_prev_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked pagination prev")

    @action("Hover bucket info icon")
    def hover_bucket_info_icon(self, timeout: int = 10000) -> None:
        """Hover the main-panel bucket-info (i) icon to reveal its tooltip.

        The tooltip opens on HOVER, not click (CLARIFICATION #1617 / #669).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.bucket_info_button.wait_for(state="visible", timeout=timeout)
        self.bucket_info_button.hover()
        self.bucket_info_tooltip_content.wait_for(state="visible", timeout=timeout)
        logger.info("Bucket-info tooltip opened")

    def get_bucket_info_tooltip_text(self, timeout: int = 10000) -> str:
        """Return the bucket-info tooltip's text content.

        Args:
            timeout: How long to wait for the tooltip content.

        Returns:
            e.g. ``"Retention Policy:1 YearNumber of files:0"`` — labels and
            values are sibling Typography nodes, so there is no separating
            whitespace.
        """
        self.bucket_info_tooltip_content.wait_for(state="visible", timeout=timeout)
        return (self.bucket_info_tooltip_content.text_content() or "").strip()

    def get_rendered_bucket_names(self) -> list[str]:
        """Return the distinct bucket names currently rendered in the left panel.

        Reads each row's own ``artifacts-bucket-row-{name}`` testid and
        de-duplicates: a PINNED bucket is rendered twice by
        ``BucketsListContent.jsx`` (once in the pinned list, once in the full
        list), so a raw row count would over-count it.

        This is the oracle ELITEA-1803/1805 use for the left-panel footer's
        "Buckets: N" stat — ``BucketsPanel.jsx`` feeds the footer
        ``bucketCount={buckets?.length}``, the same array the list renders, so
        footer and list must agree within one snapshot. (An API cross-check
        was tried first and proved racy: the buckets listing is eventually
        consistent — measured 760 rendered against 762 from
        ``GET /artifacts/buckets/default/{project}`` seconds after creating
        buckets.)

        Read-only DOM observation: ``evaluate_all`` here only READS each
        node's own ``data-testid``; it injects nothing and mutates nothing, so
        it is not a substitution under the fidelity policy. It is used instead
        of N per-element round-trips because the panel renders 750+ rows.

        Returns:
            De-duplicated bucket names, in render order.
        """
        prefix = "artifacts-bucket-row-"
        names: list[str] = []
        for testid in self.page.locator(self.BUCKET_ROW_ANY_SELECTOR).evaluate_all(
            "nodes => nodes.map(n => n.getAttribute('data-testid'))"
        ):
            if testid and testid.startswith(prefix):
                name = testid[len(prefix):]
                if name not in names:
                    names.append(name)
        return names

    def file_rows(self) -> Locator:
        """Return a locator for every rendered file/folder row.

        Public accessor over the pre-existing :meth:`_file_rows` so specs
        assert row counts through the page object (``expect(...)``'s
        auto-retry) instead of constructing locators themselves.

        Returns:
            Locator for the file/folder row collection.
        """
        return self._file_rows()

    def file_row_checkboxes(self) -> Locator:
        """Return a locator for every rendered file-row selection checkbox.

        Returns:
            Locator matching :attr:`ARTIFACT_FILE_CHECKBOX_ANY_SELECTOR`.
        """
        return self.page.locator(self.ARTIFACT_FILE_CHECKBOX_ANY_SELECTOR)

    def file_row_action_buttons(self) -> Locator:
        """Return a locator for every rendered file-row actions (dot-menu) trigger.

        Returns:
            Locator matching :attr:`ARTIFACT_ACTIONS_MENU_BUTTON_ANY_SELECTOR`.
        """
        return self.page.locator(self.ARTIFACT_ACTIONS_MENU_BUTTON_ANY_SELECTOR)

    def tree_item(self, item_key: str) -> Locator:
        """Return the left-panel tree node for *item_key*.

        Locator-returning sibling of the pre-existing
        :meth:`is_tree_item_visible` / :meth:`click_tree_item`, for specs that
        want ``expect(...)``'s auto-retrying assertions on the node.

        Args:
            item_key: Full relative path of the file/folder (e.g.
                ``"sample.txt"`` or ``"a1/sample.txt"``).

        Returns:
            Locator for that tree node.
        """
        return self.page.locator(self.ARTIFACTS_TREE_ITEM.format(item_key))
