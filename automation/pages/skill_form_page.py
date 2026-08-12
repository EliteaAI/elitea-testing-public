"""Skill Form Page - Create and edit skill forms.

Handles: /skills/create and /skills/all/{id} (edit mode)
- Fill in skill details (name, description, instructions)
- Save/cancel operations
- Form validation
"""

import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action


logger = logging.getLogger("elitea.pages.skill_form")


class SkillFormPage(BasePage):
    """Page object for skill create/edit form.

    URL: /skills/create (create) or /skills/all/{id} (edit)
    """

    # Form field locators
    name_input = LocatorDescriptor(
        testid="skill-name-input",
        description="Skill name input field"
    )

    description_input = LocatorDescriptor(
        testid="skill-description-input",
        description="Skill description input field"
    )

    instructions_editor = LocatorDescriptor(
        testid="skill-instructions-editor",
        description="Skill instructions CodeMirror editor wrapper"
    )

    instructions_editor_content = LocatorDescriptor(
        testid="skill-instructions-editor-content",
        description="Skill instructions CodeMirror content element (.cm-content)"
    )

    instructions_edit_mode_button = LocatorDescriptor(
        testid="skill-instructions-edit-mode-button",
        description="Instructions Edit/Preview toggle — Edit mode button (ELITEA-2432)"
    )

    instructions_preview_mode_button = LocatorDescriptor(
        testid="skill-instructions-preview-mode-button",
        description="Instructions Edit/Preview toggle — Preview mode button (ELITEA-2432)"
    )

    instructions_preview_content = LocatorDescriptor(
        testid="skill-instructions-preview-content",
        description="Instructions Preview-mode rendered Markdown container (ELITEA-2432)"
    )

    save_button = LocatorDescriptor(
        testid="skill-save-button",
        description="Save skill button"
    )

    cancel_button = LocatorDescriptor(
        testid="skill-cancel-button",
        description="Cancel button"
    )

    tags_input = LocatorDescriptor(
        testid="skill-tags-input",
        description="Tags combobox wrapper (MUI Autocomplete root)"
    )

    name_input_field = LocatorDescriptor(
        testid="skill-name-input-field",
        description="Skill name — real <input> element (skill-name-input is the wrapper)"
    )

    description_input_field = LocatorDescriptor(
        testid="skill-description-input-field",
        description="Skill description — real <textarea> element (skill-description-input is the wrapper)"
    )

    tags_input_field = LocatorDescriptor(
        testid="skill-tags-input-field",
        description="Tags combobox — real <input> element (skill-tags-input is the wrapper)"
    )

    tag_chip = LocatorDescriptor(
        testid="skill-tag-chip",
        description="Committed tag chip (one per tag; shared testid, collection locator)"
    )

    # Dynamic (runtime-parameterized) testid template — Tags autocomplete
    # option for a previously-created project tag. See
    # ``select_existing_tag()``.
    SKILL_TAG_OPTION = '[data-testid="skill-tag-option-{}"]'

    # Dynamic (runtime-parameterized) testid template — a committed tag
    # chip's delete icon, keyed by tag name (ELITEA-2433). Added via
    # add-data-testid (EliteaUI CreateSkillForm.jsx's ``chipDeleteTestId``
    # prop on ``TagEditor``/``AutoCompleteDropDown``, mirroring the existing
    # ``getOptionTestId`` pattern) — see ``remove_tag()``.
    SKILL_TAG_CHIP_DELETE = '[data-testid="skill-tag-chip-delete-{}"]'

    # ------------------------------------------------------------------
    # Icon picker (ELITEA-2602) — CreateSkillForm.jsx is the SAME shared
    # component rendered on both /skills/create and /skills/all/{id}
    # (confirmed via source: EditSkill.jsx and CreateSkill.jsx both render
    # it), so these live on the FORM page (not the detail page, unlike
    # AgentDetailPage's icon fields, since Agent uses two separate
    # components for create vs edit — see
    # `.agents/memory/qa-engineer/agent_form_dual_component_and_icon_picker_quirks.md`).
    # `skill_icon_button`/`skill_icon_img` testids added via add-data-testid
    # to CreateSkillForm.jsx's `<EntityIcon>` call (EliteaUI automation/testids
    # commit 3d74538c) — mirrors AgentDetailPage.agent_icon_button/
    # agent_icon_img's naming, scoped to the Skill call site.
    skill_icon_button = LocatorDescriptor(
        testid="skill-form-icon-button",
        description=(
            "Skill icon avatar/button (opens the icon picker). Shares the "
            "same hover-then-click quirk as the Agent icon picker (same "
            "EntityIcon component): a bare single .click() with no prior "
            ".hover() only mounts the hover-triggered edit-pencil overlay "
            "and does NOT open the dialog. Callers must hover() before "
            "click()."
        ),
    )
    skill_icon_img = LocatorDescriptor(
        testid="skill-form-icon-img",
        description="Skill form icon's <img> element (absent until an "
                     "icon.url is set — see get_form_icon_src())",
    )
    # Icon picker dialog (SelectIconDialog.jsx) — SHARED across
    # Agent/Skill/Pipeline, same testids AgentDetailPage already declares
    # (literal `agent-` prefix, entity-agnostic per that component's own
    # naming — see `.agents/testing.md` § Locator policy).
    icon_picker_dialog = LocatorDescriptor(testid="agent-icon-picker-dialog")
    icon_picker_close_button = LocatorDescriptor(testid="agent-icon-picker-close-button")
    # Upload button — no testid existed anywhere on this shared dialog
    # before ELITEA-2602 (confirmed via source read: the header IconButton
    # only carried a tooltip accessible name). Added via add-data-testid
    # (EliteaUI automation/testids commit 3d74538c) with the entity-agnostic
    # `agent-` prefix, matching the dialog's own naming convention.
    icon_picker_upload_button = LocatorDescriptor(
        testid="agent-icon-picker-upload-button",
        description='Icon picker dialog — "Upload" header button (opens '
                     "the native file chooser)",
    )

    # App-wide toast (shared Toast.jsx component) — used to confirm "The
    # image has been uploaded" after a successful icon upload.
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body",
    )
    # App-wide toast Alert root (same shared Toast.jsx component) — carries
    # data-severity (ELITEA-2604, used to confirm the oversized-icon
    # rejection toast is severity="error"). Not yet declared on this page
    # object before this case; pre-existing testid, mirrors
    # ChatPage.toast_alert / AgentDetailPage.toast_alert.
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    # Severity-scoped toast alert selector — testid identity + data-severity
    # state filter, the compliant shape for a state-dependent assertion
    # (mirrors ChatPage.TOAST_ALERT_SEVERITY / AgentDetailPage.TOAST_ALERT_SEVERITY).
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

    # "Default" tile in the icon picker's gallery — selecting it (edit mode)
    # reverts the skill to the system default icon. Pre-existing, shared/
    # entity-agnostic testid (same component AgentDetailPage.icon_picker_default_icon
    # already declares) — not yet exposed on this page object before ELITEA-2604.
    default_icon_tile = LocatorDescriptor(
        testid="agent-icon-picker-default-icon",
        description='Icon picker dialog — "Default" tile; selecting it '
                     "reverts to the system default icon (entity-agnostic).",
    )

    # NOTE (ELITEA-2604 implementer, live-confirmed 2026-08-12): dynamic
    # "Uploaded" gallery templates (ICON_PICKER_OPTION/ICON_PICKER_UPLOADED/
    # ICON_PICKER_UPLOADED_SELECTED/ICON_PICKER_UPLOADED_DELETE_BUTTON), the
    # shared alert_dialog_content/alert_dialog_confirm_button confirmation
    # dialog, and a delete_selected_uploaded_icon() method (mechanism (a) —
    # delete the currently-selected uploaded icon via its hover-revealed
    # delete button) were explored here but REMOVED — confirmed live that the
    # "Uploaded" gallery's infinite-scroll loader (ListInfiniteMoreLoader +
    # RTK Query merge in getSkillIcons) gets PERMANENTLY stuck after a
    # mutation (upload/replace/delete) invalidates the list while the
    # dialog's local `page` state is already > 0 — exactly the situation this
    # test's own Part B/C already produce by the time Part D runs. Filed as
    # EliteaAI/elitea-testing-public#1459. This test uses mechanism (b)
    # (select_default_icon_tile(), below) instead, per the AFS's own
    # documented phased-approach allowance. The `agent-icon-picker-uploaded-
    # {index}-delete-button` testid (EliteaAI/EliteaUI@1553565f) remains live
    # in EliteaUI source for a future case once #1459 is fixed.

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_form_load(self, timeout: int = 15000):
        """Wait for the skill create/edit form to be fully loaded.

        Waits for the Name input to be visible and network to settle.
        """
        self.name_input.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        self.page.wait_for_timeout(1000)
        logger.info("Skill form loaded")

    # ------------------------------------------------------------------
    # Form operations
    # ------------------------------------------------------------------

    @action("Fill skill form")
    def fill_form(
        self,
        name: str,
        instructions: str,
        description: str = "Automation test skill",
    ):
        """Fill all required fields in the skill form.

        Name and description use click + clear + press_sequentially (React
        onChange pattern). Instructions use the CodeMirror pattern:
        click + Ctrl+A + keyboard.type().

        Args:
            name: Skill name (required).
            instructions: Skill instructions text (required, CodeMirror).
            description: Skill description (required, defaults to generic value).
        """
        self._fill_text_input(self.name_input, name)
        self._fill_text_input(self.description_input, description)
        self.fill_instructions(instructions)
        logger.info("Filled skill form: name=%r", name)

    @action("Set name")
    def set_name(self, name: str):
        """Replace the Name field's content (works on pre-filled fields).

        Mirrors :meth:`set_description` exactly — the wrapper-level click +
        Ctrl+A pattern in :meth:`fill_form`/:meth:`_fill_text_input` only
        reliably clears an *empty* field; ``Control+a`` alone does not
        reliably select existing content first (typed text ends up inserted
        rather than replacing it, or an empty ``text`` argument leaves the
        prior value in place since a bare selection with nothing typed over
        it does not clear the field). Uses ``Locator.select_text()`` +
        Backspace to reliably clear the real, editable input (addressed
        directly via its own ``skill-name-input-field`` testid, set on the
        real element via MUI's ``inputProps``/``htmlInput`` slot, not a raw
        CSS chain off the ``skill-name-input`` wrapper testid) before typing
        the replacement — needed for a step that must clear an
        already-populated Name field back to empty.

        Args:
            name: New name text (pass ``""`` to clear the field).
        """
        field = self.name_input_field
        field.click()
        field.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        if name:
            self.page.keyboard.type(name)
        self.page.wait_for_timeout(300)
        logger.info("Set name: %r", name[:60])

    @action("Set description")
    def set_description(self, description: str):
        """Replace the Description field's content (works on pre-filled fields).

        The Description field renders as two ``<textarea>`` elements (MUI's
        autosize shadow copy plus the real, editable one) — the wrapper-level
        click + Ctrl+A pattern in :meth:`fill_form` only reliably clears an
        *empty* field; ``Control+a`` alone does not reliably select existing
        content here (typed text ends up inserted rather than replacing it).
        Uses Locator.select_text() + Backspace to clear the real, editable
        textarea (addressed directly via its own
        ``skill-description-input-field`` testid, set on the real element via
        MUI's ``inputProps``/``htmlInput`` slot, not a raw CSS chain off the
        ``skill-description-input`` wrapper testid) before typing the
        replacement.

        Args:
            description: New description text.
        """
        field = self.description_input_field
        field.click()
        field.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(description)
        self.page.wait_for_timeout(300)
        logger.info("Set description: %r", description[:60])

    @action("Add tag")
    def add_tag(self, tag: str):
        """Type a tag into the Tags combobox and commit it with Enter.

        The Tags field is a MUI Autocomplete (``skill-tags-input`` testid on
        the root wrapper); the actual text input carries its own
        ``skill-tags-input-field`` testid.

        Args:
            tag: Tag text to type and commit.
        """
        tag_field = self.tags_input_field
        tag_field.click()
        tag_field.type(tag)
        tag_field.press("Enter")
        self.page.wait_for_timeout(200)
        logger.info("Added tag: %r", tag)

    @action("Select existing tag from autocomplete")
    def select_existing_tag(self, tag_name: str, timeout: int = 5000):
        """Select a previously-created tag from the Tags autocomplete dropdown.

        Unlike :meth:`add_tag` (type + Enter, which commits a brand-new tag),
        this selects an existing project-scoped tag suggestion — confirmed
        live (ELITEA-1740 AFS exploration): once a tag exists in the project,
        later skills' Tags combobox surfaces it as a clickable option in the
        MUI Autocomplete listbox. Each option carries its own
        ``skill-tag-option-{tag_name}`` testid (set directly on the
        ``<li role="option">`` node), addressed via the
        :attr:`SKILL_TAG_OPTION` class-level template constant rather than
        an inline per-call testid lookup.

        Args:
            tag_name: Existing tag text to select from the dropdown.
            timeout: Maximum wait time in milliseconds for the option to appear.
        """
        tag_field = self.tags_input_field
        tag_field.click()
        tag_field.type(tag_name)
        option = self.page.locator(self.SKILL_TAG_OPTION.format(tag_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.page.wait_for_timeout(200)
        logger.info("Selected existing tag: %r", tag_name)

    @action("Remove a committed tag chip")
    def remove_tag(self, tag_name: str, timeout: int = 5000):
        """Remove a committed tag chip by clicking its delete icon.

        Clicking the chip's label/body does NOT remove it — only the
        delete icon (a ``RemoveIcon`` SVG child) does. Located via the
        name-keyed ``skill-tag-chip-delete-{tag_name}`` testid (ELITEA-2433,
        added via add-data-testid) using the class-level
        :attr:`SKILL_TAG_CHIP_DELETE` template constant.

        Args:
            tag_name: Exact tag text of the chip to remove.
            timeout: Maximum wait time in milliseconds for the icon to appear.
        """
        delete_icon = self.page.locator(self.SKILL_TAG_CHIP_DELETE.format(tag_name))
        delete_icon.wait_for(state="visible", timeout=timeout)
        delete_icon.click()
        self.page.wait_for_timeout(200)
        logger.info("Removed tag: %r", tag_name)

    # ------------------------------------------------------------------
    # Icon picker (ELITEA-2602)
    # ------------------------------------------------------------------

    @action("Open the skill icon picker dialog")
    def open_icon_picker(self, timeout: int = 10000):
        """Open the skill icon picker dialog.

        LOCATOR: ``skill_icon_button``. Must ``hover()`` immediately before
        ``click()`` — the icon's clickable state only mounts once its
        hover-triggered edit-pencil overlay is rendered (same EntityIcon
        component/quirk as ``AgentDetailPage.open_icon_picker()``).

        Args:
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Opening the skill icon picker dialog")
        self.skill_icon_button.scroll_into_view_if_needed()
        self.skill_icon_button.hover()
        self.skill_icon_button.click()
        self.icon_picker_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Icon picker dialog opened")

    @action("Upload a custom skill icon")
    def upload_skill_icon(self, file_path: str, timeout: int = 10000):
        """Open the icon picker and upload a custom icon file.

        Opens the picker (:meth:`open_icon_picker`), clicks the Upload
        button (``icon_picker_upload_button``), selects *file_path* via the
        native file chooser, and waits for the "The image has been
        uploaded" toast (``uploadFile()`` in SelectIconDialog.jsx calls
        ``toastSuccess`` on success and auto-applies the icon — no explicit
        "select" click needed, confirmed live per the AFS).

        Args:
            file_path: Path to a valid image file (PNG/JPG, under 500KB).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Uploading skill icon: %s", file_path)
        self.open_icon_picker(timeout=timeout)

        with self.page.expect_file_chooser() as fc_info:
            self.icon_picker_upload_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

        self.toast_message.wait_for(state="visible", timeout=timeout)
        toast_text = self.toast_message.text_content()
        assert toast_text == "The image has been uploaded", (
            f"Expected 'The image has been uploaded' toast, got: {toast_text!r}"
        )
        self.wait_for_network(timeout=5000)
        logger.info("Skill icon uploaded")

    def get_form_icon_src(self, timeout: int = 5000) -> str:
        """Return the ``src`` of the skill form icon's ``<img>`` element.

        LOCATOR: ``skill_icon_img``. A skill with no icon explicitly set
        yet renders an inline SVG placeholder instead (no ``<img>`` at
        all) — mirrors ``AgentDetailPage.get_header_icon_src()`` — so this
        returns ``""`` in that case rather than timing out.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.skill_icon_img.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        return self.skill_icon_img.get_attribute("src") or ""

    def get_toast_alert(self, severity: str):
        """Return the toast Alert locator scoped to a specific data-severity value.

        Testid identity (``toast-alert``) + a ``data-severity`` state filter
        — the compliant shape for a state-dependent assertion (mirrors
        ``ChatPage.get_toast_alert()`` / ``AgentDetailPage``'s identical
        pattern for the same shared Toast.jsx component).

        Args:
            severity: e.g. "error", "success", "warning", "info".
        """
        return self.page.locator(self.TOAST_ALERT_SEVERITY.format(severity))

    @action("Upload a custom skill icon (edit mode — replaces the current icon)")
    def upload_skill_icon_edit_mode(self, file_path: str, timeout: int = 10000) -> str:
        """Open the icon picker (edit mode, entityId present) and upload a
        replacement icon file.

        Edit-mode upload fires TWO sequential requests — ``POST
        .../upload_skill_icon/prompt_lib/{project}`` (uploads to the gallery,
        identical to create mode) followed by ``PUT
        .../upload_skill_icon/prompt_lib/{project}/{versionId}`` (applies/
        persists the icon to this specific skill version) — unlike create
        mode's single POST (see :meth:`upload_skill_icon`). The "The image
        has been uploaded" toast is superseded by a second toast before the
        next snapshot in some runs, so this method asserts on the network
        response PAIR (POST 200 + PUT 200) as the authoritative persistence
        signal instead of a toast-text match (AFS ELITEA-2604 step 8's
        finding — :meth:`upload_skill_icon`'s exact-match toast assertion is
        correct only for the single-request create-mode path).

        Args:
            file_path: Path to a valid image file (PNG/JPG/GIF/WEBP, under 500KB).
            timeout: Maximum wait time in milliseconds for each response.

        Returns:
            The resulting ``skill-form-icon-img`` src after the PUT completes.
        """
        logger.info("Uploading skill icon (edit mode — replace): %s", file_path)
        self.open_icon_picker(timeout=timeout)

        with self.page.expect_response(
            lambda r: "/upload_skill_icon/prompt_lib/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as put_info:
            with self.page.expect_response(
                lambda r: "/upload_skill_icon/prompt_lib/" in r.url
                and r.request.method == "POST",
                timeout=timeout,
            ) as post_info:
                with self.page.expect_file_chooser() as fc_info:
                    self.icon_picker_upload_button.click()
                fc_info.value.set_files(file_path)
            post_response = post_info.value
            assert post_response.status == 200, (
                f"Edit-mode icon upload POST should return 200, got {post_response.status}"
            )
        put_response = put_info.value
        assert put_response.status == 200, (
            f"Edit-mode icon upload PUT should return 200, got {put_response.status}"
        )

        src = self.get_form_icon_src(timeout=timeout)
        logger.info("Skill icon replaced (edit mode) — resulting src: %s", src)
        return src

    @action("Attempt to upload an oversized skill icon (expects a 400 rejection)")
    def attempt_upload_oversized_icon(self, file_path: str, timeout: int = 10000) -> dict:
        """Open the icon picker and attempt to upload a file expected to be
        rejected server-side for exceeding the size limit.

        Validation is server-side, not client-side (confirmed via source:
        ``useUploadSkillIconMutation``'s RTK-Query builder has no pre-flight
        size check — the FormData POST always fires) — this waits for the
        network response rather than short-circuiting on a client-side
        error. The icon picker dialog stays OPEN on a failed upload (does
        NOT auto-close, unlike a successful one — see :meth:`upload_skill_icon`).

        Args:
            file_path: Path to an oversized image file (>500KB/512KB).
            timeout: Maximum wait time in milliseconds.

        Returns:
            The parsed JSON body of the 400 response (e.g.
            ``{"error": "File size exceeds 512 KB"}``).
        """
        logger.info("Attempting oversized skill icon upload: %s", file_path)
        self.open_icon_picker(timeout=timeout)

        with self.page.expect_response(
            lambda r: "/upload_skill_icon/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as response_info:
            with self.page.expect_file_chooser() as fc_info:
                self.icon_picker_upload_button.click()
            fc_info.value.set_files(file_path)

        response = response_info.value
        assert response.status == 400, (
            f"Oversized icon upload should be rejected with 400, got {response.status}"
        )
        body = response.json()
        logger.info("Oversized upload rejected as expected: %r", body)
        return body

    @action("Select the Default icon tile (revert to default, edit mode)")
    def select_default_icon_tile(self, timeout: int = 10000) -> str:
        """Open the icon picker and click the "Default" tile to reset the
        skill's icon to the system default (edit mode).

        LOCATOR: ``default_icon_tile`` (``agent-icon-picker-default-icon``,
        pre-existing shared testid). In edit mode (entityId present),
        clicking this tile calls the same ``replaceSkillIcon`` mutation as
        any other gallery selection but with an empty ``{name: "", url: ""}``
        payload — confirmed live: ``PUT
        .../upload_skill_icon/prompt_lib/{project}/{versionId}`` -> 200,
        toast "The icon has been reset to default icon", dialog auto-closes.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The resulting ``skill-form-icon-img`` src — empty string, since
            the icon reverted to the default (absent-``<img>``) state, see
            :meth:`get_form_icon_src`.
        """
        logger.info("Selecting the Default icon tile (revert to default)")
        self.open_icon_picker(timeout=timeout)

        with self.page.expect_response(
            lambda r: "/upload_skill_icon/prompt_lib/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as put_info:
            self.default_icon_tile.click()
        put_response = put_info.value
        assert put_response.status == 200, (
            f"Reset-to-default PUT should return 200, got {put_response.status}"
        )

        self.icon_picker_dialog.wait_for(state="hidden", timeout=timeout)
        src = self.get_form_icon_src(timeout=timeout)
        logger.info("Icon reset to default — resulting src: %r", src)
        return src

    def _fill_text_input(self, locator, text: str):
        """Fill a standard MUI text input with React-safe keyboard events.

        Clicks the wrapper to transfer focus to the inner input, then uses
        page.keyboard so events go to the focused element (not the wrapper div).

        Args:
            locator: LocatorDescriptor or Playwright locator for the input.
            text: Text to type.
        """
        locator.click()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(text)
        self.page.wait_for_timeout(300)

    @action("Fill instructions editor")
    def fill_instructions(self, text: str):
        """Replace the CodeMirror instructions editor's content.

        CodeMirror does not respond to fill(). On an *empty* editor,
        click + Ctrl+A + keyboard.type() works. On an *already-populated*
        editor (editing an existing skill's instructions), Ctrl+A does not
        reliably select the existing content first — typed text ends up
        inserted rather than replacing it, producing a doubled value
        (``"new text" + "old text"``). Mirrors the same finding documented
        for the Description textarea (:meth:`set_description`) — use
        ``Locator.select_text()`` + Backspace to reliably clear first,
        which works for both empty and populated editors alike.

        Args:
            text: Instructions text to enter.
        """
        self.instructions_editor.click()
        self.page.wait_for_timeout(200)
        self.instructions_editor_content.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(text)
        self.page.wait_for_timeout(300)
        logger.info("Filled instructions editor")

    @action("Fill instructions editor with Markdown source (list-safe)")
    def fill_instructions_markdown(self, text: str):
        """Replace the CodeMirror instructions editor's content with raw
        Markdown source that may contain multi-line lists (ELITEA-2432).

        Same reliable-clear mechanism as :meth:`fill_instructions`
        (``select_text()`` + Backspace, works on both empty and populated
        editors), but inserts via ``Keyboard.insert_text()`` instead of
        ``Keyboard.type()``. Confirmed live: this editor's markdown
        language mode (``@codemirror/lang-markdown``) auto-continues an
        unordered list on Enter — ``keyboard.type()`` dispatches a
        discrete Enter keydown for every ``\\n`` in the typed text, which
        triggers that continuation and inserts an extra ``"- "`` at the
        start of the line right after a list-item line, corrupting any
        typed multi-line list Markdown (e.g. typing
        ``"- Item one\\n- Item two"`` renders as
        ``"- Item one\\n- - Item two"``). ``keyboard.insert_text()`` inserts
        the whole string as one atomic operation with no discrete Enter
        keydown, so the list-continuation keymap never fires, while still
        triggering the editor's real input handling (confirmed live: the
        character counter and React form state update correctly).

        Args:
            text: Markdown instructions text to enter verbatim.
        """
        self.instructions_editor.click()
        self.page.wait_for_timeout(200)
        self.instructions_editor_content.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.insert_text(text)
        self.page.wait_for_timeout(300)
        logger.info("Filled instructions editor with Markdown source (list-safe)")

    # ------------------------------------------------------------------
    # Instructions Edit/Preview toggle (ELITEA-2432)
    # ------------------------------------------------------------------

    @action("Switch Instructions to Edit mode")
    def click_edit_mode(self, timeout: int = 5000):
        """Switch the Instructions section to Edit mode (raw Markdown/CodeMirror).

        100% client-side toggle (local ``useState`` in ``CreateSkillForm.jsx``) —
        no network wait needed, only a short settle for the view swap.
        """
        self.instructions_edit_mode_button.click()
        self.page.wait_for_timeout(200)
        logger.info("Switched Instructions to Edit mode")

    @action("Switch Instructions to Preview mode")
    def click_preview_mode(self, timeout: int = 5000):
        """Switch the Instructions section to Preview mode (rendered Markdown).

        100% client-side toggle — no network wait needed, only a short
        settle for the view swap.
        """
        self.instructions_preview_mode_button.click()
        self.page.wait_for_timeout(200)
        logger.info("Switched Instructions to Preview mode")

    # ------------------------------------------------------------------
    # Save state
    # ------------------------------------------------------------------

    def is_save_enabled(self) -> bool:
        """Return True if the Save button is currently enabled.

        Returns:
            True if Save is enabled, False if disabled.
        """
        return self.save_button.is_enabled()

    def wait_for_form_validation(self, timeout: int = 1000):
        """Wait for React form debounce and validation to complete.

        After filling form fields, React's onChange + validation pipeline
        takes ~500ms to update the Save button's disabled state.
        """
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(500)

    @action("Save skill and wait for navigation")
    def save_and_wait_for_navigation(self, timeout: int = 15000):
        """Click Save and wait for navigation to the skill detail page.

        The create form's useBlocker (nav guard) intercepts the programmatic
        navigate() call that fires after a successful save because the form is
        still marked dirty at that moment.  The blocker shows a "There are
        unsaved changes. Are you sure you want to leave?" dialog.  We wait up
        to 3 s for that dialog to appear, click Confirm if it does, then wait
        for the URL to settle on /skills/all/{id}.

        Args:
            timeout: Maximum wait time in milliseconds for the final URL change.
        """
        logger.info("Clicking Save and waiting for navigation")
        self.save_button.evaluate("el => el.click()")

        # Poll for either the nav-blocker confirm button or the detail page URL.
        # The nav-blocker dialog appears ~0-3s after save; dismiss it if it shows.
        import time as _time
        deadline = _time.time() + timeout / 1000
        while _time.time() < deadline:
            # Check if navigation already happened
            if "/skills/all/" in self.page.url and "/create" not in self.page.url:
                logger.info("Navigated to detail page directly (no dialog)")
                break
            # Check if the nav-blocker dialog is visible
            confirm_btn = self.page.get_by_test_id("alert-dialog-confirm-button")
            if confirm_btn.count() > 0 and confirm_btn.is_visible():
                confirm_btn.click()
                logger.info("Dismissed nav-blocker dialog after save")
                break
            self.page.wait_for_timeout(300)

        # Wait for the detail page URL to settle, then for the page to render.
        self.page.wait_for_url("**/skills/all/**", timeout=timeout)
        self.page.get_by_test_id("skill-information-section").wait_for(
            state="visible", timeout=timeout
        )
        self.wait_for_network(timeout=5000)
        logger.info("Saved skill — URL: %s", self.page.url)

    @action("Save skill (create flow) and capture the POST payload + status")
    def save_and_wait_for_navigation_capturing_payload(self, timeout: int = 15000) -> tuple[dict, int]:
        """Same as :meth:`save_and_wait_for_navigation`, but also captures the
        create-flow ``POST .../elitea_core/skills/prompt_lib/{project_id}``
        request body AND response status (ELITEA-2434 — proves pre-save tags
        ride the create payload, and that the create actually succeeded with
        a ``201``, not just that the eventual redirect happened).

        DECLARED IMPROVISATION — reads the body via a temporary
        ``page.route()`` interceptor (reading ``route.request.post_data_json``
        inside the handler, then ``route.continue_()``) rather than
        ``response.request.post_data_json`` / ``Page.expect_request``, mirroring
        the pattern already used in ``SecretsPage`` (``secrets_page.py``) for
        the same documented reason: interception reads the body BEFORE the
        request leaves the browser, unaffected by the post-hoc-read timing gap.
        The status is captured separately via ``page.expect_response()``
        wrapping the same save action — the two mechanisms are independent
        listeners on the same request/response pair, so both fire from the
        one click. No sanctioned canon pattern covers Playwright
        request-body capture in this project yet — flagged for the lead per
        `.agents/role-overrides.md` § Declared-improvisation protocol.

        Args:
            timeout: Maximum wait time in milliseconds for the final URL change.

        Returns:
            A ``(payload, status)`` tuple: the parsed JSON body of the
            create-flow POST request, and its HTTP response status code.
        """
        captured: dict = {}
        route_pattern = "**/elitea_core/skills/prompt_lib/**"

        def _capture_post_body(route):
            if route.request.method == "POST":
                captured["post_data_json"] = route.request.post_data_json
            route.continue_()

        self.page.route(route_pattern, _capture_post_body)
        try:
            with self.page.expect_response(
                lambda r: "/elitea_core/skills/prompt_lib/" in r.url
                and r.request.method == "POST",
                timeout=timeout,
            ) as response_info:
                self.save_and_wait_for_navigation(timeout=timeout)
            status = response_info.value.status
        finally:
            self.page.unroute(route_pattern, _capture_post_body)
        return captured.get("post_data_json"), status

    # ------------------------------------------------------------------
    # Read field values
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the current value of the Name input field.

        The ``skill-name-input`` testid is on the MUI FormControl wrapper,
        not the inner ``<input>`` — the real element carries its own
        ``skill-name-input-field`` testid.
        """
        return self.name_input_field.input_value()

    def get_description(self) -> str:
        """Return the current value of the Description field.

        The ``skill-description-input`` testid is on the MUI FormControl
        wrapper; the actual ``<textarea>`` carries its own
        ``skill-description-input-field`` testid.
        """
        return self.description_input_field.input_value()

    def get_instructions(self) -> str:
        """Return the current text content of the Instructions CodeMirror editor.

        CodeMirror has no ``input_value()`` — read the rendered text content
        of the ``.cm-content`` element instead, addressed via its own
        ``skill-instructions-editor-content`` testid (set directly on the
        CodeMirror content node via EditorView.contentAttributes in
        EliteaUI, ELITEA-1737) rather than a raw CSS selector chained off
        the wrapper testid.
        """
        return (self.instructions_editor_content.text_content() or "").strip()

    def get_instructions_multiline(self) -> str:
        """Return the Instructions CodeMirror editor's text content,
        preserving line breaks (ELITEA-2432).

        :meth:`get_instructions` reads ``text_content()``, which
        concatenates CodeMirror's per-line ``<div class="cm-line">``
        elements with NO separator — correct for the single-line
        instructions every other caller of :meth:`get_instructions` uses,
        but confirmed live to silently drop every line break for
        multi-line content (a 3-line Markdown source round-trips as one
        unbroken string via ``text_content()``). ``inner_text()`` is
        layout-aware — Playwright inserts a newline between adjacent
        block-level elements — so it reconstructs the editor's line breaks
        correctly with no new selector needed (each ``cm-line`` div is
        already block-level).
        """
        return (self.instructions_editor_content.inner_text() or "").strip()

    def get_preview_content(self) -> str:
        """Return the rendered Markdown text content of the Instructions
        Preview pane (ELITEA-2432).

        Reads ``text_content()`` of the ``skill-instructions-preview-content``
        container — the app's shared ``Markdown`` component renders bold/list/etc.
        as real HTML nodes with the raw Markdown syntax characters (``**``, ``- ``)
        stripped, so this text can be compared directly against the raw source
        from :meth:`get_instructions` to prove real interpretation happened.
        Only meaningful while the Preview mode is active (see :meth:`click_preview_mode`).
        """
        return (self.instructions_preview_content.text_content() or "").strip()

    def get_tags(self) -> list[str]:
        """Return the currently committed tags as a list of strings.

        Reads each committed-tag chip via the shared ``skill-tag-chip``
        testid (one element per tag; the delete icon is an SVG with no
        text nodes, so each chip's text content is exactly its tag name).

        Returns:
            List of tag name strings, in display order.
        """
        chips = self.tag_chip
        return [chips.nth(i).text_content() or "" for i in range(chips.count())]
