"""Import a valid, hand-authored agent .md file — agent appears in the
list with correct config (ELITEA-1901).

Writes a plain, hand-authored ``.md`` fixture (NOT exported from the app —
that is the whole point of this case versus its round-trip siblings
ELITEA-1795/1902) with a minimal YAML frontmatter (``name``/``description``/
``model``) and instructions as the markdown BODY below the closing ``---``,
imports it via the Agents list "Import" button, and asserts: the "Import
parameters" preview dialog shows the entity card; confirming produces a
``201 Created`` and an "Import Complete" dialog listing the new agent;
re-opening the Agents dashboard shows a card with the correct name; and the
imported agent's detail page shows Name, Description, Instructions, and
Model all matching the source file verbatim.

No product defect found. One case-text imprecision found (not a product
defect): the case's Test Data row lists ``instructions`` alongside the
frontmatter keys, but the live product requires it as the markdown body
instead — filed as CLARIFICATION EliteaAI/elitea-testing-public#628 (AFS §
Known Defects). One pre-existing, unrelated React dev-mode console warning
(``validateDOMNesting`` on the Import-Complete dialog's Tooltip) fires on
every successful import — filtered out of the zero-console-errors assertion
rather than asserted against (mirrors ELITEA-1902's
``_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING`` pattern).

Spec: test-specs/agents/l2_import-valid-agent-md-file-correct-config_ELITEA-1901.md
"""

import logging
import uuid

import allure
import pytest

from config import settings
from pages.agent_detail_page import AgentDetailPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.agents")

DESC_MARKER = "ELITEA_1901_DESC_MARKER"
INSTR_MARKER = "ELITEA_1901_INSTR_MARKER"

# Known, pre-existing, unrelated React dev-mode DOM-nesting warning that
# fires on every successful Import Complete dialog render (AFS § Known
# Defects, already tracked at EliteaAI/elitea-testing-public#570) — not
# specific to this case. Filtered out of the zero-console-errors assertion
# rather than asserted against, mirroring
# test_import_agent_zip_nested_agent_dependencies.py's
# ``_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING`` pattern.
_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING = "validateDOMNesting"

# Live-confirmed rendered display name for settings.default_model_name
# ("gpt-5.2") on the Model Selector's closed state (AFS Test Data section —
# confirmed via the real Import button -> preview -> confirm -> detail page
# flow). Not a general slug->display transformation (other models render
# differently, e.g. "GPT-5 mini"), so kept as an explicit literal rather than
# derived from settings.default_model_name.upper().
EXPECTED_MODEL_DISPLAY_NAME = "GPT-5.2"


