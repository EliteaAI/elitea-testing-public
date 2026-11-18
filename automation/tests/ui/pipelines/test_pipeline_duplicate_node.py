"""UI test — Pipeline: Duplicate node end-to-end.

TMS: ELITEA-4719
(test-specs/pipelines/l2_pipeline-duplicate-node-end-to-end_ELITEA-4719.md)

Seeds ``MCP 1 (entry, DeepWiki read_wiki_structure with a fixed mapping) -> LLM 1 -> END`` via the API.
Case-text drift (AFS § Known Defects): the fixture DeepWiki MCP replaces "test-github-mcp / get_me"; the chip
attribution renders the node name space-stripped ("MCP1_copy"); after the first duplicate the copy overlaps the
original, so the original is selected by a JS click on its card (a forced centre click hits the copy).
"""

import re

import allure
import pytest
import yaml
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

T = 15_000
SAVE_TIMEOUT = 30_000
RUN_TIMEOUT = 120_000
ORIGINAL = "MCP 1"
COPY = "MCP 1_copy"
COPY_2 = "MCP 1_copy_2"
LLM = "LLM 1"
END_ID = "EliteAPipelineEnd"


def _node_yaml(pp) -> dict:
    """The open panel's node YAML (a one-item list) as a dict."""
    pp.open_node_yaml_tab(timeout=T)
    parsed = yaml.safe_load(pp.node_yaml_text())
    pp.open_node_flow_tab(timeout=T)
    return parsed[0] if isinstance(parsed, list) else parsed


@pytest.fixture
def mcp_duplicate_pipeline(pipeline_api, toolkit_api, mcp_toolkit_with_tools, request):
    """Pipeline ``MCP 1 (entry) -> LLM 1 -> END``; yields the pipeline id."""
    from fixtures.data_fixtures import _llm_node_dict

    mt = mcp_toolkit_with_tools
    toolkit = toolkit_api.get_toolkit(mt["id"])
    nodes = [
        {
            "id": ORIGINAL, "type": "mcp", "toolkit_name": mt["toolkit_name"], "tool": "read_wiki_structure",
            "input": ["input"], "output": ["messages"],
            "input_mapping": {"repoName": {"type": "fixed", "value": "facebook/react"}},
            "structured_output": False, "transition": LLM,
        },
        _llm_node_dict("END"),
    ]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=f"autotest_dup_{request.node.name}"[:32],
        description="Auto-created for ELITEA-4719",
        entry_point=ORIGINAL,
        nodes=nodes,
        tools=[toolkit],
    )
    pid = pipeline["id"]
    yield pid
    try:
        pipeline_api.delete_pipeline(pid)
    except Exception:  # noqa: BLE001 — best-effort cleanup
        pass


