"""Export Agent with attached Skills — exported .md contains Skill content
(ELITEA-1794, also covers ELITEA-1896).

Creates a Skill + an Agent, attaches the Skill to the Agent, triggers
"Export" from the agent-actions overflow menu (VERSION group), downloads
the resulting ``.agent.md`` file, and asserts its raw content directly:
the attached Skill's ``name``, `base` ``version``, and full ``instructions``
text (via a planted unique marker string) are all embedded verbatim in the
exported YAML frontmatter — not merely referenced by ID.

ELITEA-1896 is a behavioural duplicate of ELITEA-1794 (same objective, same
steps, same pass criteria under different literal test-data names) — see
test-specs/agents/lextend_export-agent-with-attached-skills-exported-md-contains-skill_ELITEA-1896.md
for the dedup proof. Updated 2026-11 (#2991, Agent Skills spec frontmatter): the embedded Skill
now carries a ``frontmatter`` mapping (license + ELITEA fields under
``metadata``); both cases assert it (base version: no elitea-version).

Precondition (updated 2026-11, elitea_issues#7185): the attached Skill has no
files (Files – 0) — a skill WITH files makes the agent export as
``<agent>.agent.zip``; a file-less one still exports ``.md`` (asserted in Step 6).

No product defect found.

Spec: test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md
"""

import json
import logging
import re
import tempfile
import uuid
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import expect

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

MARKER = "ELITEA_1794_MARKER_TEXT"
SKILL_TAG = "regression"
SKILL_LICENSE = "MIT"


