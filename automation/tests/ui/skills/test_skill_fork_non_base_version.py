"""Fork a non-base Skill version, into a different project (ELITEA-2603).

Creates a source Skill via the API (base version), creates a second
version ("v2-enhanced") with different instructions/tags via the UI, then
forks the skill WHILE the v2-enhanced version is active — verifying the
Fork wizard preview shows the v2-enhanced version's own content (not
base's), and that the forked skill in the target project:

1. Has exactly ONE version, named "base" (normalized regardless of which
   source version was forked — the case's central assertion).
2. Carries the v2-enhanced version's specific instructions and tags, NOT
   the original base version's.
3. Has ``meta.parent_version_id`` pointing at the SOURCE's v2-enhanced
   version id (not its base version id) — the strongest possible proof the
   backend captured the version-specific export rather than defaulting to
   base internally.

Shares the Fork-wizard/project-switch page-object methods
(``SkillDetailPage.open_fork_wizard`` / ``select_fork_target_project`` /
``confirm_fork`` / ``confirm_fork_complete``) with the sibling case
ELITEA-2602 (Fork Skill End-to-End) — see that spec's Concrete Handles /
Automation Hints for the shared mechanics; this file only covers what's
version-specific.

Test case: ELITEA-2603
AFS: test-specs/skills/l3_fork-non-base-skill-version_ELITEA-2603.md
"""

import logging
import time

import allure
import pytest
from api import SkillAPI
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

logger = logging.getLogger("elitea.tests.skills")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORK_TIMEOUT = 15_000

# Same source/target project pair as the sibling ELITEA-2602 case.
TARGET_PROJECT_ID = 400