@pytest.mark.tms("ELITEA-4719")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-4719_pipeline-duplicate-node-end-to-end.md",
    "onetest-ai Test Case link",
)
def test_pipeline_duplicate_node_end_to_end(page, mcp_duplicate_pipeline, mcp_toolkit_with_tools):
    """Duplicate makes a disconnected, non-entry copy sharing the tool; names increment; Discard removes; copy runs."""
    pipeline_id = mcp_duplicate_pipeline
    tool_name = mcp_toolkit_with_tools["name"]
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)

    with allure.step("Step 1 — Duplicate MCP 1: toast, new card MCP 1_copy with its panel open, Save enabled"):
        pp.navigate(pipeline_id)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        expect(pp.node_card(ORIGINAL)).to_be_visible(timeout=T)
        expect(pp.save_button).to_be_disabled(timeout=T)
        pp.open_node_panel_by_card(ORIGINAL, timeout=T)
        original_yaml = _node_yaml(pp)
        pp.duplicate_selected_node(timeout=T)
        assert pp.get_toast_text(timeout=T) == f"{ORIGINAL} duplicated as {COPY}"
        expect(pp.node_card(COPY)).to_be_visible(timeout=T)
        expect(pp.node_panel_name_input).to_have_value(COPY, timeout=T)
        expect(pp.save_button).to_be_enabled(timeout=T)
        assert pp.node_card_ids() == sorted([ORIGINAL, COPY, LLM])

    with allure.step("Step 2 — The copy has the same MCP, tool and input mapping as the original"):
        copy_yaml = _node_yaml(pp)
        assert copy_yaml["id"] == COPY
        for key in ("type", "toolkit_name", "tool", "input", "input_mapping", "output", "structured_output"):
            assert copy_yaml.get(key) == original_yaml.get(key), (
                f"{key} differs: copy {copy_yaml.get(key)!r} vs original {original_yaml.get(key)!r}"
            )
        assert original_yaml["input_mapping"] == {"repoName": {"type": "fixed", "value": "facebook/react"}}

    with allure.step("Step 3 — The copy has no edges and no Entrypoint badge; the original keeps both"):
        edges = pp.canvas_edge_testids()
        assert not [e for e in edges if COPY in e], f"Copy must have no edges, got {edges}"
        assert any(f"{ORIGINAL}---{LLM}" in e for e in edges), f"Original edge to {LLM} missing: {edges}"
        assert any(f"{LLM}---{END_ID}" in e for e in edges), f"{LLM} -> END edge missing: {edges}"
        expect(pp.node_entrypoint_badge(ORIGINAL)).to_have_count(1, timeout=T)
        expect(pp.node_entrypoint_badge(COPY)).to_have_count(0, timeout=T)
        expect(pp.all_entrypoint_badges()).to_have_count(1, timeout=T)

    with allure.step("Step 4 — TOOLS has ONE entry for the MCP, Used by both nodes"):
        pp.expand_tools_section(timeout=T)
        expect(pp.toolkit_card).to_have_count(1, timeout=T)
        expect(pp.tool_card_used_by_chips(tool_name)).to_have_text([ORIGINAL, COPY], timeout=T)

    with allure.step("Step 5 — Select MCP 1 again and duplicate: toast names MCP 1_copy_2"):
        pp.select_node_by_js_click(ORIGINAL, timeout=T)
        pp.duplicate_selected_node(timeout=T)
        assert pp.get_toast_text(timeout=T) == f"{ORIGINAL} duplicated as {COPY_2}"
        expect(pp.node_card(COPY_2)).to_be_visible(timeout=T)
        assert pp.node_card_ids() == sorted([ORIGINAL, COPY, COPY_2, LLM])

    with allure.step("Step 6 — Discard removes both copies and restores the saved canvas"):
        pp.start_discard(timeout=T)
        pp.confirm_discard(timeout=T)
        expect(pp.node_card(COPY)).to_have_count(0, timeout=T)
        expect(pp.node_card(COPY_2)).to_have_count(0, timeout=T)
        assert pp.node_card_ids() == sorted([ORIGINAL, LLM])
        expect(pp.save_button).to_be_disabled(timeout=T)

    with allure.step("Step 7 — Duplicate again, make the copy the entrypoint, connect it to LLM 1 and Save"):
        pp.open_node_panel_by_card(ORIGINAL, timeout=T)
        pp.duplicate_selected_node(timeout=T)
        assert pp.get_toast_text(timeout=T) == f"{ORIGINAL} duplicated as {COPY}"
        expect(pp.node_panel_name_input).to_have_value(COPY, timeout=T)
        pp.make_selected_node_entrypoint(timeout=T)
        pp.connect_nodes(COPY, LLM)
        pp.wait_for_edge_present(COPY, LLM)
        pp.save_button.click(timeout=T)
        expect(pp.save_button).to_be_disabled(timeout=SAVE_TIMEOUT)
        expect(pp.all_entrypoint_badges()).to_have_count(1, timeout=T)
        expect(pp.node_entrypoint_badge(COPY)).to_have_count(1, timeout=T)
        expect(pp.node_entrypoint_badge(ORIGINAL)).to_have_count(0, timeout=T)

    with allure.step("Step 8 — Test Pipeline: the copy is highlighted running (not the original), run completes"):
        pp.dismiss_banner_if_present()
        pp.open_test_pipeline_panel(timeout=T)
        pp.start_running_node_recorder()
        pp.send_message_in_embedded_chat("go", timeout=T)
        pp.wait_for_embedded_chat_run_completion(timeout=RUN_TIMEOUT)
        running = pp.recorded_running_nodes()
        assert COPY in running, f"{COPY} was never highlighted running; saw {running}"
        assert ORIGINAL not in running, f"Original {ORIGINAL} must not run; saw {running}"
        chips = pp.get_embedded_chat_tool_chip_texts()
        assert any(re.search(r"\(MCP\s?1_copy\)", c) and "read_wiki_structure" in c for c in chips), (
            f"Tool call not attributed to {COPY}: {chips}"
        )