def _create_skill(
    page, name: str, description: str, instructions: str,
    tag: str | None = None, license_id: str | None = None,
) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1737/1738/1739/1789/1792:
    fill the form (name / description / CodeMirror instructions), save, and
    confirm the nav-blocker dialog that fires on every save from the create
    form.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, instructions=instructions, description=description)
    if tag:
        form_page.add_tag(tag)
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for skill '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", name, skill_id)
    if license_id:
        # The create form has no frontmatter editor: add the licence on the
        # saved base version via edit mode (same sequence as
        # test_skill_export_import.py Step 3b).
        detail_page.click_edit_mode()
        expect(detail_page.instructions_editor_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        detail_page.add_frontmatter_license(license_id)
        detail_page.save_edits(timeout=FORM_SAVE_TIMEOUT)
    return skill_id


class TestExportAgentWithAttachedSkills:
    """Export Agent with attached Skills (ELITEA-1794, l3)."""

    @pytest.mark.tms("ELITEA-1794", "ELITEA-1896")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1794_export-agent-with-attached-skills.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1896_export-agent-with-attached-skills-exported-md-contains-skill.md",
        "onetest-ai Test Case link (also covers ELITEA-1896 — behavioural duplicate, "
        "see test-specs/agents/lextend_export-agent-with-attached-skills-exported-md-contains-skill_ELITEA-1896.md)",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_export_agent_with_attached_skills(self, page, agent_api, skill_api):
        """Create a Skill + an Agent, attach the Skill, export the Agent via
        the actions overflow menu, and verify the downloaded file's raw
        content embeds the Skill's full content verbatim.

        Steps (AFS test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md):
        1. Create a Skill via UI, with a planted unique marker string in its
           instructions.
        2. Create an Agent via UI.
        3. Attach the Skill to the Agent (case precondition).
        4. Confirm the Agent detail view is open with the Skill attached
           (already satisfied by step 3).
        5. Open the agent-actions overflow menu; click "Export" (VERSION
           group); verify a file download is initiated.
        6. Verify the downloaded file has a `.md`-suffixed name (not `.agent.zip`).
        7. Read the downloaded file's raw content; verify it's a YAML
           frontmatter + markdown body, with the Skill's name, `base`
           version, and full instructions (including the marker) embedded
           verbatim in the `skills:` list.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        # Skill name field enforces MAX_NAME_LENGTH=32 chars (silently
        # truncates via input maxLength) — keep well under that so the
        # popper-search lookup in attach_skill() matches the actual saved
        # name, not a truncated variant.
        skill_name = f"el-1794-skill-{unique_suffix}"
        skill_description = "Test skill for ELITEA-1794 export verification."
        skill_instructions = (
            f"You are {skill_name}. This exact instruction sentence {MARKER} "
            "must appear verbatim in the exported Agent .md file, not merely "
            "referenced."
        )
        # Agent name field also enforces MAX_NAME_LENGTH=32 (same
        # silent-truncation risk as the skill name above).
        agent_name = f"el-1794-agent-{unique_suffix}"
        agent_description = "Agent for ELITEA-1794 export verification."
        agent_instructions = (
            "You are a test agent used for verifying Agent export with "
            "attached Skills."
        )

        skill_id = None
        agent_id = None
        download_path = None
        console_messages = None  # CapturedConsoleMessages, needs stop() in finally

        try:
            with allure.step(
                "Step 1 — Create a Skill via UI, with a planted unique "
                "marker string in its instructions"
            ):
                skill_id = _create_skill(
                    page, skill_name, skill_description, skill_instructions,
                    tag=SKILL_TAG, license_id=SKILL_LICENSE,
                )
                # Case precondition (ELITEA-1794): the attached Skill has no
                # files (Files – 0). A skill with files exports as
                # <agent>.agent.zip since elitea_issues#7185; this one must
                # stay on the single-file .md path.
                skill_detail = SkillDetailPage(page)
                expect(skill_detail.skill_view_files_tab).to_have_text(
                    re.compile(r"Files\s*[–-]\s*0"), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 2 — Create an Agent via UI"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=agent_name,
                    description=agent_description,
                    instructions=agent_instructions,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", agent_name, agent_id)

            with allure.step(
                "Step 3 — Attach the Skill to the Agent (precondition: "
                "Agent exists with >=1 Skill attached)"
            ):
                console_messages = detail_page.capture_console_errors()

                detail_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert detail_page.is_skill_attached(skill_name), (
                    f"Skill card for '{skill_name}' should render after attaching"
                )
                assert detail_page.get_skill_version_text(skill_name) == "base", (
                    "Attached skill's card should show 'base' as its version"
                )

            with allure.step(
                "Step 4 — Confirm the Agent detail/edit view is open with "
                "the Skill attached (already satisfied by Step 3)"
            ):
                detail_page.verify_on_detail_page(expected_agent_id=agent_id)
                assert detail_page.is_skill_attached(skill_name), (
                    "Skill should still be attached on the open Agent detail view"
                )

            with allure.step(
                "Step 5 — Open the agent-actions overflow menu; click "
                "'Export' (VERSION group); verify a file download is "
                "initiated"
            ):
                download = detail_page.export_agent_via_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert download.suggested_filename, (
                    "Export should trigger a file download with a suggested filename"
                )
                assert not console_messages, (
                    "Expected no console errors during the export/download flow, "
                    f"got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 6 — Verify the downloaded file has a .md-suffixed name"
            ):
                assert not download.suggested_filename.endswith(".agent.zip"), (
                    "Export format regression: an Agent whose attached Skill has "
                    "no files (Files – 0) must export as a single .md, got a "
                    f".agent.zip: {download.suggested_filename!r}"
                )
                assert download.suggested_filename.endswith(".md"), (
                    f"Expected a .md download, got: {download.suggested_filename!r}"
                )
                # Playwright's internal download path doesn't preserve the
                # suggested filename/extension — save_as() to a path that
                # keeps the real ".md" extension (mirrors the pattern used
                # for skill export/import in test_skill_export_import.py).
                download_path = Path(tempfile.gettempdir()) / download.suggested_filename
                download.save_as(download_path)
                assert download_path.exists() and download_path.stat().st_size > 0, (
                    "Downloaded export file should exist and be non-empty"
                )

            with allure.step(
                "Step 7 — Read the downloaded file's raw content; verify "
                "YAML frontmatter + markdown body, with the Skill's name, "
                "base version, and full instructions (incl. marker) "
                "embedded verbatim"
            ):
                raw_content = download_path.read_text(encoding="utf-8")
                parts = raw_content.split("---", 2)
                assert len(parts) == 3, (
                    "Expected YAML frontmatter delimited by '---', got "
                    f"structure: {raw_content[:200]!r}"
                )
                frontmatter = yaml.safe_load(parts[1])
                agent_body = parts[2].strip()

                assert frontmatter.get("name") == agent_name, (
                    f"Exported frontmatter name mismatch: {frontmatter.get('name')!r} "
                    f"!= {agent_name!r}"
                )
                assert frontmatter.get("description") == agent_description, (
                    "Exported frontmatter description should match the Agent"
                )
                assert agent_body == agent_instructions, (
                    "Exported markdown body should match the Agent's own instructions"
                )

                skills = frontmatter.get("skills")
                assert isinstance(skills, list) and len(skills) == 1, (
                    f"Expected exactly one attached Skill in the exported "
                    f"'skills:' list, got: {skills!r}"
                )
                exported_skill = skills[0]

                assert exported_skill.get("name") == skill_name, (
                    "Exported skills[0].name should match the attached Skill's "
                    f"name, got: {exported_skill.get('name')!r}"
                )
                assert exported_skill.get("version") == "base", (
                    "Exported skills[0].version should read 'base', got: "
                    f"{exported_skill.get('version')!r}"
                )
                # This is the case's core claim and the strongest evidence:
                # the marker substring can only appear if the FULL
                # instructions text is embedded, not a bare ID/reference.
                exported_instructions = exported_skill.get("instructions") or ""
                assert MARKER in exported_instructions, (
                    "Exported skills[0].instructions should contain the "
                    f"planted marker {MARKER!r} verbatim, got: "
                    f"{exported_instructions!r}"
                )
                # The export now carries the skill body with a leading blank
                # line (its frontmatter is stripped out into `frontmatter`).
                assert exported_instructions.strip() == skill_instructions, (
                    "Exported skills[0].instructions should match the "
                    "attached Skill's full instructions text verbatim"
                )

                # Agent Skills spec frontmatter (#2991): spec keys at the top
                # level, ELITEA fields namespaced under `metadata`.
                skill_fm = exported_skill.get("frontmatter")
                assert isinstance(skill_fm, dict), (
                    f"Exported skills[0] should embed a `frontmatter` mapping, got: {skill_fm!r}"
                )
                assert skill_fm.get("license") == SKILL_LICENSE, (
                    f"Embedded Skill frontmatter license should be {SKILL_LICENSE!r}, "
                    f"got: {skill_fm.get('license')!r}"
                )
                assert set(skill_fm) == {"license", "metadata"}, (
                    "Embedded Skill frontmatter should hold only spec keys "
                    f"(license, metadata), got: {sorted(skill_fm)}"
                )
                fm_metadata = skill_fm["metadata"]
                assert json.loads(fm_metadata["elitea-tags"]) == [SKILL_TAG], (
                    "ELITEA tags should live under metadata.elitea-tags, got: "
                    f"{fm_metadata.get('elitea-tags')!r}"
                )
                assert "elitea-version" not in fm_metadata, (
                    "A base-version Skill should not export metadata.elitea-version, "
                    f"got: {fm_metadata!r}"
                )
                legacy_keys = {"tags", "elitea_version", "elitea_run_settings"}
                assert not legacy_keys & (set(skill_fm) | set(exported_skill)), (
                    "Legacy top-level ELITEA keys must not be exported, got: "
                    f"{sorted(legacy_keys & (set(skill_fm) | set(exported_skill)))}"
                )

        finally:
            # Stop listeners to prevent resource leaks that cause test hangs.
            if console_messages is not None:
                console_messages.stop()

            # Cleanup per AFS: delete the agent first (teardown hygiene —
            # remove the thing with attached-state dependencies first), then
            # the skill, tolerating individual failures (mirrors
            # ELITEA-1735/1737/1738/1739/1789/1792's cleanup pattern).
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                    )
            if download_path is not None:
                try:
                    download_path.unlink(missing_ok=True)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to remove downloaded file %s: %s",
                        download_path, exc,
                    )
