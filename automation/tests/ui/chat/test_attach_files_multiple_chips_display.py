"""UI Test for ELITEA-2196 — Chat: File Attachments, Upload Multiple Files and
Verify They Display Above Message Input Field.

Verifies that attaching 4 files renders 4 chips in a single horizontal row
above the composer, each chip showing a file-type icon, the filename, and a
functional X (close) button, styled with a genuinely dark (composited)
background and light (white) filename text.

Spec: test-specs/chat-interface/l3_attach-files-multiple-chips-display_ELITEA-2196.md

Case-text clarification (AFS § Coverage Map, step 2; filed as issue #1589
— a dedicated ticket for THIS case's own mismatch, distinct from #1122
which covers the same finding for the sibling ELITEA-2197 case): the
case's own "files begin uploading" wording does not describe a live,
observable event — attaching is entirely client-side (confirmed live, no
network request fires at selection time, same finding already documented
by the merged ELITEA-2197 AFS). The real, self-consistent observable — the
chips render immediately — is what this test asserts instead.

Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@7f29c3dc):
- ``chat-attachment-remove-chip-{index}`` — the (X) remove-icon Box inside
  each visible attachment chip (``FileList.jsx``). The ELITEA-2197 AFS
  reserved this as ``chat-attachment-chip-remove-{index}``; renamed during
  this implementation — that name shares the ``chat-attachment-chip-``
  prefix with ``ChatPage.CHAT_ATTACHMENT_CHIP_PREFIX``, which the existing,
  merged ``get_attachment_chip_count()`` (ELITEA-2197) uses, so every
  remove button was being double-counted as an extra chip. See AFS
  Coverage Map / Concrete Handles for the amendment.

New page-object surface (``ChatPage``, additive):
- ``CHAT_ATTACHMENT_CHIP_REMOVE`` template constant.
- ``get_attachment_chip_remove_button(index)`` / ``remove_attachment_chip(index)``.
- ``get_attachment_chip_visual_facts(index)`` (background/text-color/icon
  presence, read via one scoped ``.evaluate()`` call).

Known defects: none for this case.

ELITEA-2198 (``extend-existing`` onto this module — AFS
test-specs/chat-interface/lextend_attach-files-remove-individual-files-sequential_ELITEA-2198.md)
adds a SIBLING test below,
``test_attach_files_then_remove_two_individually_sequentially``. It covers the
gap this module's original test never exercises: a SECOND sequential
individual removal (click X on chip 0, then click X on the next chip 0 after
renumbering), verifying removal keeps decrementing/renumbering correctly
across repeated clicks — not just once — and that the exact two SURVIVING
filenames (not just a count) are the ones never clicked. Zero new testids —
reuses ``CHAT_ATTACHMENT_CHIP_REMOVE`` / ``remove_attachment_chip()`` /
``wait_for_attachment_chip_count()`` verbatim, all added by this module's
original ELITEA-2196 implementation. This module's original test and its
fixture usage are UNCHANGED.

ELITEA-2199 (``extend-existing`` onto this module — AFS
test-specs/chat-interface/lextend_attach-files-icon-genericity-and-truncation_ELITEA-2199.md)
adds a SIBLING test below,
``test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates``.
Covers two gaps: (a) attaching 3 genuinely different file types (.png/.pdf/.txt,
not renamed .txt files) and verifying every chip renders the exact SAME icon
markup — the live-confirmed, corrected observable that supersedes the case's
literal "type-appropriate icon" wording (case-text clarification, issue
#1591 — ``FileList.jsx`` renders one generic ``AttachedFileIcon`` for every
attachment, no branching by type); (b) attaching a genuinely long filename
(never exercised by this module's own short-filename fixtures) and verifying
its chip's name text genuinely, visually truncates
(``scrollWidth > clientWidth``, CSS ``text-overflow: ellipsis``). New
page-object surface (additive, ``ChatPage``):
``get_attachment_chip_icon_markup(index)``,
``get_attachment_chip_name_overflow_facts(index)``.

ELITEA-2467 (``extend-existing`` onto this module — AFS
test-specs/chat-interface/lextend_attach-files-truncation-and-overflow-click-to-expand_ELITEA-2467.md)
adds a SIBLING test below,
``test_long_filename_truncates_and_overflow_indicator_click_expands``. Covers
two gaps: (a) the same long-filename truncation observable as ELITEA-2199,
verified independently on this case's own trigger (shared
``get_attachment_chip_name_overflow_facts()`` helper, no duplication); (b)
the "+N" overflow indicator's CLICK-TO-EXPAND interaction as its own
observable — existing tests (ELITEA-2196/2197) click the overflow button
only as page-object plumbing (``get_overflow_attachment_names()``) to read
hidden filenames for a total-count assertion; this is the first test to
assert the interaction itself: ``aria-expanded`` flips to ``"true"`` on
click, a real MUI ``role="menu"`` element becomes visible, and the hidden
filenames render in order — proving the control is a REAL, functioning
expand action, not an inert count display. New page-object surface
(additive, ``ChatPage``): ``open_attachment_overflow_menu_and_read()``,
plus the ``chat_attachment_overflow_menu`` testid (``FileList.jsx``
``slotProps.list`` — this IS the MUI ``MenuList`` root, i.e. the
``role="menu"`` node itself, not a derived proxy).

All new test methods below reuse ``attach_files_via_menu()`` /
``close_plus_menu_popper()`` / ``wait_for_attachment_chip_count()`` /
``remove_attachment_chip()`` verbatim (all pre-existing, ELITEA-2196/2197);
this module's earlier tests and their fixture usage are UNCHANGED.

Usage:
    cd automation
    pytest tests/ui/chat/test_attach_files_multiple_chips_display.py -v
"""