class TestSkillForkNonBaseVersion:
    """Fork a non-base skill version, into a different project (ELITEA-2603, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2603_fork-non-base-skill-version.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_fork_non_base_skill_version(self, page, skill_api, _browser_cookies):
        """Create a second skill version with distinct content, fork it
        while active, and verify the forked copy carries THAT version's
        content — normalized to version name "base" in the target project.

        Steps (AFS
        test-specs/skills/l3_fork-non-base-skill-version_ELITEA-2603.md):
        1. Create the source Skill via API (precondition — base version).
        2. On the skill's detail page, edit instructions + tags to the
           "v2-enhanced" test data — BEFORE clicking Save As Version.
        3. Click "Save As Version"; verify a new version is created and
           becomes active.
        4. Verify the VERSION dropdown lists both "base" and "v2-enhanced".
        5. Open the overflow menu and click "Fork"; verify the wizard opens.
        6. Expand the Main entity card; verify it shows the v2-enhanced
           version's instructions (not base's).
        7. Select the target project; complete the fork.
        8. Click "Got it"; verify navigation into the target project.
        9. Verify the forked skill has exactly one version named "base",
           carrying the v2-enhanced version's instructions/tags, with
           ``parent_version_id`` pointing at the source's v2-enhanced
           version id (not its base version id).
        10. Clean up: delete the forked skill and the source skill.
        """
        unique_suffix = int(time.time())
        source_skill_name = f"el-2603-versioned-{unique_suffix}"[:32]
        base_instructions = (
            "Comprehensive instructions for the skill behavior used to "
            "verify the fork end-to-end flow — ELITEA-2603 base version."
        )
        v2_version_name = "v2-enhanced"  # hyphen IS accepted here (Create Version dialog)
        v2_instructions = (
            "Enhanced instructions with additional capabilities for the "
            "v2-enhanced version — ELITEA-2603."
        )
        # Tags MUST use underscores — same silent-hyphen-rejection root
        # cause as ELITEA-2602 (issue #1445). "enhanced" has no hyphen and
        # would work as literally specified, but v2_tag replaces v2-tag.
        v2_tag_1, v2_tag_2 = "v2_tag", "enhanced"

        target_project_skill_api = SkillAPI(
            browser_cookies=_browser_cookies, project_id=str(TARGET_PROJECT_ID),
        )

        source_skill_id = None
        forked_skill_id = None
        soft_failures = []

        try:
            with allure.step(
                "Step 1 — Create the source Skill via API (base version)"
            ):
                created = skill_api.create_skill(
                    name=source_skill_name,
                    description="Autotest skill for ELITEA-2603 non-base-version fork.",
                    instructions=base_instructions,
                )
                source_skill_id = created["id"]
                assert created["version_details"]["name"] == "base", (
                    "Freshly-created skill should have a 'base' version"
                )
                source_base_version_id = created["version_details"]["id"]
                logger.info(
                    "Created source skill id=%s base_version_id=%s",
                    source_skill_id, source_base_version_id,
                )

                detail_page = SkillDetailPage(page)
                detail_page.navigate(source_skill_id)

            with allure.step(
                "Step 2 — Edit instructions + tags to the v2-enhanced test "
                "data BEFORE clicking Save As Version (save_as_version() "
                "snapshots whatever is CURRENTLY in the editor)"
            ):
                detail_page.fill_instructions(v2_instructions)
                detail_page.add_tag(v2_tag_1)
                detail_page.add_tag(v2_tag_2)
                assert set(detail_page.get_tags()) == {v2_tag_1, v2_tag_2}, (
                    f"Expected tags {{v2_tag_1, v2_tag_2}} committed before "
                    f"Save As Version, got: {detail_page.get_tags()!r}"
                )

            with allure.step(
                'Step 3 — Click "Save As Version"; verify the new version '
                "is created and becomes active"
            ):
                detail_page.save_as_version(v2_version_name, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_version_selector_value() == v2_version_name, (
                    f"VERSION selector should show {v2_version_name!r} as "
                    f"the active version after Save As Version"
                )
                # Capture the v2-enhanced version's real id HERE, while the
                # URL still carries it as the trailing digit segment
                # (/skills/all/{skillId}/{versionId}) — once the test later
                # navigates onto the FORKED skill's own single-version URL,
                # get_version_id() would read that URL instead and silently
                # return the wrong id.
                source_v2_version_id = detail_page.get_version_id()
                assert source_v2_version_id != str(source_skill_id), (
                    "Save As Version should mint a distinct version id, "
                    f"not reuse the skill id ({source_skill_id})"
                )

            with allure.step(
                'Step 4 — Verify the VERSION dropdown lists both "base" '
                'and "v2-enhanced"'
            ):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_visible("base", timeout=UI_ELEMENT_TIMEOUT), (
                    "VERSION dropdown should list 'base'"
                )
                assert detail_page.is_version_option_visible(v2_version_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"VERSION dropdown should list {v2_version_name!r}"
                )
                # Close the dropdown (Escape) before continuing — re-open
                # elsewhere would otherwise stack a second listbox.
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)

            with allure.step(
                'Step 5 — Open the overflow menu and click "Fork"; verify '
                "the wizard opens"
            ):
                detail_page.open_fork_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.fork_main_entity_name.text_content() == source_skill_name, (
                    "Fork wizard's Main-entity name preview should show the "
                    "source skill's name verbatim"
                )

            with allure.step(
                "Step 6 — Expand the Main entity card; verify it shows the "
                "v2-enhanced version's instructions (not base's)"
            ):
                detail_page.fork_entity_card_toggle.click()
                dialog_text = detail_page.fork_wizard_dialog.text_content() or ""
                assert v2_instructions in dialog_text, (
                    "Expanded Main-entity card should show the ACTIVE "
                    "(v2-enhanced) version's instructions"
                )
                assert base_instructions not in dialog_text, (
                    "Expanded Main-entity card should NOT show the base "
                    "version's original instructions while v2-enhanced is active"
                )

            with allure.step(
                "Step 7 — Select the target project; complete the fork "
                "(POST returns 201 Created)"
            ):
                detail_page.select_fork_target_project(
                    TARGET_PROJECT_ID, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.fork_confirm_button.is_enabled(), (
                    "Fork confirm button should become enabled once a "
                    "target project is selected"
                )

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
                    detail_page.confirm_fork(timeout=FORK_TIMEOUT)

                fork_response = fork_response_info.value
                assert fork_response.status == 201, (
                    f"Fork POST to project {TARGET_PROJECT_ID} should "
                    f"return 201 Created, got {fork_response.status}"
                )
                fork_response_body = fork_response.json()
                forked_skill_id_from_response = fork_response_body["result"]["skills"][0]["id"]
                assert forked_skill_id_from_response, (
                    "Fork POST response should carry the new forked skill's "
                    f"ID at result.skills[0].id — got: {fork_response_body!r}"
                )
                page.wait_for_timeout(500)  # let any deferred console errors surface

                # Known defect #570 (validateDOMNesting <p>-in-<p>, shared
                # IWModalSucceedContent.jsx) — same handling as ELITEA-2602;
                # not re-documented here beyond the soft-assertion capture.
                unexpected_errors = [
                    m.text for m in console_messages
                    if "validateDOMNesting" not in m.text
                ]
                assert not unexpected_errors, (
                    "Expected no UNEXPECTED console errors around the Fork "
                    f"Complete dialog, got: {unexpected_errors!r}"
                )
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
                'Step 8 — Click "Got it"; verify navigation into the '
                "target project"
            ):
                forked_skill_id = detail_page.confirm_fork_complete(timeout=NAVIGATION_TIMEOUT)
                assert forked_skill_id == forked_skill_id_from_response, (
                    "Navigated-to skill ID should match the Fork POST "
                    "response's forked skill ID"
                )
                assert f"/skills/all/{forked_skill_id}" in page.url, (
                    "Should navigate to the forked Skill's own detail page URL"
                )

            with allure.step(
                "Step 9 — Verify the forked skill has exactly ONE version "
                'named "base", carrying the v2-enhanced version\'s '
                "instructions/tags, with parent_version_id pointing at the "
                "source's v2-enhanced version id (not its base version id)"
            ):
                forked_skill = target_project_skill_api.get_skill(forked_skill_id)
                assert len(forked_skill["versions"]) == 1, (
                    "Forked skill should have exactly ONE version, got: "
                    f"{forked_skill['versions']!r}"
                )
                assert forked_skill["versions"][0]["name"] == "base", (
                    "Forked skill's (only) version name should be "
                    f"normalized to 'base', got: {forked_skill['versions'][0]['name']!r}"
                )
                version_details = forked_skill["version_details"]
                assert version_details["name"] == "base", (
                    "Forked skill's active version_details.name should be "
                    f"'base', got: {version_details['name']!r}"
                )
                assert version_details["instructions"] == v2_instructions, (
                    "Forked skill's instructions should match the "
                    "v2-enhanced version's content, NOT the original base "
                    f"instructions — got: {version_details['instructions']!r}"
                )
                assert version_details["instructions"] != base_instructions, (
                    "Forked skill's instructions must NOT equal the "
                    "original base version's instructions"
                )
                forked_tags = {
                    t.get("name") if isinstance(t, dict) else t
                    for t in version_details.get("tags", [])
                }
                assert forked_tags == {v2_tag_1, v2_tag_2}, (
                    f"Forked skill's tags should be {{v2_tag_1, v2_tag_2}}, "
                    f"got: {forked_tags!r}"
                )
                meta = version_details.get("meta", {})
                # source_v2_version_id was captured in Step 3, while the
                # SOURCE skill's URL still carried it — see that step's
                # comment for why it can't be re-derived here.
                assert str(meta.get("parent_version_id")) == str(source_v2_version_id), (
                    "Forked version's parent_version_id should equal the "
                    f"SOURCE's v2-enhanced version id ({source_v2_version_id}), "
                    f"got: {meta.get('parent_version_id')!r}"
                )
                assert str(meta.get("parent_version_id")) != str(source_base_version_id), (
                    "Forked version's parent_version_id must NOT equal the "
                    "source's BASE version id — that would mean the backend "
                    "defaulted to base instead of capturing the "
                    "version-specific export"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — rest of the flow, steps 8-9, "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: forked skill via the UI's type-to-confirm
            # delete flow (fallback to API on failure), source skill (with
            # both versions — one delete removes them together) via API.
            if forked_skill_id is not None:
                try:
                    detail_page.switch_project(TARGET_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                    detail_page.navigate(forked_skill_id)
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
                    logger.info("Cleanup: deleted source skill id=%s (both versions)", source_skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source skill id=%s: %s",
                        source_skill_id, exc,
                    )
            target_project_skill_api.close()
