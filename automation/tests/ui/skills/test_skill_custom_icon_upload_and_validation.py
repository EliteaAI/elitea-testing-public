"""Skill custom icon upload and validation (ELITEA-2604).

Creates a dedicated, uniquely-named disposable skill (icon state is a
visible, list/mention-affecting mutation — per this project's Hard Rule 10
test-data guidance, same reasoning as the ELITEA-1899/ELITEA-2602 icon
AFSes) and exercises the full icon lifecycle end-to-end:

  Part A — upload a valid PNG icon DURING creation, save, reopen (reload)
           and verify server-side persistence.
  Part B — replace the icon in EDIT mode across three more formats
           (GIF/WEBP/JPG); edit-mode replace fires a distinct POST+PUT
           network pair instead of create mode's single POST (AFS step 8's
           finding) — asserted on the network response pair, not a
           toast-text match.
  Part C — attempt an oversized (>512KB) upload; verify the server-side
           400 rejection (exact error body), the app-wide error toast, and
           that the previously-set icon is retained (upload failure does
           NOT clear the current icon).
  Part D — revert to the default icon via the icon picker's "Default"
           tile (AFS step 17, mechanism (b) — the case's own "delete/remove
           option" wording is satisfied by either of the AFS's two
           documented mechanisms; mechanism (a), deleting the currently-
           selected uploaded icon via its hover-revealed delete button, was
           tried first but is unreliable in THIS test's exact usage pattern
           — confirmed live that the "Uploaded" gallery's infinite-scroll
           loader gets permanently stuck after the mutations Parts B/C
           already fire, filed as EliteaAI/elitea-testing-public#1459).
           Verify the icon reverts to the default (absent-<img>) state and
           that this persists across a full page reload.

Case-text CLARIFICATIONs (reverse-masking guard, not defects — see AFS
Coverage Map / Known Defects):
  - Steps 10/20 ("Save the skill"): no literal Save click needed — the
    icon persists independently via its own network call the instant it's
    applied (icon is not formik-tracked); Save stays DISABLED throughout.
    Same pattern as ELITEA-1899's Agent-icon AFS.
  - Step 19 ("reverts to default skill-icon.svg"): the live product's
    default state is an ABSENT <img> element (an inline SVG placeholder
    rendered by EntityTypeIcon), never a literal "skill-icon.svg" asset —
    asserted via ``get_form_icon_src() == ""``, same convention as
    ELITEA-1899.

One new testid added for this case (none existed before):
``agent-icon-picker-uploaded-{index}-delete-button`` — UserIconItem.jsx's
per-uploaded-icon delete IconButton carried zero data-testid at analysis
time; forwarded via a new ``deleteButtonTestId`` prop from
SelectIconDialog.jsx's per-item call site (EliteaAI/EliteaUI@1553565f).
Landed in EliteaUI source but NOT exercised by this test — see Part D note
above (EliteaAI/elitea-testing-public#1459); left in place for a future
case once that gallery bug is fixed.

Spec: test-specs/skills/l2_skill-custom-icon-upload-and-validation_ELITEA-2604.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest

from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

logger = logging.getLogger("elitea.tests.skills")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

_IMAGES_DIR = Path(__file__).resolve().parents[4] / "test-data" / "images"
PNG_ICON = str(_IMAGES_DIR / "skill-fork-test-icon.png")
JPG_ICON = str(_IMAGES_DIR / "test-icon.jpg")
GIF_ICON = str(_IMAGES_DIR / "test-icon.gif")
WEBP_ICON = str(_IMAGES_DIR / "test-icon.webp")
OVERSIZED_ICON = str(_IMAGES_DIR / "large-icon.png")


class TestSkillCustomIconUploadAndValidation:
    """Skill custom icon upload and validation (ELITEA-2604, p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2604_skill-custom-icon-upload-and-validation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_skill_custom_icon_upload_and_validation(self, page, skill_api):
        """Full icon lifecycle: upload during creation, replace across
        formats in edit mode, reject an oversized file, delete and revert
        to default — each transition verified for server-side persistence.

        Steps (AFS
        test-specs/skills/l2_skill-custom-icon-upload-and-validation_ELITEA-2604.md):
        1-4. Create form loads; open icon picker; upload a valid PNG; preview shows it.
        5-6. Fill required fields; save.
        7. Reopen (reload); custom PNG icon persists.
        8-11. Replace with GIF in edit mode; Save stays disabled; GIF displayed.
        12. Replace with WEBP.
        13. Replace with JPG.
        14-16. Oversized upload rejected (400); error shown; previous icon retained.
        17-18. Revert to default via the icon picker's "Default" tile; confirm.
        19-20. Icon reverts to default (absent <img>); Save stays disabled.
        21. Reopen (reload); default icon still displayed.
        """
        unique_suffix = int(time.time())
        skill_name = f"el2604-icon-test-{unique_suffix}"[:32]
        skill_description = "Skill for ELITEA-2604 icon upload/validation testing"
        skill_instructions = "Instructions for ELITEA-2604 icon upload/validation testing."

        skill_id = None

        try:
            with allure.step(
                "Steps 1-4 — Navigate to Create Skill page, open the icon "
                "picker, upload a valid PNG icon, verify the preview shows it"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                assert form_page.name_input.is_visible(), (
                    "Skill create form should be loaded (Name field visible)"
                )
                assert not form_page.is_save_enabled(), (
                    "Save should be disabled before any fields are filled"
                )

                form_page.upload_skill_icon(PNG_ICON, timeout=UI_ELEMENT_TIMEOUT)
                png_src = form_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert png_src, (
                    "Skill form icon avatar should show the uploaded PNG "
                    "(non-empty img src) after upload"
                )

            with allure.step(
                "Steps 5-6 — Fill required fields (name, description, "
                "instructions) and save the skill"
            ):
                form_page.fill_form(
                    name=skill_name,
                    instructions=skill_instructions,
                    description=skill_description,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                assert detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT) == png_src, (
                    "Skill's icon on the just-saved detail page should match "
                    "the uploaded PNG"
                )
                logger.info("Created skill %r id=%s", skill_name, skill_id)

            with allure.step(
                "Step 7 — Reopen the skill (full page reload); verify the "
                "custom PNG icon is still displayed (server-side persistence)"
            ):
                page.reload()
                detail_page.wait_for_page_load()
                assert detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT) == png_src, (
                    "Custom PNG icon should persist across a full page reload"
                )

            with allure.step(
                "Steps 8-11 — Replace the icon with a GIF (edit mode); "
                "verify Save stays disabled (icon persists independently) "
                "and the GIF is displayed"
            ):
                gif_src = detail_page.upload_skill_icon_edit_mode(
                    GIF_ICON, timeout=UI_ELEMENT_TIMEOUT
                )
                assert gif_src and gif_src != png_src, (
                    "Icon src should change after replacing with the GIF"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should remain disabled after an icon-only edit-mode "
                    "change — the icon persists independently (no formik "
                    "tracking), same as the Agent icon flow (ELITEA-1899)"
                )

            with allure.step(
                "Step 12 — Replace the icon with a WEBP file; verify it "
                "uploads and displays correctly"
            ):
                webp_src = detail_page.upload_skill_icon_edit_mode(
                    WEBP_ICON, timeout=UI_ELEMENT_TIMEOUT
                )
                assert webp_src and webp_src != gif_src, (
                    "Icon src should change after replacing with the WEBP"
                )

            with allure.step(
                "Step 13 — Replace the icon with a JPG file; verify it "
                "uploads and displays correctly"
            ):
                jpg_src = detail_page.upload_skill_icon_edit_mode(
                    JPG_ICON, timeout=UI_ELEMENT_TIMEOUT
                )
                assert jpg_src and jpg_src != webp_src, (
                    "Icon src should change after replacing with the JPG"
                )

            with allure.step(
                "Steps 14-16 — Attempt to upload an oversized file; verify "
                "the server-side 400 rejection with the exact error toast, "
                "and that the previous (JPG) icon is retained"
            ):
                error_body = detail_page.attempt_upload_oversized_icon(
                    OVERSIZED_ICON, timeout=UI_ELEMENT_TIMEOUT
                )
                assert error_body == {"error": "File size exceeds 512 KB"}, (
                    f"Oversized-upload 400 response body should be the exact "
                    f"server error, got: {error_body!r}"
                )
                error_toast = detail_page.get_toast_alert("error")
                error_toast.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (detail_page.toast_message.text_content() or "").strip() == (
                    "File size exceeds 512 KB"
                ), "Error toast text should match the server's exact error message"
                assert detail_page.icon_picker_dialog.is_visible(), (
                    "Icon picker dialog should remain open after a failed upload"
                )
                assert detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT) == jpg_src, (
                    "Previously-set (JPG) icon should be retained, unchanged, "
                    "after a rejected oversized upload"
                )
                detail_page.icon_picker_close_button.click()
                detail_page.icon_picker_dialog.wait_for(
                    state="hidden", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Steps 17-18 — Revert the icon to the default via the icon "
                "picker's 'Default' tile (mechanism (b) — see AFS step 17; "
                "mechanism (a)'s hover-revealed delete button is unreliable "
                "here due to a confirmed 'Uploaded' gallery infinite-scroll "
                "bug, EliteaAI/elitea-testing-public#1459)"
            ):
                reverted_src = detail_page.select_default_icon_tile(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Steps 19-20 — Verify the icon reverts to the default "
                "(absent <img>) state and Save stays disabled (no separate "
                "save action needed — delete already persisted server-side)"
            ):
                assert reverted_src == "", (
                    "Icon should revert to the default (absent <img>) state "
                    "after selecting the Default tile — the case's own "
                    "'skill-icon.svg' wording is case-text imprecision (see "
                    f"AFS), got src: {reverted_src!r}"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should remain disabled — the reset already "
                    "persisted server-side"
                )

            with allure.step(
                "Step 21 — Reopen the skill (full page reload); verify the "
                "default icon is STILL displayed (server-side persistence "
                "of the reverted state)"
            ):
                page.reload()
                detail_page.wait_for_page_load()
                assert detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT) == "", (
                    "Default (reverted) icon state should persist across a "
                    "full page reload — confirming server-side persistence, "
                    "not just client-side/optimistic state"
                )

        finally:
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                    )