import base64
import logging
import re

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

# AFS § Automation Hints — reuse the ELITEA-2197 precedent viewport so
# FileList.jsx's width-driven visible/overflow split is deterministic.
VIEWPORT_WIDTH = 1700
VIEWPORT_HEIGHT = 1100

FILE_COUNT = 4  # AFS: chosen so all 4 render as VISIBLE chips, zero overflow

# ELITEA-2467 AFS § Test Data — confirmed live at VIEWPORT_WIDTH=1700: 7
# attached files render as exactly 4 visible chips + a "+3" overflow bucket.
OVERFLOW_FILE_COUNT = 7

# ELITEA-2199/2467 AFS § Test Data — confirmed live: at the 200px-wide chip /
# ~116px-wide name column, this filename's rendered scrollWidth (731px) is
# far past its clientWidth (116px) — genuine CSS-ellipsis truncation, not
# merely a short name that happens to fit.
LONG_FILENAME = (
    "this_is_a_genuinely_very_long_filename_that_should_definitely_get_"
    "truncated_in_the_ui_chip_display.txt"
)

# ELITEA-2199 AFS § Test Data — a minimal, genuinely valid 1x1 PNG (not a
# renamed .txt file) so the "different types" check exercises real
# content, not just a swapped extension.
_MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

# Luminance thresholds (WCAG relative-luminance formula, 0=black..1=white).
# Confirmed live this session: composited chip background ~0.03 (very dark),
# filename text luminance 1.0 (pure white) — thresholds leave ample margin.
DARK_LUMINANCE_MAX = 0.3
LIGHT_LUMINANCE_MIN = 0.7

_RGBA_RE = re.compile(r"rgba?\(([^)]+)\)")


def _parse_rgba(color: str) -> tuple:
    """Parse a CSS 'rgb(r, g, b)' / 'rgba(r, g, b, a)' string into (r, g, b, a)."""
    match = _RGBA_RE.match(color.strip())
    assert match, f"Unrecognized CSS color format: {color!r}"
    parts = [float(p.strip()) for p in match.group(1).split(",")]
    r, g, b = parts[0], parts[1], parts[2]
    a = parts[3] if len(parts) > 3 else 1.0
    return r, g, b, a


