"""Import agent .zip with nested agent dependencies — creates main + all
nested agents and links them (ELITEA-1902).

Creates a nested (dependency) Agent, then a main Agent with the nested
Agent attached via the Tools section's "+ Agent" picker, exports the main
Agent via the actions overflow menu, and asserts the downloaded archive is
a ``.zip`` (not the single ``.md`` every Skill-only/no-dependency export in
this repo produces — ELITEA-1794/1795/1894) containing one ``.agent.md``
per entity. Imports the ``.zip`` back via the Agents list "Import" button
and asserts: the preview dialog shows entity cards for both the main agent
AND the nested dependency; the "Import Complete" dialog lists both new
entities; and the newly imported main agent's Tools section shows the
newly imported nested agent attached as a sub-agent tool with a brand-new,
distinct ID (the import recreates both entities, mirroring the "always-new,
never-linked-by-ID" pattern ELITEA-1795 already established for Skills).

No product defect found. One pre-existing, unrelated React dev-mode
console warning (`validateDOMNesting` on the Import-Complete dialog's
Tooltip) fires on every successful import — filtered out of the
zero-console-errors assertion rather than asserted against (see AFS §
Known Defects).

Spec: test-specs/agents/l3_import-agent-zip-nested-dependencies_ELITEA-1902.md
"""

import logging
import re
import tempfile
import uuid
import zipfile
from pathlib import Path

import allure
import pytest
import yaml

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.agents")

MAIN_MARKER = "ELITEA_1902_MAIN_MARKER"
NESTED_MARKER = "ELITEA_1902_NESTED_MARKER"

# Known, pre-existing, unrelated React dev-mode DOM-nesting warning that
# fires on every successful Import Complete dialog render (AFS § Known
# Defects) — not specific to this case, not a user-visible defect. Filtered
# out of the zero-console-errors assertion rather than asserted against, so
# the assertion stays meaningful for anything ELSE the flow might regress.
_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING = "validateDOMNesting"


def _create_agent(page, name: str, description: str, instructions: str) -> int:
    """Create an agent via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1794/1795/1894: fill the
    form, save, and confirm the resulting detail page.
    """
    list_page = AgentsListPage(page)
    list_page.navigate_to_create()

    form_page = AgentFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, description=description, instructions=instructions)
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for agent '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = AgentDetailPage(page)
    detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
    detail_page.verify_on_detail_page()
    agent_id = int(detail_page.get_agent_id())
    logger.info("Created agent %r with id=%d", name, agent_id)
    return agent_id


