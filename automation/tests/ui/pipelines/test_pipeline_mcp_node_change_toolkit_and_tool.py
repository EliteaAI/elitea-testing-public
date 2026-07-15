"""UI test — MCP Integration in Pipeline: change MCP node Toolkit and Tool.

TMS: ELITEA-1954
(test-specs/pipelines/l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md)

Opens a pipeline whose MCP node is already configured with a Toolkit and
Tool, switches the Toolkit to a second attached MCP, verifies the Tool
dropdown resets and repopulates with exactly the new MCP's own tools (no
stale leakage), selects a new Tool, fills the resulting Input-mapping
fields, saves, and confirms everything persists through a full page reload.
"""

import logging

import pytest
import allure

from pages.pipeline_detail_page import PipelineDetailPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# The two Input-mapping parameters "ask_question" requires (raw schema keys —
# NOT the capitalized display labels the case text uses ("RepoName"/"Question");
# see McpNode/InputMapping.jsx: variableName is a display-only capitalization
# of these exact keys, and the AFS's recommended dynamic testid is keyed on
# the raw schema key, not the display label).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1954_mcp-integration-in-pipeline-change-toolkit-and-tool.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_change_toolkit_and_tool(page, mcp_pipeline_with_toolkits):
    """Change an MCP node's Toolkit and Tool; verify reset/repopulate + persistence."""
    fixture = mcp_pipeline_with_toolkits
    pipeline_id = fixture["id"]
    node_id = fixture["node_id"]
    initial_toolkit_name = fixture["toolkit_name"]  # "RemoteGithub"
    initial_tool = fixture["tool"]  # "search_repositories"
    new_toolkit_name = fixture["other_toolkit_name"]  # the deepwiki MCP's toolkit_name
    new_tools = set(fixture["other_tools"])  # {"read_wiki_structure", "read_wiki_contents", "ask_question"}
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node
    # click, dropdown opens, tool selection, Input-mapping render) are
    # captured — not just from Step 9 onward. AFS Expected Results require
    # "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the pipeline; verify configuration panel loads"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — AFS Known Defects:
        # a bare /pipelines/all/{id} URL (no query params) 404s; reloading THIS
        # captured URL (which already carries ?viewMode=owner) avoids that.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step("Step 2 — Locate the MCP node on the canvas; config fields visible inline"):
        mcp_node = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        assert mcp_node, "MCP node should be present on the canvas with a non-empty data-id"
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible inline on the canvas card — "
            "no separate click-to-open action needed (live product simplification, "
            "see AFS Coverage Map row 2)"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), "Tool select should be visible inline"

    with allure.step("Step 3 — Read current Toolkit and Tool values; match preconfigured state"):
        current_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        current_tool = pipeline_page.get_mcp_node_tool_value()
        assert current_toolkit == initial_toolkit_name, (
            f"Toolkit should show the preconfigured value {initial_toolkit_name!r}, got {current_toolkit!r}"
        )
        assert current_tool == initial_tool, (
            f"Tool should show the preconfigured value {initial_tool!r}, got {current_tool!r}"
        )

    with allure.step("Step 4 — Open Toolkit dropdown; verify it lists every MCP attached in TOOLS"):
        pipeline_page.open_mcp_node_toolkit_select()
        listed_toolkits = set(pipeline_page.get_open_listbox_option_names())
        assert listed_toolkits == {initial_toolkit_name, new_toolkit_name}, (
            f"Toolkit dropdown should list exactly the 2 attached MCPs "
            f"{{{initial_toolkit_name!r}, {new_toolkit_name!r}}}, got {listed_toolkits!r}"
        )
        # Close by selecting the new toolkit directly (step 5) rather than a
        # separate close action — the AFS steps 4→5 are one continuous flow.
        pipeline_page.select_open_listbox_option(new_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 5 — Select the other MCP; Toolkit combobox shows the new name"):
        new_toolkit_value = pipeline_page.get_mcp_node_toolkit_value()
        assert new_toolkit_value == new_toolkit_name, (
            f"Toolkit select should now show {new_toolkit_name!r}, got {new_toolkit_value!r}"
        )

    with allure.step(
        "Step 6 — Tool resets to empty immediately, then repopulates with exactly the new MCP's tools"
    ):
        # Immediately after the Toolkit change and before opening the Tool
        # dropdown: the Tool select must show no stale value from the
        # previous MCP (RemoteGithub's search_repositories).
        reset_tool_value = pipeline_page.get_mcp_node_tool_value(timeout=UI_ELEMENT_TIMEOUT)
        assert reset_tool_value == "", (
            f"Tool select should be visibly empty right after the Toolkit change, "
            f"got {reset_tool_value!r}"
        )

        pipeline_page.open_mcp_node_tool_select()
        listed_tools = set(pipeline_page.get_open_listbox_option_names())
        assert listed_tools == new_tools, (
            f"Tool dropdown should show exactly the new MCP's own tools {new_tools!r}, "
            f"got {listed_tools!r} — no stale tools from the previous MCP should leak through"
        )
        assert initial_tool not in listed_tools, (
            f"Previous MCP's tool {initial_tool!r} must not leak into the new Tool dropdown"
        )

    with allure.step("Step 7 — Select a tool from the new MCP's list; Tool combobox shows it"):
        pipeline_page.select_open_listbox_option("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        selected_tool = pipeline_page.get_mcp_node_tool_value()
        assert selected_tool == "ask_question", (
            f"Tool select should show 'ask_question' after selection, got {selected_tool!r}"
        )

    with allure.step(
        "Step 8 — Input mapping (required 2) appears with the new tool's actual parameters"
    ):
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 2)' section should appear for ask_question's "
            "2 required parameters (repoName, question)"
        )
        # Both Value fields for the new tool's parameters must be present —
        # this IS the "Input/Output variables update according to new tool"
        # behavior (per-tool-parameter mapping), distinct from the separate,
        # tool-agnostic Input/Output state-variable selects (which do NOT
        # change with tool selection — see AFS Coverage Map row 8).
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "repoName", timeout=UI_ELEMENT_TIMEOUT
        ), "repoName Value field should be visible"
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "question", timeout=UI_ELEMENT_TIMEOUT
        ), "question Value field should be visible"

    with allure.step("Step 9 — Fill Input-mapping fields; Save; verify 201 + no console errors"):
        pipeline_page.fill_mcp_node_input_mapping_value("repoName", _REPO_NAME_VALUE)
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)

        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 10 — Reload via the canonical URL; new Toolkit/Tool/Input-mapping persisted"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)

        persisted_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        persisted_tool = pipeline_page.get_mcp_node_tool_value()
        assert persisted_toolkit == new_toolkit_name, (
            f"Toolkit should persist as {new_toolkit_name!r} after reload, got {persisted_toolkit!r}"
        )
        assert persisted_tool == "ask_question", (
            f"Tool should persist as 'ask_question' after reload, got {persisted_tool!r}"
        )
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 2) section should still be present after reload"
        )
        # Axis 2 addition (AFS): the case only mentions Toolkit/Tool
        # persisting — also assert the input-mapping VALUES survive, since a
        # regression where the tool changes correctly but its filled-in
        # parameter values are silently dropped on save/reload would
        # otherwise go undetected.
        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE, (
            "repoName Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE, (
            "question Input-mapping value should persist through reload"
        )