def _relative_luminance(r: float, g: float, b: float) -> float:
    """WCAG relative luminance of an (r, g, b) triple in 0..255 range, as 0..1."""
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def _composited_luminance(chip_bg: str, backdrop_bg: str) -> float:
    """Composite a (possibly translucent) chip background over its backdrop,
    then return the resulting relative luminance — this is what a human eye
    actually perceives, unlike the raw (pre-composite) background-color alone.
    """
    cr, cg, cb, ca = _parse_rgba(chip_bg)
    br, bg, bb, _ba = _parse_rgba(backdrop_bg)
    r = cr * ca + br * (1 - ca)
    g = cg * ca + bg * (1 - ca)
    b = cb * ca + bb * (1 - ca)
    return _relative_luminance(r, g, b)


class TestAttachFilesMultipleChipsDisplay:
    """ELITEA-2196: Chat – File Attachments – Upload Multiple Files and
    Verify They Display Above Message Input Field (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2196_chat-file-attachments-upload-multiple-files-and-verify-they-display-above-message-input-field.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_attach_multiple_files_displays_chips_above_composer(self, page, conversation_id, tmp_path):
        """Attach 4 files at once; verify chips (icon+name+X button+styling)."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        file_paths = []
        file_names = []
        for i in range(1, FILE_COUNT + 1):
            name = f"testfile_{i}.txt"
            f = tmp_path / name
            f.write_text(f"Content of {name} for ELITEA-2196.")
            file_paths.append(str(f))
            file_names.append(name)

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 2 — Click + > Attach Files, select 4 files in a single "
            "file-chooser action — verify the file chooser opens"
        ):
            # AFS Coverage Map: the case's own "files begin uploading" wording
            # is not a live observable — attaching is entirely client-side, no
            # network request fires at selection time (already documented by
            # the merged ELITEA-2197 AFS). attach_files_via_menu() internally
            # asserts the file chooser opens (page.expect_file_chooser()).
            chat.attach_files_via_menu(file_paths, timeout=UI_ELEMENT_TIMEOUT)
            # The plus-menu popper does NOT auto-close after a file-chooser
            # selection (documented gotcha, `_surface.md` § File attachments)
            # — close it via a neutral click so it can't intercept the
            # chip-content interactions below.
            chat.close_plus_menu_popper()

        with allure.step(
            "Step 3 — Verify all 4 files render as chips, in a single "
            "horizontal row above the message input, zero overflow"
        ):
            chat.wait_for_attachment_chip_count(FILE_COUNT)
            assert chat.get_attachment_overflow_count() == 0, (
                "Expected zero attachments in overflow at this viewport width "
                "— all 4 should render as visible chips (AFS § Test Data)"
            )
            visible_names = chat.get_visible_attachment_names()
            assert visible_names == file_names, (
                f"Expected chips {file_names!r} in selection order, got {visible_names!r}"
            )

            # "Horizontal row": all chip bounding boxes share one y coordinate.
            chip_boxes = [chat.get_attachment_chip(i).bounding_box() for i in range(FILE_COUNT)]
            assert all(box is not None for box in chip_boxes), "Every chip should have a resolvable bounding box"
            y_positions = {round(box["y"]) for box in chip_boxes}
            assert len(y_positions) == 1, f"Expected all chips on one row (same y), got y values: {y_positions}"

        with allure.step("Step 4 — Verify each chip shows a file-type icon and the filename"):
            for i, expected_name in enumerate(file_names):
                facts = chat.get_attachment_chip_visual_facts(i)
                assert facts["has_file_icon"], f"Chip {i} ({expected_name}) should render a file-type icon"
            # Filenames already verified via get_visible_attachment_names() above.

        with allure.step(
            "Step 5 — Verify each chip has an X (close) button; verify it "
            "functions (removes exactly the targeted chip, siblings unchanged)"
        ):
            for i in range(FILE_COUNT):
                remove_button = chat.get_attachment_chip_remove_button(i)
                assert remove_button.count() == 1, f"Chip {i} should have exactly one X (remove) button"
                assert remove_button.is_visible(), f"Chip {i}'s X (remove) button should be visible"

            # Functional check (AFS § Axis 2 addition): removing chip 0
            # should leave exactly the other 3 filenames attached.
            chat.remove_attachment_chip(0)
            chat.wait_for_attachment_chip_count(FILE_COUNT - 1)
            remaining_names = chat.get_visible_attachment_names()
            assert remaining_names == file_names[1:], (
                f"Expected {file_names[1:]!r} after removing chip 0, got {remaining_names!r}"
            )

        with allure.step(
            "Step 6 — Verify chip styling: composited background is dark, "
            "filename text is light (AFS: raw background-color alone is a "
            "translucent overlay, not dark by itself — assert the composited, "
            "actually-rendered result)"
        ):
            # Chip indices renumbered after Step 5's removal — chip 0 is now
            # testfile_2.txt, the first of the 3 remaining.
            for i in range(FILE_COUNT - 1):
                facts = chat.get_attachment_chip_visual_facts(i)
                bg_luminance = _composited_luminance(facts["background_color"], facts["body_background_color"])
                assert bg_luminance < DARK_LUMINANCE_MAX, (
                    f"Chip {i} composited background should be dark (luminance < "
                    f"{DARK_LUMINANCE_MAX}), got {bg_luminance:.3f} "
                    f"(chip bg={facts['background_color']!r}, backdrop={facts['body_background_color']!r})"
                )
                name_r, name_g, name_b, _a = _parse_rgba(facts["name_color"])
                name_luminance = _relative_luminance(name_r, name_g, name_b)
                assert name_luminance > LIGHT_LUMINANCE_MIN, (
                    f"Chip {i} filename text should be light (luminance > "
                    f"{LIGHT_LUMINANCE_MIN}), got {name_luminance:.3f} (color={facts['name_color']!r})"
                )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2198_chat-attachment-removal-remove-individual-files-by-clicking-x-button.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_attach_files_then_remove_two_individually_sequentially(self, page, conversation_id, tmp_path):
        """ELITEA-2198: attach 4 files, remove chip 0, then remove a SECOND
        (different) chip — verify individual removal keeps working correctly
        across two consecutive clicks, not just the first one, and that the
        exact two surviving filenames (never a bare count) are the ones never
        clicked (extend-existing onto this module — see module docstring)."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        file_paths = []
        file_names = []
        for i in range(1, FILE_COUNT + 1):
            name = f"testfile_seqrm_{i}.txt"
            f = tmp_path / name
            f.write_text(f"Content of {name} for ELITEA-2198.")
            file_paths.append(str(f))
            file_names.append(name)

        chat = ChatPage(page)

        with allure.step("Step 1 — Attach 4 files; verify all 4 chips shown"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.attach_files_via_menu(file_paths, timeout=UI_ELEMENT_TIMEOUT)
            chat.close_plus_menu_popper()
            chat.wait_for_attachment_chip_count(FILE_COUNT)
            assert chat.get_visible_attachment_names() == file_names, (
                f"Expected all 4 chips {file_names!r} visible after attaching, "
                f"got {chat.get_visible_attachment_names()!r}"
            )

        with allure.step("Step 2 — Click X on the first file chip; verify it is removed and 3 remain"):
            chat.remove_attachment_chip(0)
            chat.wait_for_attachment_chip_count(FILE_COUNT - 1)
            remaining_after_first = chat.get_visible_attachment_names()
            assert remaining_after_first == file_names[1:], (
                f"Expected {file_names[1:]!r} after removing the first chip, got {remaining_after_first!r}"
            )

        with allure.step(
            "Step 3 — Click X on another (different) chip; verify that file is "
            "removed and exactly 2 remain (the gap ELITEA-2196's own test never "
            "exercises: a SECOND sequential individual removal)"
        ):
            chat.remove_attachment_chip(0)  # chips renumbered after step 2; index 0 is now testfile_seqrm_2
            chat.wait_for_attachment_chip_count(FILE_COUNT - 2)
            remaining_after_second = chat.get_visible_attachment_names()
            assert remaining_after_second == file_names[2:], (
                f"Expected {file_names[2:]!r} after removing a second chip, got {remaining_after_second!r}"
            )

        with allure.step(
            "Step 4 — Verify the remaining files are still shown correctly: 2 "
            "chips visible, each with its own filename and a functioning X button"
        ):
            assert chat.get_visible_attachment_names() == file_names[2:], (
                "Remaining chips should still show the exact 2 files that were "
                "never clicked, in original order"
            )
            for i in range(FILE_COUNT - 2):
                remove_button = chat.get_attachment_chip_remove_button(i)
                assert remove_button.count() == 1, f"Remaining chip {i} should have exactly one X (remove) button"
                assert remove_button.is_visible(), f"Remaining chip {i}'s X (remove) button should be visible"

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2199_chat-attachment-preview-verify-attached-files-display-with-filenames-and-icons.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates(
        self, page, conversation_id, tmp_path
    ):
        """ELITEA-2199: attach files of 3 genuinely different types
        (.png/.pdf/.txt) — verify every chip renders the exact SAME icon
        markup (case-text clarification, issue #1591: FileList.jsx renders
        one generic icon for every attachment, no branching by type — NOT
        the case's literal "type-appropriate icon" wording). Separately
        attach a genuinely long filename and verify its chip's name text
        genuinely, visually truncates (scrollWidth > clientWidth).
        extend-existing onto this module (see module docstring)."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        png_path = tmp_path / "attachment_type_test.png"
        png_path.write_bytes(base64.b64decode(_MINIMAL_PNG_B64))
        pdf_path = tmp_path / "attachment_type_test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
        txt_path = tmp_path / "attachment_type_test.txt"
        txt_path.write_text("Content of attachment_type_test.txt for ELITEA-2199.")
        type_file_paths = [str(png_path), str(pdf_path), str(txt_path)]

        long_file_path = tmp_path / LONG_FILENAME
        long_file_path.write_text(f"Content of {LONG_FILENAME} for ELITEA-2199.")

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 2 — Click + > Attach Files, select 3 files of different "
            "types (.png, .pdf, .txt) in a single file-chooser action"
        ):
            chat.attach_files_via_menu(type_file_paths, timeout=UI_ELEMENT_TIMEOUT)
            chat.close_plus_menu_popper()
            chat.wait_for_attachment_chip_count(3)

        with allure.step(
            "Step 3 — Verify all 3 chips render the exact same icon markup "
            "— the live-confirmed invariant that supersedes the case's "
            "literal 'type-appropriate icon' wording (issue #1591)"
        ):
            icon_markups = [chat.get_attachment_chip_icon_markup(i) for i in range(3)]
            assert all(markup for markup in icon_markups), (
                f"Every chip should render an icon element, got {icon_markups!r}"
            )
            assert len(set(icon_markups)) == 1, (
                "Issue #1591: the product should render the exact same "
                f"generic file-type icon for every attachment regardless of type, "
                f"got distinct icon markups across chips: {icon_markups!r}"
            )

        with allure.step(
            "Step 4 — In a separate attach action (fresh chip set), attach "
            "the 1 long-filename file alone and verify its name genuinely "
            "visually truncates"
        ):
            for _ in range(3):
                chat.remove_attachment_chip(0)
            chat.wait_for_attachment_chip_count(0)

            chat.attach_files_via_menu(str(long_file_path), timeout=UI_ELEMENT_TIMEOUT)
            chat.close_plus_menu_popper()
            chat.wait_for_attachment_chip_count(1)

            facts = chat.get_attachment_chip_name_overflow_facts(0)
            assert facts["scrollWidth"] > facts["clientWidth"], (
                "Long filename chip's name should genuinely visually "
                f"truncate (scrollWidth > clientWidth), got {facts!r}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2467_chat-attached-files-display-with-filenames-icons-and-truncation-for-long-names.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_long_filename_truncates_and_overflow_indicator_click_expands(self, page, conversation_id, tmp_path):
        """ELITEA-2467: attach a genuinely long filename alone and verify
        its chip's name text genuinely, visually truncates (scrollWidth >
        clientWidth). Separately attach 7 files and verify the '+3'
        overflow indicator is a REAL, functioning click-to-expand control —
        aria-expanded flips to 'true' on click, a real MUI role='menu'
        element becomes visible (chat-attachment-overflow-menu testid added
        this round, ELITEA-2467), and the exact 3 hidden filenames render in
        order — not an inert count display.
        extend-existing onto this module (see module docstring)."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        long_file_path = tmp_path / LONG_FILENAME
        long_file_path.write_text(f"Content of {LONG_FILENAME} for ELITEA-2467.")

        overflow_file_paths = []
        overflow_file_names = []
        for i in range(1, OVERFLOW_FILE_COUNT + 1):
            name = f"extra_file_{i}.txt"
            f = tmp_path / name
            f.write_text(f"Content of {name} for ELITEA-2467.")
            overflow_file_paths.append(str(f))
            overflow_file_names.append(name)

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 2 — Attach the 1 long-filename file alone; verify its "
            "name genuinely visually truncates"
        ):
            chat.attach_files_via_menu(str(long_file_path), timeout=UI_ELEMENT_TIMEOUT)
            chat.close_plus_menu_popper()
            chat.wait_for_attachment_chip_count(1)

            facts = chat.get_attachment_chip_name_overflow_facts(0)
            assert facts["scrollWidth"] > facts["clientWidth"], (
                "Long filename chip's name should genuinely visually "
                f"truncate (scrollWidth > clientWidth), got {facts!r}"
            )

        with allure.step(
            "Step 3 — In a fresh attach state, attach 7 distinct files; "
            "verify 4 render as visible chips and the overflow button "
            "shows '+3'"
        ):
            chat.remove_attachment_chip(0)
            chat.wait_for_attachment_chip_count(0)

            chat.attach_files_via_menu(overflow_file_paths, timeout=UI_ELEMENT_TIMEOUT)
            chat.close_plus_menu_popper()
            chat.wait_for_attachment_chip_count(4)
            overflow_count = chat.get_attachment_overflow_count()
            assert overflow_count == OVERFLOW_FILE_COUNT - 4, (
                f"Expected '+{OVERFLOW_FILE_COUNT - 4}' overflow (4 visible + "
                f"{OVERFLOW_FILE_COUNT - 4} hidden = {OVERFLOW_FILE_COUNT} total "
                f"at {VIEWPORT_WIDTH}px), got overflow count {overflow_count}"
            )

        with allure.step(
            "Step 4-5 — Click the overflow indicator; verify it genuinely "
            "expands (aria-expanded flips to 'true'), a real role='menu' "
            "element becomes visible, and it lists exactly the 3 hidden "
            "filenames, in order — a real click-to-expand control, not an "
            "inert count display"
        ):
            result = chat.open_attachment_overflow_menu_and_read(timeout=UI_ELEMENT_TIMEOUT)
            assert result["expanded_before"] != "true", (
                "Overflow button should not be expanded before the click, "
                f"got {result['expanded_before']!r}"
            )
            assert result["expanded_after"] == "true", (
                "Overflow button's aria-expanded should flip to 'true' "
                f"after the click, got {result['expanded_after']!r}"
            )
            assert result["menu_visible"] is True, (
                "Clicking the overflow indicator should open a visible "
                f"menu, got menu_visible={result['menu_visible']!r}"
            )
            assert result["menu_role"] == "menu", (
                "The opened overflow control should be a real MUI menu "
                f"(role='menu'), got role={result['menu_role']!r}"
            )
            expected_hidden = overflow_file_names[4:]
            assert result["names"] == expected_hidden, (
                f"Expected hidden filenames {expected_hidden!r} in order, "
                f"got {result['names']!r}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