class TestImportAgentValidMdFile:
    """Import a valid, hand-authored agent .md file (ELITEA-1901, l2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1901_import-valid-agent-md-file-appears-in-list-with-correct-config.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_import_agent_valid_md_file(self, page, agent_api, tmp_path):
        """Import a hand-authored (not app-exported) ``.md`` file and verify
        the resulting Agent's Name/Description/Instructions/Model all match
        the source file verbatim.

        Steps (AFS
        test-specs/agents/l2_import-valid-agent-md-file-correct-config_ELITEA-1901.md):
        1. Navigate to the Agents dashboard; verify header, Import button,
           and existing agent cards render.
        2. Click the Import button and select the hand-authored ``.md``
           fixture; verify the "Import parameters" preview dialog opens.
        3. Verify the dialog shows an entity card for the agent (name
           matches the fixture verbatim).
        4. Confirm the dialog's Import button; verify the "Import Complete"
           success dialog lists the new agent, backed by a
           ``201 Created`` on the import_wizard endpoint.
        5. Click "Got it"; verify auto-navigation to the new Agent's detail
           page, then re-open the Agents dashboard and verify a card with
           the correct name.
        6. Open the imported agent; verify Name, Description, Instructions,
           and Model all match the source file verbatim.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        agent_name = f"el-1901-import-{unique_suffix}"
        agent_description = (
            "Externally-authored agent for ELITEA-1901 import verification. "
            f"{DESC_MARKER} must appear verbatim."
        )
        agent_instructions = (
            f"You are {agent_name}, a hand-authored test agent for ELITEA-1901. "
            f"This exact instruction sentence {INSTR_MARKER} must appear "
            "verbatim in the imported Agent."
        )

        # Critical fixture-shape finding (AFS § Test Data, CLARIFICATION
        # EliteaAI/elitea-testing-public#628): ``instructions`` MUST be the
        # markdown BODY below the closing '---', NOT a frontmatter key —
        # putting it in frontmatter silently produces an empty Instructions
        # field on import. Mirrors the app's own export shape
        # (test_export_agent_no_nested_dependencies.py: ``parts[2].strip()``
        # is the Agent's instructions).
        fixture_content = (
            "---\n"
            f"name: {agent_name}\n"
            f"description: {agent_description}\n"
            f"model: {settings.default_model_name}\n"
            "---\n"
            f"{agent_instructions}\n"
        )
        fixture_path = tmp_path / f"{agent_name}.md"
        fixture_path.write_text(fixture_content, encoding="utf-8")

        imported_agent_id = None

        # Registered before Step 1 (not inside it) so the zero-console-errors
        # assertion genuinely covers the FULL flow — dashboard load included,
        # not just upload-onward (mirrors ELITEA-1902's registration point).
        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 — Navigate to the Agents dashboard; verify header, "
                "Import button, and existing agent cards render"
            ):
                agents_list_page = AgentsListPage(page)
                agents_list_page.navigate()
                assert agents_list_page.import_button.is_visible(), (
                    "Import button should be visible in the Agents dashboard toolbar"
                )
                assert agents_list_page.get_agent_card_names(), (
                    "Agents dashboard should render at least one existing agent card"
                )

            with allure.step(
                "Step 2 — Click the Import button and select the "
                "hand-authored .md fixture; verify the 'Import parameters' "
                "preview dialog opens"
            ):
                # import_agent() performs the click + file-chooser handling
                # in one call; a successfully-rendered "Import parameters"
                # dialog (asserted inside the method) is the observable
                # proof that the native file chooser opened and accepted
                # the file (mirrors ELITEA-1795's Step 2 justification).
                agents_list_page.import_agent(str(fixture_path), timeout=IMPORT_TIMEOUT)
                assert agents_list_page.import_preview_dialog.is_visible(), (
                    "Import parameters dialog should be visible after "
                    "selecting the hand-authored .md fixture"
                )

            with allure.step(
                "Step 3 — Verify the dialog shows an entity card for the "
                "agent (name matches the fixture verbatim)"
            ):
                assert agents_list_page.import_preview_name.is_visible(), (
                    "Import dialog should preview the fixture Agent's name"
                )
                assert agents_list_page.import_preview_name.text_content() == agent_name, (
                    "Import dialog's Main-entity name preview should show "
                    "the fixture's name verbatim"
                )

            with allure.step(
                "Step 4 — Confirm the dialog's Import button; verify the "
                "'Import Complete' success dialog lists the new agent, "
                "backed by a 201 Created on the import_wizard endpoint"
            ):
                with page.expect_response(
                    lambda r: (
                        "/elitea_core/import_wizard/prompt_lib/" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=IMPORT_TIMEOUT,
                ) as import_response_info:
                    agents_list_page.confirm_agent_import(timeout=IMPORT_TIMEOUT)

                assert import_response_info.value.status == 201, (
                    "Import wizard POST should return 201 Created, got: "
                    f"{import_response_info.value.status}"
                )
                assert agents_list_page.import_complete_dialog.is_visible(), (
                    "Success dialog should be visible after confirming the import"
                )
                assert agent_name in agents_list_page.import_complete_agents_list.text_content(), (
                    "Success dialog's Agents list should include the "
                    "imported Agent's name — confirming a new Agent entity "
                    "was created"
                )

            with allure.step(
                "Step 5 — Click 'Got it'; verify auto-navigation to the new "
                "Agent's detail page, then re-open the Agents dashboard and "
                "verify a card with the correct name"
            ):
                imported_agent_id = agents_list_page.confirm_import_complete(
                    timeout=NAVIGATION_TIMEOUT,
                )
                detail_page = AgentDetailPage(page)
                detail_page.verify_on_detail_page(expected_agent_id=imported_agent_id)
                logger.info("Imported agent created — id=%d", imported_agent_id)

                agents_list_page.navigate()
                assert agent_name in agents_list_page.get_agent_card_names(), (
                    f"Agents dashboard should show a card named {agent_name!r} "
                    "after re-opening the list post-import"
                )

            with allure.step(
                "Step 6 — Open the imported agent; verify Name, "
                "Description, Instructions, and Model all match the source "
                "file verbatim"
            ):
                detail_page.navigate(imported_agent_id)

                assert detail_page.get_name() == agent_name, (
                    "Imported agent's Name field should match the fixture's "
                    "name verbatim"
                )
                imported_description = detail_page.get_description()
                assert DESC_MARKER in imported_description, (
                    f"Imported agent's Description should contain the "
                    f"planted marker {DESC_MARKER!r} verbatim, got: "
                    f"{imported_description!r}"
                )
                assert imported_description == agent_description, (
                    "Imported agent's Description field should match the "
                    "fixture's description verbatim"
                )
                imported_instructions = detail_page.get_instructions()
                assert INSTR_MARKER in imported_instructions, (
                    f"Imported agent's Instructions should contain the "
                    f"planted marker {INSTR_MARKER!r} verbatim, got: "
                    f"{imported_instructions!r}"
                )
                assert imported_instructions == agent_instructions, (
                    "Imported agent's Instructions field should match the "
                    "fixture's markdown body verbatim (not empty — the "
                    "instructions-as-body fixture shape, per CLARIFICATION "
                    "#628)"
                )

                # Axis 2 addition — Model is part of an Agent's config just
                # as much as Name/Description/Instructions (AFS Axis 2).
                selected_model = detail_page.get_selected_model_name()
                assert selected_model == EXPECTED_MODEL_DISPLAY_NAME, (
                    "Imported agent's Model selector should reflect the "
                    f"fixture's model ({settings.default_model_name!r}), "
                    f"expected {EXPECTED_MODEL_DISPLAY_NAME!r}, got: "
                    f"{selected_model!r}"
                )

                # Axis 2 addition — zero (unfiltered) console errors across
                # the entire upload -> preview -> confirm -> navigate flow.
                real_console_errors = [
                    m.text for m in console_messages
                    if _KNOWN_NONBLOCKING_CONSOLE_SUBSTRING not in m.text
                ]
                assert not real_console_errors, (
                    "Expected no (unfiltered) console errors during the "
                    f"import flow, got: {real_console_errors!r}"
                )

        finally:
            # Cleanup per AFS: delete the imported agent (mirrors
            # ELITEA-1794/1795/1894/1902's cleanup pattern). The fixture
            # .md file lives under pytest's tmp_path and is auto-cleaned —
            # no manual removal needed.
            if imported_agent_id is not None:
                try:
                    agent_api.delete_agent(imported_agent_id)
                    logger.info(
                        "Cleanup: deleted imported agent id=%d", imported_agent_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete imported agent id=%s: %s",
                        imported_agent_id, exc,
                    )
