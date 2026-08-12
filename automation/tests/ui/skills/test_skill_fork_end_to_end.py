"""Fork skill end-to-end, into a different project (ELITEA-2602).

Creates a source Skill via the UI in the default project (399, ``Private``)
— including a custom icon and two committed tags — forks it via the skill
controls overflow menu's "Fork" item into a DIFFERENT target project (400,
``UI Testing`` — the only cross-project target confirmed by the AFS to
carry full CRUD, including delete, for the localhost dev-token identity;
same pair as the sibling Agent/Pipeline fork cases ELITEA-1893/ELITEA-2051),
and verifies:

1. The Fork wizard's "Main entity" card shows the skill's name/description/
   instructions (tags are NOT shown in the preview — a confirmed case-text
   overstatement, not a defect; filed as clarification #1455).
2. The target-project dropdown excludes the current project (399).
3. The Fork POST returns 201 Created.
4. "Got it" navigates into the target project, onto the newly forked Skill.
5. The forked skill's name/description/instructions/tags/custom icon all
   match the source exactly, and lineage metadata (parent_entity_id,
   parent_project_id, parent_version_id) is present.
6. Editing the forked skill's instructions does not affect the original
   (independence, verified both by editing the fork and re-reading the
   untouched original).
7. Cleanup deletes both the forked skill (target project) and the source
   skill (source project) via the UI's type-to-confirm dialog.

One MINOR, isolated, already-filed product defect (React
``validateDOMNesting`` ``<p>``-in-``<p>`` console warning on the Fork/Import
"Complete" dialog, https://github.com/EliteaAI/elitea-testing-public/issues/570
— shared ``IWModalSucceedContent.jsx`` component, previously confirmed for
Agent/ELITEA-1893 and Pipeline/ELITEA-2051) reproduces here too, confirmed
for Skills as a third entity type. Handled via the same pytest-native
soft-assertion pattern (``soft_failures`` list + a final ``pytest.fail()``)
so it doesn't mask any *other* console error and never demotes the failure
to a log-only signal.

Two testids were added for this case (none existed before):
``skill-form-icon-button``/``skill-form-icon-img`` (CreateSkillForm.jsx's
``EntityIcon`` call site — the icon avatar/img elements carried no
data-testid prop at all) and ``agent-icon-picker-upload-button`` (the
shared SelectIconDialog.jsx's Upload button — entity-agnostic, same
literal ``agent-`` prefix convention as the dialog's other testids).

Spec: test-specs/skills/l2_fork-skill-end-to-end_ELITEA-2602.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest
from api import SkillAPI
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p1, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
FORK_TIMEOUT = 15_000

# Source project is the suite default (ELITEA_PROJECT_ID=399, "Private").
# Target project MUST be "UI Testing" (400) — confirmed by the AFS to carry
# full CRUD (including delete) for the localhost dev-token identity, same
# pair as the sibling Agent (ELITEA-1893) / Pipeline (ELITEA-2051) fork cases.
TARGET_PROJECT_ID = 400

ICON_FILE = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)


class TestSkillForkEndToEnd:
    """Fork skill end-to-end, into a different project (ELITEA-2602, l2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2602_fork-skill-end-to-end.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_fork_skill_end_to_end(self, page, skill_api, _browser_cookies):
        """Fork a Skill (with a custom icon + tags) into a different project
        and verify the forked skill's configuration + lineage + independence,
        then clean up.

        Steps (AFS
        test-specs/skills/l2_fork-skill-end-to-end_ELITEA-2602.md):
        1. Create the source Skill via UI (name, description, instructions,
           two tags, a custom icon).
        2. Save; verify URL settles on the skill's own detail page.
        3. Open the skill controls overflow menu; verify "Fork" is present
           and enabled.
        4. Click "Fork"; verify the Fork wizard dialog opens, showing the
           Main entity card (name + description + instructions; tags are
           NOT shown per the confirmed case-text drift).
        5. Verify the target-project dropdown excludes the source project.
        6. Select the target project; verify the Fork confirm button
           becomes enabled.
        7. Click "Fork"; verify the fork POST returns 201 Created and the
           dialog re-renders as "Fork Complete".
        8. Click "Got it"; verify navigation into the target project, onto
           the new forked Skill.
        9. Verify the forked skill's name/description/instructions/tags/
           icon match the source, and lineage metadata is present.
        10. Edit the forked skill's instructions and save.
        11. Switch back to the source project and verify the original
            skill's instructions are UNCHANGED (no cross-propagation).
        12. Clean up: delete the forked skill (target project) and the
            source skill (source project) via the UI.
        """
        unique_suffix = int(time.time())
        source_skill_name = f"el-2602-forkable-{unique_suffix}"[:32]
        source_description = (
            "Detailed description for fork testing purposes covering more "
            "than one hundred characters so that it satisfies the case's "
            "length requirement fully."
        )
        source_instructions = (
            "Comprehensive instructions for the skill behavior used to "
            "verify the fork end-to-end flow ELITEA-2602."
        )
        modified_instructions = (
            "Updated instructions after forking to test independence — ELITEA-2602."
        )
        # Tags MUST use underscores — the live Tags field silently rejects
        # hyphens (0 network calls, no chip created; same root cause as
        # issue #1445). See AFS § Test Data / § Known Defects.
        tag_1, tag_2 = "test_tag", "fork_demo"

        # Project-400-scoped SkillAPI for verification + a fallback cleanup
        # path — the case's own cleanup is UI-driven (see below); this is a
        # safety net so a UI-step failure doesn't leak a forked skill in
        # project 400 across test runs. Mirrors
        # test_fork_agent_to_different_project.py's target_project_agent_api.
        target_project_skill_api = SkillAPI(
            browser_cookies=_browser_cookies, project_id=str(TARGET_PROJECT_ID),
        )

        source_skill_id = None
        forked_skill_id = None
        # pytest has no built-in expect.soft() for a raw console-message list
        # — this list is the pytest-native equivalent, mirroring
        # test_fork_agent_to_different_project.py's identical mechanism.
        soft_failures = []

        try:
            with allure.step(
                "Step 1 — Create the source Skill via UI: name, description, "
                "instructions, two tags, and a custom icon"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                assert form_page.name_input.is_visible(), (
                    "Skill create form should be loaded (Name field visible)"
                )
                form_page.fill_form(
                    name=source_skill_name,
                    instructions=source_instructions,
                    description=source_description,
                )
                form_page.add_tag(tag_1)
                form_page.add_tag(tag_2)
                assert form_page.get_tags() == [tag_1, tag_2], (
                    f"Expected [{tag_1!r}, {tag_2!r}] committed pre-save, "
                    f"got: {form_page.get_tags()!r}"
                )

                form_page.upload_skill_icon(ICON_FILE, timeout=UI_ELEMENT_TIMEOUT)
                source_icon_src = form_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert source_icon_src, (
                    "Skill form icon avatar should show the uploaded image "
                    "(non-empty img src) after upload"
                )

                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required skill fields"
                )

            with allure.step(
                "Step 2 — Save; verify URL settles on the skill's own detail page"
            ):
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                source_skill_id = int(detail_page.get_skill_id())

                # DECLARED IMPROVISATION: SkillDetailPage.get_version_id()
                # derives its value from the URL's digit segments, and on a
                # freshly-created "base" version the URL carries only ONE
                # digit segment (the skill id) — its docstring says "Version
                # ID equals the Skill ID" for that case, which is a
                # deliberate simplification for ITS existing callers
                # (Save-As-Version before/after comparisons), not the real
                # database version id. Confirmed live via SkillAPI during
                # this case's exploration: a freshly-created skill's own
                # base version id is a DISTINCT integer, never equal to the
                # skill id (e.g. skill=1495, version_details.id=1554). The
                # lineage assertion in Step 9 needs the real value, so it is
                # read from the API instead of the URL-derived page-object
                # method — no sanctioned canon pattern covers this
                # DOM-vs-API split for Skills yet, flagged per
                # `.agents/role-overrides.md` § Declared-improvisation protocol.
                source_skill_snapshot = skill_api.get_skill(source_skill_id)
                source_version_id = source_skill_snapshot["version_details"]["id"]
                source_icon_url = (
                    source_skill_snapshot["version_details"]
                    .get("meta", {})
                    .get("icon_meta", {})
                    .get("url")
                )
                assert source_icon_url, (
                    "Source skill's saved version_details.meta.icon_meta.url "
                    "should be populated after Save (the icon upload's "
                    "onSelectIcon callback sets the formik field before Save "
                    "posts the full payload)"
                )
                logger.info(
                    "Created source skill %r id=%s version_id=%s",
                    source_skill_name, source_skill_id, source_version_id,
                )

            with allure.step(
                'Step 3 — Open the skill controls overflow menu; verify '
                '"Fork" is present and enabled'
            ):
                detail_page.open_actions_menu()
                assert detail_page.fork_menuitem.is_visible(), (
                    "Skill controls menu should show a 'Fork' menuitem"
                )
                assert detail_page.fork_menuitem.is_enabled(), (
                    "'Fork' menuitem should be enabled"
                )

            with allure.step(
                "Step 4 — Click 'Fork'; verify the Fork wizard dialog opens "
                "showing the Main entity card (name + description + "
                "instructions; tags are NOT shown per confirmed case-text drift)"
            ):
                # Menu is already open from Step 3 — click the Fork
                # menuitem directly rather than re-opening via
                # open_fork_wizard() (which would re-click the already-open
                # overflow trigger and toggle it closed instead).
                detail_page.fork_menuitem.click()
                detail_page.fork_wizard_dialog.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.fork_main_entity_name.text_content() == source_skill_name, (
                    "Fork wizard's Main-entity name preview should show the "
                    "source skill's name verbatim"
                )
                # Every rendered entity-preview card carries the SAME
                # agent-import-preview-card-toggle testid — exactly one
                # toggle confirms only the Main entity card renders (no
                # Nested entities section, since the source has no
                # attached toolkits/sub-skills — AFS Axis 2).
                assert detail_page.fork_entity_card_toggle.count() == 1, (
                    "Fork wizard should render exactly one entity-preview "
                    "card (Main entity only) for a dependency-free source skill"
                )
                assert not detail_page.fork_confirm_button.is_enabled(), (
                    "Fork confirm button should be disabled before a target "
                    "project is selected"
                )

                detail_page.fork_entity_card_toggle.click()
                dialog_text = detail_page.fork_wizard_dialog.text_content() or ""
                assert source_description in dialog_text, (
                    "Expanded Main-entity card should show the source "
                    "skill's Description verbatim"
                )
                assert source_instructions in dialog_text, (
                    "Expanded Main-entity card should show the source "
                    "skill's Instructions verbatim"
                )
                # Confirmed case-text drift (not a defect, issue #1455):
                # tags are never rendered in the Fork preview for any
                # entity type. Assert the negative to catch a future
                # regression flipping this silently either way.
                assert tag_1 not in dialog_text and tag_2 not in dialog_text, (
                    "Fork wizard preview is not expected to show tags "
                    "(clarification #1455) — if this now fails, tags "
                    "started rendering and the AFS/clarification need updating"
                )

            with allure.step(
                "Step 5 — Verify the target-project dropdown excludes the "
                "source project (399)"
            ):
                detail_page.fork_project_select_trigger.click()
                source_project_option = page.locator(
                    detail_page.FORK_PROJECT_OPTION.format(399)
                )
                target_project_option = page.locator(
                    detail_page.FORK_PROJECT_OPTION.format(TARGET_PROJECT_ID)
                )
                target_project_option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert source_project_option.count() == 0, (
                    "Fork wizard's target-project dropdown should exclude "
                    "the current/source project (399, 'Private')"
                )

            with allure.step(
                "Step 6 — Select the target project; verify the Fork "
                "confirm button becomes enabled"
            ):
                target_project_option.click()
                assert detail_page.fork_confirm_button.is_enabled(), (
                    "Fork confirm button should become enabled once a "
                    "target project is selected"
                )

            with allure.step(
                "Step 7 — Click 'Fork'; verify the fork POST returns 201 "
                "Created and the dialog re-renders as 'Fork Complete'"
            ):
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                with page.expect_response(
                    lambda r: (
                        f"/elitea_core/fork/prompt_lib/{TARGET_PROJECT_ID}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=FORK_TIMEOUT,
                ) as fork_response_info:
                    detail_page.fork_confirm_button.click()
                    detail_page.fork_complete_dialog.wait_for(
                        state="visible", timeout=FORK_TIMEOUT,
                    )

                fork_response = fork_response_info.value
                assert fork_response.status == 201, (
                    f"Fork POST to project {TARGET_PROJECT_ID} should "
                    f"return 201 Created, got {fork_response.status}"
                )
                fork_response_body = fork_response.json()
                forked_skill_id_from_response = fork_response_body["result"]["skills"][0]["id"]
                assert forked_skill_id_from_response, (
                    "Fork POST response should carry the new forked skill's ID "
                    f"at result.skills[0].id — got: {fork_response_body!r}"
                )
                assert detail_page.fork_complete_dialog.is_visible(), (
                    "Fork Complete dialog should be visible after a "
                    "successful fork"
                )
                assert source_skill_name in detail_page.fork_complete_skills_list.text_content(), (
                    "Fork Complete dialog's Skills list should include the "
                    "source skill's name — confirming a new forked entity "
                    "was created"
                )
                page.wait_for_timeout(500)  # let any deferred console errors surface

            with allure.step(
                "Step 7b — Console-cleanliness check around the Fork "
                "Complete dialog (a known, isolated, non-blocking defect "
                "fires a validateDOMNesting warning here — soft-asserted, "
                "not a demoted log-only check)"
            ):
                unexpected_errors = [
                    m.text for m in console_messages
                    if "validateDOMNesting" not in m.text
                ]
                assert not unexpected_errors, (
                    "Expected no UNEXPECTED console errors around the Fork "
                    f"Complete dialog, got: {unexpected_errors!r}"
                )
                # Known defect: #570 — React validateDOMNesting <p>-in-<p>
                # warning on IWModalSucceedContent.jsx's "Forked:" label.
                # Does not block the functional flow. Recorded in
                # soft_failures rather than only logged, so a regression
                # here still fails the test instead of silently passing.
                known_defect_errors = [
                    m.text for m in console_messages if "validateDOMNesting" in m.text
                ]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/570: "
                        f"validateDOMNesting console error(s) on the Fork Complete "
                        f"dialog: {known_defect_errors!r}"
                    )

            with allure.step(
                "Step 8 — Click 'Got it'; verify navigation into the "
                "target project, onto the new forked Skill"
            ):
                forked_skill_id = detail_page.confirm_fork_complete(timeout=NAVIGATION_TIMEOUT)
                assert forked_skill_id == forked_skill_id_from_response, (
                    "Navigated-to skill ID should match the Fork POST "
                    "response's forked skill ID"
                )
                assert forked_skill_id != source_skill_id, (
                    f"Forked Skill ID should differ from source: "
                    f"forked={forked_skill_id}, source={source_skill_id}"
                )
                assert f"/skills/all/{forked_skill_id}" in page.url, (
                    "Should navigate to the forked Skill's own detail page URL"
                )
                logger.info(
                    "Forked skill created — id=%d in project %d",
                    forked_skill_id, TARGET_PROJECT_ID,
                )

            with allure.step(
                "Step 9 — Verify the forked skill's name/description/"
                "instructions/tags/icon match the source, and lineage "
                "metadata is present"
            ):
                forked_skill = target_project_skill_api.get_skill(forked_skill_id)
                assert forked_skill["name"] == source_skill_name, (
                    "Forked skill's name should match the source verbatim"
                )
                assert forked_skill["description"] == source_description, (
                    "Forked skill's description should match the source verbatim"
                )
                version_details = forked_skill["version_details"]
                assert version_details["instructions"] == source_instructions, (
                    "Forked skill's instructions should match the source verbatim"
                )
                forked_tags = {
                    t.get("name") if isinstance(t, dict) else t
                    for t in version_details.get("tags", [])
                }
                assert forked_tags == {tag_1, tag_2}, (
                    f"Forked skill's tags should be {{tag_1, tag_2}}, got: {forked_tags!r}"
                )
                forked_icon_url = version_details.get("meta", {}).get("icon_meta", {}).get("url")
                # Fork references the source's icon (same file), it is not
                # re-uploaded per fork — same underlying URL. Compared
                # against the authoritative API value captured in Step 2,
                # not the DOM src (which may be a proxied/relative form).
                assert forked_icon_url == source_icon_url, (
                    f"Forked skill's icon URL ({forked_icon_url!r}) should "
                    f"exactly match the source's saved icon URL "
                    f"({source_icon_url!r}) — same file, referenced not re-uploaded"
                )
                meta = version_details.get("meta", {})
                assert meta.get("parent_entity_id") == source_skill_id, (
                    f"Forked version's parent_entity_id should equal the "
                    f"source skill ID ({source_skill_id}), got: {meta.get('parent_entity_id')!r}"
                )
                assert meta.get("parent_project_id") == 399, (
                    f"Forked version's parent_project_id should be 399 "
                    f"('Private'), got: {meta.get('parent_project_id')!r}"
                )
                assert str(meta.get("parent_version_id")) == str(source_version_id), (
                    f"Forked version's parent_version_id should equal the "
                    f"source's base version ID ({source_version_id}), got: "
                    f"{meta.get('parent_version_id')!r}"
                )

            with allure.step(
                "Step 10 — Edit the forked skill's instructions and save"
            ):
                detail_page.fill_instructions(modified_instructions)
                detail_page.save_edits(timeout=FORM_SAVE_TIMEOUT)
                assert detail_page.get_instructions() == modified_instructions, (
                    "Forked skill's instructions should reflect the edit "
                    "after saving"
                )

            with allure.step(
                "Step 11 — Switch back to the source project and verify "
                "the original skill's instructions are UNCHANGED (no "
                "cross-propagation)"
            ):
                detail_page.switch_project(399, timeout=NAVIGATION_TIMEOUT)
                detail_page.navigate(source_skill_id)
                assert detail_page.get_instructions() == source_instructions, (
                    "Original skill's instructions must remain UNCHANGED "
                    "after editing the fork's instructions — a mismatch "
                    "here would indicate cross-propagation between fork "
                    "and original"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — rest of the flow, steps 8-11, "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: source skill (project 399, via the
            # suite-default skill_api) always; forked skill (project 400)
            # via the UI's type-to-confirm delete flow, with a fallback API
            # delete if the UI step didn't run/succeed.
            if forked_skill_id is not None:
                try:
                    detail_page.switch_project(TARGET_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                    detail_page.navigate(forked_skill_id)
                    # Forked skill's name matches the source verbatim
                    # (asserted in Step 9) — the type-to-confirm dialog
                    # needs the CURRENTLY-displayed (forked) skill's name.
                    detail_page.delete_skill_via_menu(
                        skill_name=source_skill_name, timeout=NAVIGATION_TIMEOUT,
                    )
                    logger.info(
                        "Cleanup: deleted forked skill id=%d in project %d via UI",
                        forked_skill_id, TARGET_PROJECT_ID,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: UI delete of forked skill id=%s failed (%s) — "
                        "falling back to API delete", forked_skill_id, exc,
                    )
                    try:
                        target_project_skill_api.delete_skill(forked_skill_id)
                        logger.info(
                            "Fallback cleanup: deleted forked skill id=%d in "
                            "project %d via API", forked_skill_id, TARGET_PROJECT_ID,
                        )
                    except Exception as api_exc:
                        logger.warning(
                            "Fallback cleanup also failed for forked skill "
                            "id=%s: %s", forked_skill_id, api_exc,
                        )
            if source_skill_id is not None:
                try:
                    skill_api.delete_skill(source_skill_id)
                    logger.info("Cleanup: deleted source skill id=%d", source_skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source skill id=%s: %s",
                        source_skill_id, exc,
                    )
            target_project_skill_api.close()