class TestImportAgentZipNestedAgentDependencies:
    """Import agent .zip with nested agent dependencies (ELITEA-1902, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1902_import-agent-zip-with-nested-agent-dependencies.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_import_agent_zip_nested_agent_dependencies(self, page, agent_api):
        """Export a main Agent with a nested Agent dependency attached
        (produces a .zip), import it back, and verify both entities are
        recreated with new IDs and correctly linked.

        Steps (AFS test-specs/agents/l3_import-agent-zip-nested-dependencies_ELITEA-1902.md):
        1. (Precondition setup) Create a nested Agent, then a main Agent
           with the nested Agent attached via the "+ Agent" picker.
        2. Export the main Agent via the actions overflow menu; verify a
           `.zip` file is downloaded.
        3. Unzip and inspect the archive's contents; verify it contains one
           `.agent.md` per entity (main + nested), and the main entity's
           frontmatter references the nested Agent.
        4. Navigate to Agents list; import the `.zip`; verify the "Import
           parameters" preview dialog opens.
        5. Verify the import wizard lists entity cards for the main agent
           AND the nested dependency.
        6. Confirm the dialog's Import button; verify the "Import
           Complete" success dialog.
        7. Verify the success dialog lists both new entities ("2 agents").
        8. Click "Got it"; verify the main agent and nested agent are both
           created with new, distinct IDs and correctly linked (Tools
           section shows the nested agent attached).
        """
        unique_suffix = uuid.uuid4().hex[:8]
        nested_agent_name = f"el-1902-nested-{unique_suffix}"
        nested_agent_description = "Nested dependency agent for ELITEA-1902 import test."
        # Shorter than the AFS's "used in this run" wording (implementer
        # Phase 2 technique adjustment, not a scope change): the shared
        # AgentFormPage.fill_form() types instructions via
        # press_sequentially(delay=80ms/char) against a 10s default action
        # timeout (same constraint documented in ELITEA-1894's export
        # test) — keep well under that. The marker-verbatim requirement is
        # unaffected — only the surrounding prose is shorter.
        nested_agent_instructions = f"Nested dep agent. {NESTED_MARKER} must appear verbatim."
        main_agent_name = f"el-1902-main-{unique_suffix}"
        main_agent_description = (
            "Main agent for ELITEA-1902 import test (has nested agent dependency)."
        )
        main_agent_instructions = f"Main agent, delegates. {MAIN_MARKER} must appear verbatim."

        source_nested_agent_id = None
        source_main_agent_id = None
        imported_main_agent_id = None
        imported_nested_agent_id = None
        download_path = None

        try:
            with allure.step(
                "Step 1 — Precondition setup: create a nested Agent, then a "
                "main Agent with the nested Agent attached via the "
                "'+ Agent' picker"
            ):
                source_nested_agent_id = _create_agent(
                    page, nested_agent_name, nested_agent_description,
                    nested_agent_instructions,
                )

                source_main_agent_id = _create_agent(
                    page, main_agent_name, main_agent_description,
                    main_agent_instructions,
                )

                detail_page = AgentDetailPage(page)
                detail_page.attach_agent(nested_agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_toolkit_attached(
                    nested_agent_name, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"Sub-agent card for '{nested_agent_name}' should render "
                    "on the main agent after attaching"
                )

            with allure.step(
                "Step 2 — Export the main Agent via the actions overflow "
                "menu; verify a .zip file is downloaded"
            ):
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                download = detail_page.export_agent_via_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert download.suggested_filename.endswith(".zip"), (
                    "Exporting an Agent with a nested Agent dependency should "
                    f"produce a .zip archive, got: {download.suggested_filename!r}"
                )
                download_path = Path(tempfile.gettempdir()) / download.suggested_filename
                download.save_as(download_path)
                assert download_path.exists() and download_path.stat().st_size > 0, (
                    "Downloaded export archive should exist and be non-empty"
                )

            with allure.step(
                "Step 3 — Unzip and inspect the archive's contents; verify "
                "one .agent.md per entity (main + nested), and the main "
                "entity's frontmatter references the nested Agent"
            ):
                with zipfile.ZipFile(download_path) as archive:
                    member_names = archive.namelist()
                    agent_md_members = [n for n in member_names if n.endswith(".agent.md")]
                    assert len(agent_md_members) == 2, (
                        "Expected exactly 2 '.agent.md' members in the exported "
                        f"archive (main + nested), got: {member_names!r}"
                    )

                    main_member = next(
                        (n for n in agent_md_members if main_agent_name in n), None,
                    )
                    nested_member = next(
                        (n for n in agent_md_members if nested_agent_name in n), None,
                    )
                    assert main_member is not None, (
                        f"Archive should contain a '.agent.md' member for the "
                        f"main agent {main_agent_name!r}, got: {member_names!r}"
                    )
                    assert nested_member is not None, (
                        f"Archive should contain a '.agent.md' member for the "
                        f"nested agent {nested_agent_name!r}, got: {member_names!r}"
                    )

                    main_raw = archive.read(main_member).decode("utf-8")
                    nested_raw = archive.read(nested_member).decode("utf-8")

                main_parts = main_raw.split("---", 2)
                assert len(main_parts) == 3, (
                    "Expected the main entity's .agent.md to have YAML "
                    f"frontmatter delimited by '---', got: {main_raw[:200]!r}"
                )
                main_frontmatter = yaml.safe_load(main_parts[1])
                assert main_frontmatter.get("name") == main_agent_name, (
                    "Main entity's exported frontmatter name should match "
                    f"the main agent, got: {main_frontmatter.get('name')!r}"
                )
                nested_agents_ref = main_frontmatter.get("nested_agents")
                assert isinstance(nested_agents_ref, list) and len(nested_agents_ref) == 1, (
                    "Main entity's frontmatter should carry exactly one "
                    f"'nested_agents' entry, got: {nested_agents_ref!r}"
                )
                assert nested_agents_ref[0].get("name") == nested_agent_name, (
                    "Main entity's nested_agents[0].name should reference the "
                    f"nested agent, got: {nested_agents_ref[0].get('name')!r}"
                )
                assert NESTED_MARKER in nested_raw, (
                    "Nested entity's exported .agent.md should contain the "
                    f"planted marker {NESTED_MARKER!r} verbatim"
                )
                assert MAIN_MARKER in main_parts[2], (
                    "Main entity's exported .agent.md body should contain the "
                    f"planted marker {MAIN_MARKER!r} verbatim"
                )

            with allure.step(
                "Step 4 — Navigate to Agents list; import the .zip; verify "
                "the 'Import parameters' preview dialog opens"
            ):
                agents_list_page = AgentsListPage(page)
                agents_list_page.navigate()
                agents_list_page.import_agent(str(download_path), timeout=IMPORT_TIMEOUT)
                assert agents_list_page.import_preview_dialog.is_visible(), (
                    "Import parameters dialog should be visible after "
                    "selecting the .zip archive"
                )

            with allure.step(
                "Step 5 — Verify the import wizard lists entity cards for "
                "the main agent AND the nested dependency"
            ):
                assert agents_list_page.import_preview_name.is_visible(), (
                    "Import dialog should preview the main entity's name"
                )
                assert agents_list_page.import_preview_name.text_content() == main_agent_name, (
                    "Import dialog's Main-entity name preview should show "
                    "the exported main Agent's name verbatim"
                )
                assert agents_list_page.import_preview_nested_agent_name.is_visible(), (
                    "Import dialog should preview the nested Agent's name in "
                    "a 'Nested entities' section"
                )
                assert (
                    agents_list_page.import_preview_nested_agent_name.text_content()
                    == nested_agent_name
                ), (
                    "Import dialog's Nested-Agent name preview should show "
                    "the nested Agent's name verbatim"
                )

                agents_list_page.expand_import_preview_details(timeout=IMPORT_TIMEOUT)
                nested_instructions_preview = (
                    agents_list_page.import_preview_nested_agent_instructions.text_content()
                )
                assert nested_instructions_preview == nested_agent_instructions, (
                    "Import dialog should preview the nested Agent's full "
                    f"instructions verbatim (incl. marker {NESTED_MARKER!r}), "
                    "proving the dialog parses the uploaded archive's content "
                    f"client-side — got: {nested_instructions_preview!r}"
                )

            with allure.step(
                "Step 6 — Confirm the dialog's Import button; verify the "
                "'Import Complete' success dialog"
            ):
                agents_list_page.confirm_agent_import(timeout=IMPORT_TIMEOUT)
                assert agents_list_page.import_complete_dialog.is_visible(), (
                    "Success dialog should be visible after confirming the import"
                )

            with allure.step(
                "Step 7 — Verify the success dialog lists both new "
                "entities ('2 agents')"
            ):
                complete_agents_text = agents_list_page.import_complete_agents_list.text_content()
                assert main_agent_name in complete_agents_text, (
                    "Success dialog's Agents list should include the "
                    f"imported main Agent's name, got: {complete_agents_text!r}"
                )
                assert nested_agent_name in complete_agents_text, (
                    "Success dialog's Agents list should include the "
                    "imported nested Agent's name — confirming a new Agent "
                    f"entity was created, got: {complete_agents_text!r}"
                )

            with allure.step(
                "Step 8 — Click 'Got it'; verify the main agent and nested "
                "agent are both created with new, distinct IDs and "
                "correctly linked (Tools section shows the nested agent "
                "attached)"
            ):
                imported_main_agent_id = agents_list_page.confirm_import_complete(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert imported_main_agent_id != source_main_agent_id, (
                    "Imported main Agent ID should differ from the source: "
                    f"imported={imported_main_agent_id}, source={source_main_agent_id}"
                )

                detail_page = AgentDetailPage(page)
                detail_page.verify_on_detail_page(expected_agent_id=imported_main_agent_id)
                assert detail_page.get_name() == main_agent_name, (
                    "Imported main agent's name should match the exported "
                    "main Agent's name"
                )
                assert detail_page.is_toolkit_attached(
                    nested_agent_name, timeout=NAVIGATION_TIMEOUT
                ), (
                    f"Imported main agent's Tools section should show the "
                    f"nested agent '{nested_agent_name}' attached as a "
                    "sub-agent tool"
                )

                # Drill into the nested agent's own card (via the card's
                # "open in new tab" action — the shared toolkit-card open
                # button, the same handle `click_toolkit_open_in_new_tab()`
                # already uses for external toolkits) to confirm it too was
                # recreated with a brand-new, distinct ID (not merely
                # linked by reference to the source nested agent) — the
                # same "always-new, never-linked-by-ID" pattern ELITEA-1795
                # already established for Skills.
                new_tab_url = detail_page.click_toolkit_open_in_new_tab(
                    nested_agent_name, timeout=NAVIGATION_TIMEOUT,
                )
                url_match = re.search(r"/agents/all/(\d+)", new_tab_url)
                assert url_match, (
                    "Expected the nested agent's 'open in new tab' URL to "
                    f"contain an Agent ID, got: {new_tab_url!r}"
                )
                imported_nested_agent_id = int(url_match.group(1))

                nested_detail_page = AgentDetailPage(page)
                nested_detail_page.navigate(imported_nested_agent_id)
                assert imported_nested_agent_id != source_nested_agent_id, (
                    "This is the case's core claim: the imported nested "
                    "Agent's ID must differ from the source. "
                    f"imported={imported_nested_agent_id}, "
                    f"source={source_nested_agent_id}"
                )
                assert nested_detail_page.get_name() == nested_agent_name, (
                    "Imported nested agent's name should match the source "
                    "verbatim"
                )
                imported_nested_instructions = nested_detail_page.get_instructions()
                assert NESTED_MARKER in imported_nested_instructions, (
                    "Imported nested agent's instructions should contain "
                    f"the planted marker {NESTED_MARKER!r} verbatim, got: "
                    f"{imported_nested_instructions!r}"
                )
                assert imported_nested_instructions == nested_agent_instructions, (
                    "Imported nested agent's instructions should match the "
                    "source nested agent's full instructions verbatim"
                )

                # Axis 2 addition — the import is purely additive: the
                # source main + nested agents remain unaffected.
                source_main_detail_page = AgentDetailPage(page)
                source_main_detail_page.navigate(source_main_agent_id)
                assert source_main_detail_page.get_name() == main_agent_name, (
                    "Source main agent should remain unchanged and "
                    "independently addressable after the import"
                )
                source_nested_detail_page = AgentDetailPage(page)
                source_nested_detail_page.navigate(source_nested_agent_id)
                assert source_nested_detail_page.get_name() == nested_agent_name, (
                    "Source nested agent should remain unchanged and "
                    "independently addressable after the import"
                )

                real_console_errors = [
                    m.text for m in console_messages
                    if _KNOWN_NONBLOCKING_CONSOLE_SUBSTRING not in m.text
                ]
                assert not real_console_errors, (
                    "Expected no (unfiltered) console errors during the "
                    f"export/import/attach flow, got: {real_console_errors!r}"
                )

        finally:
            # Cleanup per AFS: imported nested agent -> imported main agent
            # -> source nested agent -> source main agent, tolerating
            # individual failures (mirrors ELITEA-1795's cleanup pattern).
            if imported_nested_agent_id is not None:
                try:
                    agent_api.delete_agent(imported_nested_agent_id)
                    logger.info(
                        "Cleanup: deleted imported nested agent id=%d",
                        imported_nested_agent_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported nested agent "
                        "id=%s: %s", imported_nested_agent_id, exc,
                    )
            if imported_main_agent_id is not None:
                try:
                    agent_api.delete_agent(imported_main_agent_id)
                    logger.info(
                        "Cleanup: deleted imported main agent id=%d",
                        imported_main_agent_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported main agent "
                        "id=%s: %s", imported_main_agent_id, exc,
                    )
            if source_nested_agent_id is not None:
                try:
                    agent_api.delete_agent(source_nested_agent_id)
                    logger.info(
                        "Cleanup: deleted source nested agent id=%d",
                        source_nested_agent_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source nested agent "
                        "id=%s: %s", source_nested_agent_id, exc,
                    )
            if source_main_agent_id is not None:
                try:
                    agent_api.delete_agent(source_main_agent_id)
                    logger.info(
                        "Cleanup: deleted source main agent id=%d",
                        source_main_agent_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source main agent "
                        "id=%s: %s", source_main_agent_id, exc,
                    )
            if download_path is not None:
                try:
                    download_path.unlink(missing_ok=True)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to remove downloaded file %s: %s",
                        download_path, exc,
                    )
