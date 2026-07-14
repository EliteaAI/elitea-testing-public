"""Import Agent with attached Skills recreates Skills with new IDs
(ELITEA-1795).

Mirrors ELITEA-1794's setup (create a Skill + an Agent, attach the Skill,
export the Agent via the agent-actions overflow menu) then imports the
downloaded ``.agent.md`` file via the Agents list "Import" button, and
asserts that the import creates a brand-new Skill entity with a new
unique ID (distinct from the source Skill's ID) plus full verbatim
content, correctly linked to the newly created Agent.

No product defect found. One UI-only async-timing quirk documented (not
a defect — the Skills counter on the imported Agent's detail page can
show "0/5" for ~1-2s before its secondary ``application_skills`` fetch
resolves; this test waits on that condition instead of asserting on
first paint).

Spec: test-specs/skills/l3_import-agent-recreates-skills-with-new-ids_ELITEA-1795.md
"""

import logging
import tempfile
import uuid
from pathlib import Path

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

MARKER = "ELITEA_1795_MARKER_TEXT"


def _create_skill(page, name: str, description: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1737/1738/1739/1789/
    1792/1794: fill the form (name / description / CodeMirror instructions),
    save, and confirm the resulting detail page.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, instructions=instructions, description=description)
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for skill '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", name, skill_id)
    return skill_id


