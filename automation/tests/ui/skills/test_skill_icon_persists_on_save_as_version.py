"""Skill custom icon persistence on Save As Version (ELITEA-2606).

Creates a dedicated, uniquely-named disposable skill with a distinctive
custom icon (full-UI setup — steps 1-3 are literal case actions, not pure
fixture setup), uses "Save As Version" to create a second version (``v2``),
and confirms:

  1. The create-version network response's ``meta.icon_meta.url`` is
     byte-identical to the uploaded icon's DOM ``src`` — the authoritative
     server-side proof the backend copies the base version's icon into the
     new version at creation time, not a client-side carryover artifact.
  2. The custom icon is displayed on the new version, both immediately
     after creation AND after a full page reload (rules out "looks
     preserved because client state carried over" as a false pass).
  3. The base version's icon is unaffected by creating ``v2``.
  4. The icon stays consistent across a base -> v2 -> base -> v2 round trip
     (three-way DOM ``src`` match plus the response-body match).

No product/visual defect — confirmed live during AFS analysis. Case-text
disposition (reverse-masking guard, not a defect — see AFS Coverage Map):
step 6 ("Optionally modify the instructions") is a genuine no-op for THIS
case's pass criterion (icon persistence is independent of an instructions
edit, and an explicit instructions-edit action would duplicate
ELITEA-2431's coverage) — skipped per the AFS's explicit "out-of-scope"
disposition, not silently dropped.

New page-object method: ``SkillDetailPage.confirm_create_version_capturing_
response()`` (additive — ``save_as_version()`` itself is untouched, it has
5+ existing callers) — lets this test verify the "Create version" dialog
opening and the Name field as their OWN case steps (4/5) via the already-
public ``create_version_dialog``/``create_version_name_input_field``
locators, then confirm while capturing the create-version POST response for
step 7's server-side assertion.

Spec: test-specs/skills/l3_skill-custom-icon-persistence-on-save-as-version_ELITEA-2606.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest
from components.mui import Dialog
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

# Reuses the existing repo test-icon asset (already added for ELITEA-2602/2604,
# also reused by ELITEA-2605) — distinctive, well under the 500KB limit. No new
# test data file needed.
ICON_FILE = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)

NEW_VERSION_NAME = "v2"


class TestSkillIconPersistsOnSaveAsVersion:
    """Skill custom icon persistence on Save As Version (ELITEA-2606, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2606_skill-custom-icon-persistence-on-save-as-version.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_skill_custom_icon_persists_on_save_as_version(self, page, skill_api):
        """Create a skill with a custom icon, Save As Version, and verify the
        SAME icon persists on both the new version and the original base
        version, in both directions of a version switch.

        Steps (AFS
        test-specs/skills/l3_skill-custom-icon-persistence-on-save-as-version_ELITEA-2606.md):
        1. Create a skill with a distinctive custom icon.
        2. Fill required fields and save.
        3. Verify the custom icon is displayed (base version).
        4. Click "Save As Version" — verify the "Create version" dialog appears.
        5. Enter a new version name ("v2") — verify Save becomes enabled.
        6. (Optionally modify instructions — SKIPPED, out-of-scope per AFS.)
        7. Save the new version — verify toast + create-version POST 201 +
           response body's meta.icon_meta matches the uploaded icon.
        8. Verify the new version is now active/selected.
        9. Verify the custom icon on the new version, before AND after reload.
        10. Switch back to the base version.
        11. Verify the custom icon is still present on the base version.
        12. Switch to v2 again.
        13. Verify both versions share the same custom icon (3rd confirmation).
        """
        unique_suffix = int(time.time())
        skill_name = f"el-2606-version-icon-{unique_suffix}"[:32]

        skill_id = None
        console_errors = None  # CapturedConsoleMessages, needs stop() in finally

        try:
            with allure.step(
                "Step 1 — Create a skill with a distinctive custom icon"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                console_errors = form_page.capture_console_errors()

                form_page.upload_skill_icon(ICON_FILE, timeout=UI_ELEMENT_TIMEOUT)
                uploaded_icon_src = form_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert uploaded_icon_src, (
                    "Skill form icon avatar should show the uploaded image "
                    "(non-empty img src) after upload"
                )

            with allure.step("Step 2 — Fill in all required fields and save"):
                form_page.fill_form(
                    name=skill_name,
                    instructions=(
                        "You are a helper skill created for ELITEA-2606 "
                        "version-icon persistence verification. Respond with VERICONSKILL."
                    ),
                    description="ELITEA-2606 version-icon persistence verification skill.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                logger.info("Created skill %r id=%d", skill_name, skill_id)

            with allure.step(
                "Step 3 — Verify the custom icon is displayed on the base version"
            ):
                base_icon_src = detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert base_icon_src == uploaded_icon_src, (
                    "Base version icon src should match the uploaded icon's src; "
                    f"expected {uploaded_icon_src!r}, got {base_icon_src!r}"
                )

            with allure.step(
                'Step 4 — Click "Save As Version"; verify the "Create version" dialog appears'
            ):
                detail_page.save_as_version_button.click()
                detail_page.create_version_dialog.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                dialog_title = Dialog.get_title(detail_page.create_version_dialog)
                assert dialog_title == "Create version", (
                    f"Expected the 'Create version' dialog heading, got: {dialog_title!r}"
                )

            with allure.step(
                "Step 5 — Enter a new version name ('v2'); verify Save becomes enabled"
            ):
                detail_page.create_version_name_input_field.click()
                detail_page.create_version_name_input_field.type(NEW_VERSION_NAME)
                assert (
                    detail_page.create_version_name_input_field.input_value()
                    == NEW_VERSION_NAME
                ), "Create-version Name field should hold the entered version name"
                expect(detail_page.create_version_save_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Optionally modify the instructions (SKIPPED — no "
                "icon-persistence signal for this case; AFS Coverage Map "
                "disposition: out-of-scope, duplicates ELITEA-2431)"
            ):
                logger.info(
                    "Step 6 intentionally not exercised — instructions left "
                    "unmodified; icon persistence is independent of whether "
                    "instructions change (AFS scope note)"
                )

            with allure.step(
                "Step 7 — Save the new version; verify toast + create-version "
                "POST 201 + response body's icon metadata"
            ):
                version_response = detail_page.confirm_create_version_capturing_response(
                    NEW_VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert version_response.status == 201, (
                    "Expected 201 Created from the create-version POST, got "
                    f"{version_response.status}"
                )
                version_body = version_response.json()
                new_version_id = version_body.get("id")
                assert new_version_id, (
                    f"Expected a numeric id in the create-version response body: {version_body}"
                )
                response_icon_url = (version_body.get("meta") or {}).get("icon_meta", {}).get(
                    "url"
                )
                assert response_icon_url == uploaded_icon_src, (
                    "create-version response meta.icon_meta.url should match the "
                    f"uploaded icon's src; expected {uploaded_icon_src!r}, got "
                    f"{response_icon_url!r}"
                )

            with allure.step("Step 8 — Verify the new version is now active/selected"):
                assert detail_page.get_version_selector_value() == NEW_VERSION_NAME, (
                    "VERSION selector should display the newly created version"
                )
                assert detail_page.get_version_id() == str(new_version_id), (
                    "URL's trailing version-id segment should equal the "
                    f"create-version response's id ({new_version_id})"
                )

            with allure.step(
                "Step 9 — Verify the custom icon is displayed on the new "
                "version, before AND after a full page reload"
            ):
                v2_icon_src_live = detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert v2_icon_src_live == uploaded_icon_src, (
                    "New version icon src (pre-reload) should match the uploaded "
                    f"icon's src; expected {uploaded_icon_src!r}, got {v2_icon_src_live!r}"
                )

                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                v2_icon_src_reloaded = detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert v2_icon_src_reloaded == uploaded_icon_src, (
                    "New version icon src (post-reload, server-fetched) should "
                    f"match the uploaded icon's src; expected {uploaded_icon_src!r}, "
                    f"got {v2_icon_src_reloaded!r}"
                )

            with allure.step("Step 10 — Switch back to the base version"):
                detail_page.switch_version("base")
                assert detail_page.get_version_selector_value() == "base", (
                    "VERSION selector should display 'base' after switching back"
                )
                # NOTE: base's own explicit version-id (once selected via the
                # dropdown) does NOT equal the skill id — confirmed live this
                # run (skill 1511, base's explicit version-id 1572) — so we
                # only assert we're still on the SAME skill, not a specific
                # version-id number. switch_version() itself already polls
                # the selector text to convergence before returning.
                assert detail_page.get_skill_id() == str(skill_id), (
                    "Should still be on the same skill after switching to base"
                )

            with allure.step(
                "Step 11 — Verify the custom icon is still present on the base version"
            ):
                base_icon_src_after_switch = detail_page.get_form_icon_src(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert base_icon_src_after_switch == uploaded_icon_src, (
                    "Base version icon src should be unaffected by creating v2; "
                    f"expected {uploaded_icon_src!r}, got {base_icon_src_after_switch!r}"
                )

            with allure.step("Step 12 — Switch to v2 again"):
                detail_page.switch_version(NEW_VERSION_NAME)
                assert detail_page.get_version_selector_value() == NEW_VERSION_NAME, (
                    "VERSION selector should display 'v2' after switching back to it"
                )
                assert detail_page.get_version_id() == str(new_version_id), (
                    "v2's URL version-id segment should equal the create-version "
                    "response's id"
                )

            with allure.step(
                "Step 13 — Verify both versions share the same custom icon "
                "(third confirmation across the full switch round trip)"
            ):
                v2_icon_src_again = detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert v2_icon_src_again == uploaded_icon_src, (
                    "v2 icon src (after the base->v2 round trip) should match "
                    f"the uploaded icon's src; expected {uploaded_icon_src!r}, got "
                    f"{v2_icon_src_again!r}"
                )
                all_reads = {
                    uploaded_icon_src,
                    base_icon_src,
                    response_icon_url,
                    v2_icon_src_live,
                    v2_icon_src_reloaded,
                    base_icon_src_after_switch,
                    v2_icon_src_again,
                }
                assert len(all_reads) == 1, (
                    "All icon reads across upload/base/create-response/v2/reload/"
                    f"switch-back/switch-again should be byte-identical, got: {all_reads}"
                )

            with allure.step(
                "Verify zero console errors across the full create->upload->save->"
                "Save-As-Version->switch-base->switch-v2 flow"
            ):
                assert not console_errors, (
                    f"Unexpected console errors during the flow: "
                    f"{[m.text for m in console_errors]}"
                )

        finally:
            if console_errors is not None:
                console_errors.stop()
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
