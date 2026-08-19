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

Usage:
    cd automation
    pytest tests/ui/chat/test_attach_files_multiple_chips_display.py -v
"""

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