class TestImportAgentRecreatesSkillsWithNewIds:
    """Import Agent with attached Skills recreates Skills with new IDs (ELITEA-1795, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1795_import-agent-recreates-skills-with-new-ids.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_import_agent_recreates_skills_with_new_ids(self, page, agent_api, skill_api):
        """Export an Agent with an attached Skill, import it, verify a new
        Skill entity (new unique ID) is created and correctly linked.

        Steps (AFS test-specs/skills/l3_import-agent-recreates-skills-with-new-ids_ELITEA-1795.md):
        1. (Precondition setup, mirrors ELITEA-1794) Create a Skill + an
           Agent, attach the Skill, export the Agent via the actions
           overflow menu.
        2. Navigate to the Agents list; click "Import"; verify a native
           file chooser opens.
        3. Select the exported file; verify the "Import parameters"
           preview dialog previews the embedded Agent + Skill content.
        4. Confirm the dialog's Import button; verify the "Import
           Complete" success dialog lists 1 agent + 1 skill.
        5. Click "Got it"; verify auto-navigation to the new Agent's
           detail page with a new, distinct Agent ID.
        6. Verify the imported Agent's Skills section shows the Skill
           attached (waiting on the async application_skills fetch, not
           asserting on first paint) and the API response's skill_id is
           new/unique.
        7. Navigate to the Skills list; verify two cards share the Skill's
           name (source + imported); verify the imported Skill's own
           detail page shows a new ID and verbatim content; verify the
           source Skill AND the source Agent are both unaffected by the
           import (Axis 2 additions — import must be purely additive).
        8. Edit + save the imported Agent; verify a clean save.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        skill_name = f"el-1795-skill-{unique_suffix}"
        skill_description = "Test skill for ELITEA-1795 import-recreates-skill verification."
        skill_instructions = (
            f"You are {skill_name}. This exact instruction sentence {MARKER} "
            "must appear verbatim in the imported Skill, not merely referenced."
        )
        source_agent_name = f"el-1795-agent-{unique_suffix}"
        source_agent_description = "Agent for ELITEA-1795 import verification (source)."
        source_agent_instructions = (
            "You are a test agent used for verifying Agent import recreates "
            "attached Skills with new IDs."
        )

        source_skill_id = None
        source_agent_id = None
        imported_skill_id = None
        imported_agent_id = None
        download_path = None

        try:
            with allure.step(
                "Step 1 — Precondition setup (mirrors ELITEA-1794): create "
                "a Skill + an Agent, attach the Skill, export via the "
                "actions overflow menu"
            ):
                source_skill_id = _create_skill(
                    page, skill_name, skill_description, skill_instructions,
                )

                agents_list_page = AgentsListPage(page)
                agents_list_page.navigate_to_create()

                agent_form_page = AgentFormPage(page)
                agent_form_page.wait_for_form_load()
                agent_form_page.fill_form(
                    name=source_agent_name,
                    description=source_agent_description,
                    instructions=source_agent_instructions,
                )
                agent_form_page.wait_for_form_validation()
                assert agent_form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                agent_form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                source_agent_id = int(detail_page.get_agent_id())
                logger.info(
                    "Created source agent %r with id=%d", source_agent_name, source_agent_id,
                )

                detail_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached on the source agent"
                )
                assert detail_page.is_skill_attached(skill_name), (
                    f"Skill card for '{skill_name}' should render on the source agent"
                )

                download = detail_page.export_agent_via_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert download.suggested_filename.endswith(".md"), (
                    f"Expected a .md export download, got: {download.suggested_filename!r}"
                )
                # Playwright's internal download path doesn't preserve the
                # suggested filename/extension — save_as() to a path that
                # keeps the real ".md" extension so the import flow's file
                # picker sees a valid filename.
                download_path = Path(tempfile.gettempdir()) / download.suggested_filename
                download.save_as(download_path)
                assert download_path.exists() and download_path.stat().st_size > 0, (
                    "Downloaded export file should exist and be non-empty"
                )

            with allure.step(
                "Step 2 — Navigate to the Agents list; click 'Import'; "
                "verify a native file chooser opens"
            ):
                agents_list_page.navigate()
                # import_agent() itself performs the click + file-chooser
                # handling; a successfully-rendered "Import parameters"
                # dialog (asserted inside the method) is the observable
                # proof that the file chooser opened and accepted the file.
                agents_list_page.import_agent(str(download_path), timeout=IMPORT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify the 'Import parameters' preview dialog "
                "previews the embedded Agent + Skill content client-side"
            ):
                dialog = page.get_by_role("dialog")
                assert dialog.get_by_text("Import parameters").is_visible(), (
                    "Import parameters dialog should be visible after selecting the file"
                )
                assert dialog.get_by_text(source_agent_name).first.is_visible(), (
                    "Import dialog should preview the exported Agent's name"
                )
                assert dialog.get_by_text(skill_name).first.is_visible(), (
                    "Import dialog should preview the embedded Skill's name"
                )

                agents_list_page.expand_import_preview_details(timeout=IMPORT_TIMEOUT)
                assert dialog.get_by_text(skill_instructions, exact=False).is_visible(), (
                    "Import dialog should preview the embedded Skill's full "
                    f"instructions verbatim (incl. marker {MARKER!r}), proving "
                    "the dialog parses the uploaded file's content client-side, "
                    "not via a live lookup by ID"
                )

            with allure.step(
                "Step 4 — Confirm the dialog's Import button; verify the "
                "'Import Complete' success dialog lists 1 agent + 1 skill"
            ):
                agents_list_page.confirm_agent_import(timeout=IMPORT_TIMEOUT)

                success_dialog = page.get_by_role("dialog")
                assert success_dialog.get_by_text("Import Complete").is_visible(), (
                    "Success dialog should show the 'Import Complete' heading"
                )
                assert success_dialog.get_by_text(source_agent_name).is_visible(), (
                    "Success dialog should list the imported Agent's name — "
                    "confirming a new Agent entity was created"
                )
                assert success_dialog.get_by_text(skill_name).is_visible(), (
                    "Success dialog should list the imported Skill's name — "
                    "confirming a new Skill entity was created (not merely an "
                    "Agent linking to the pre-existing source Skill by ID)"
                )

            with allure.step(
                "Step 5 — Click 'Got it'; verify auto-navigation to the "
                "new Agent's detail page with a new, distinct Agent ID"
            ):
                # Wrap the navigation-triggering click so the secondary
                # application_skills fetch (fired as part of the new
                # Agent detail page's load) can be captured directly —
                # a concrete, non-UI-dependent assertion surface for
                # "Agent is linked to the new Skill" that sidesteps the
                # documented first-paint timing race (AFS Known Defects).
                with page.expect_response(
                    lambda r: (
                        "/elitea_core/application_skills/prompt_lib/" in r.url
                        and r.request.method == "GET"
                    ),
                    timeout=NAVIGATION_TIMEOUT,
                ) as skills_response_info:
                    imported_agent_id = agents_list_page.confirm_import_complete(
                        timeout=NAVIGATION_TIMEOUT,
                    )

                assert imported_agent_id != source_agent_id, (
                    f"Imported Agent ID should differ from source: "
                    f"imported={imported_agent_id}, source={source_agent_id}"
                )
                logger.info("Imported agent created — id=%d", imported_agent_id)

                detail_page = AgentDetailPage(page)
                detail_page.verify_on_detail_page(expected_agent_id=imported_agent_id)
                assert detail_page.get_name() == source_agent_name, (
                    "Imported agent's name should match the exported Agent's name"
                )

            with allure.step(
                "Step 6 — Verify the imported Agent's Skills section shows "
                "the Skill attached (waiting on the async fetch, not "
                "first paint) and the API response's skill_id is new/unique"
            ):
                skills_json = skills_response_info.value.json()
                assert skills_json.get("max_skills") == 5, (
                    f"Expected max_skills=5 in application_skills response, "
                    f"got: {skills_json!r}"
                )
                skills_entries = skills_json.get("skills") or []
                assert len(skills_entries) == 1, (
                    f"Expected exactly one attached Skill in the imported "
                    f"Agent's application_skills response, got: {skills_entries!r}"
                )
                skill_entry = skills_entries[0]
                assert skill_entry.get("name") == skill_name, (
                    "application_skills response entry name should match the "
                    f"imported Skill's name, got: {skill_entry.get('name')!r}"
                )
                imported_skill_id = skill_entry.get("skill_id")
                assert imported_skill_id is not None, (
                    f"application_skills response should include a skill_id, "
                    f"got entry: {skill_entry!r}"
                )
                assert imported_skill_id != source_skill_id, (
                    "This is the case's core claim: the imported Skill's ID "
                    f"must differ from the source. imported={imported_skill_id}, "
                    f"source={source_skill_id}"
                )

                # UI-side confirmation — poll the Skills counter (established
                # helper already used for this exact async-cache-invalidation
                # race elsewhere in the suite) rather than asserting on the
                # very first paint, which the AFS documents as a flaky race
                # ("0/5" flashes before the secondary fetch resolves).
                counter_text = detail_page.wait_for_skills_counter(
                    "1/", timeout=NAVIGATION_TIMEOUT,
                )
                assert counter_text.startswith("1/"), (
                    f"Skills counter should settle on '1/5 skills added.' once "
                    f"the async application_skills fetch resolves, got: {counter_text!r}"
                )
                assert detail_page.is_skill_attached(skill_name), (
                    f"Skill card for '{skill_name}' should render on the "
                    "imported Agent once the Skills section has fully loaded"
                )

            with allure.step(
                "Step 7 — Navigate to the Skills list; verify two cards "
                "share the Skill's name (source + imported); verify the "
                "imported Skill's own detail page shows a new ID and "
                "verbatim content; verify the source Skill AND source Agent "
                "are both unaffected by the import"
            ):
                skills_list_page = SkillsListPage(page)
                skills_list_page.navigate()
                visible_names = skills_list_page.get_visible_skill_names()
                assert visible_names.count(skill_name) == 2, (
                    f"Expected 2 skill cards named {skill_name!r} (source + "
                    f"imported) in the Skills list, got: {visible_names!r}"
                )

                skill_detail_page = SkillDetailPage(page)
                skill_detail_page.navigate(imported_skill_id)
                assert int(skill_detail_page.get_skill_id()) == imported_skill_id, (
                    "Navigating to the imported Skill's ID should land on its "
                    "own detail page"
                )
                assert skill_detail_page.get_name() == skill_name, (
                    "Imported skill's name should match the source verbatim"
                )
                assert skill_detail_page.get_description() == skill_description, (
                    "Imported skill's description should match the source verbatim"
                )
                imported_instructions = skill_detail_page.get_instructions()
                assert MARKER in imported_instructions, (
                    f"Imported skill's instructions should contain the planted "
                    f"marker {MARKER!r} verbatim, got: {imported_instructions!r}"
                )
                assert imported_instructions == skill_instructions, (
                    "Imported skill's instructions should match the source "
                    "skill's full instructions text verbatim"
                )

                # Positive check: the import is purely additive — the
                # original source Skill is unaffected (Axis 2 addition).
                source_skill_detail_page = SkillDetailPage(page)
                source_skill_detail_page.navigate(source_skill_id)
                assert source_skill_detail_page.get_name() == skill_name, (
                    "Source skill should remain unchanged and independently "
                    "addressable after the import"
                )

                # Positive check: the source Agent is likewise unaffected by
                # the import (Axis 2 addition — mirrors the source-Skill
                # check above). Re-navigate to the source Agent's own ID and
                # confirm its name/description still match what was set in
                # Step 1, before the import ever ran.
                source_agent_detail_page = AgentDetailPage(page)
                source_agent_detail_page.navigate(source_agent_id)
                assert source_agent_detail_page.get_name() == source_agent_name, (
                    "Source agent's name should remain unchanged and "
                    "independently addressable after the import"
                )
                assert source_agent_detail_page.get_description() == source_agent_description, (
                    "Source agent's description should remain unchanged after "
                    "the import — the import must not mutate the source Agent"
                )

            with allure.step(
                "Step 8 — Edit + save the imported Agent; verify a clean "
                "save with no console errors"
            ):
                detail_page.navigate(imported_agent_id)

                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                edited_description = source_agent_description + " (edited)"
                detail_page.update_description(edited_description)
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled after editing the imported Agent's description"
                )

                detail_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                assert not detail_page.is_save_enabled(), (
                    "Save should return to disabled after a clean save (dirty flag cleared)"
                )
                assert detail_page.get_description() == edited_description, (
                    "Description should persist the edit after save"
                )
                assert not console_messages, (
                    f"Expected no console errors during the imported Agent's "
                    f"Save, got: {[m.text for m in console_messages]}"
                )

        finally:
            # Cleanup per AFS: delete both Agents first (attached-state
            # dependencies), then both Skills, tolerating individual
            # failures (mirrors ELITEA-1794/1735/1737/1738/1739/1789/1792's
            # cleanup pattern, generalized to 4 entities).
            if imported_agent_id is not None:
                try:
                    agent_api.delete_agent(imported_agent_id)
                    logger.info("Cleanup: deleted imported agent id=%d", imported_agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported agent id=%s: %s",
                        imported_agent_id, exc,
                    )
            if source_agent_id is not None:
                try:
                    agent_api.delete_agent(source_agent_id)
                    logger.info("Cleanup: deleted source agent id=%d", source_agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source agent id=%s: %s",
                        source_agent_id, exc,
                    )
            if imported_skill_id is not None:
                try:
                    skill_api.delete_skill(imported_skill_id)
                    logger.info("Cleanup: deleted imported skill id=%s", imported_skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported skill id=%s: %s",
                        imported_skill_id, exc,
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
            if download_path is not None:
                try:
                    download_path.unlink(missing_ok=True)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to remove downloaded file %s: %s",
                        download_path, exc,
                    )
