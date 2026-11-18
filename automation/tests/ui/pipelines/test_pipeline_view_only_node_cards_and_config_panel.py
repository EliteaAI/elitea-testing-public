"""UI test — Pipeline: view-only node cards and node configuration panel.

TMS: ELITEA-4715
(test-specs/pipelines/l2_pipeline-view-only-node-cards-and-config-panel_ELITEA-4715.md)

Seeds ``Agent 1 (entry) -> Toolkit 1 -> Code 1 -> END`` via the API, then verifies that canvas cards are
view-only summaries, the panel mirrors the card summary, the entrypoint can be moved from the panel, and
the Name field validates / commits / persists.

Case-text drift (AFS § Case-text clarifications): Step 8 "Save is disabled" does not hold on DEV (the
invalid draft is local to the field, Save stays enabled) -> asserted message + aria-invalid + unchanged
card title instead. Step 9: the card title updates on commit (Enter/blur), not per keystroke.
"""

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_TIMEOUT = 20_000
NEW_NAME = "Code renamed"
SUMMARY_SEPARATOR = " › "


@pytest.fixture
def pipeline_agent_toolkit_code(
    pipeline_api, agent_api, agent_id, github_toolkit_with_selected_tools, toolkit_api, request
):
    """Pipeline ``Agent 1 -> Toolkit 1 -> Code 1 -> END`` (entry Agent 1); yields (pipeline id, agent name).

    ``tools`` carries BOTH the full toolkit object AND an application entry for the agent, otherwise the
    panel shows "Toolkit/Agent not found" (AFS Preconditions, LOAD-BEARING).
    """
    agent = agent_api.get_agent(agent_id)
    toolkit = toolkit_api.get_toolkit(github_toolkit_with_selected_tools["id"])
    nodes = [
        {
            "id": "Agent 1", "type": "agent", "input": ["input"], "output": ["messages"],
            "input_mapping": {
                "task": {"type": "fixed", "value": "Say hello"},
                "chat_history": {"type": "fixed", "value": []},
            },
            "tool": agent["name"], "transition": "Toolkit 1",
        },
        {
            "id": "Toolkit 1", "type": "toolkit", "toolkit_name": toolkit["toolkit_name"],
            "tool": "search_issues", "input": ["input"], "output": ["messages"],
            "input_mapping": {"search_query": {"type": "fixed", "value": "bug"}},
            "transition": "Code 1",
        },
        {
            "id": "Code 1", "type": "code", "code": {"type": "fixed", "value": '{"x": 1}'},
            "input": ["input"], "output": ["messages"], "transition": "END",
        },
    ]
    tools = [
        toolkit,
        {
            "type": "application", "name": agent["name"], "description": "d",
            "settings": {
                "application_id": agent_id,
                "application_version_id": agent["versions"][0]["id"],
            },
        },
    ]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=f"autotest_viewonly_{request.node.name}"[:32],
        description="Auto-created for ELITEA-4715",
        entry_point="Agent 1",
        nodes=nodes,
        tools=tools,
    )
    pid = pipeline["id"]
    yield pid, agent["name"]
    try:
        pipeline_api.delete_pipeline(pid)
    except Exception:  # noqa: BLE001 — best-effort cleanup
        pass


@pytest.mark.tms("ELITEA-4715")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-4715_pipeline-view-only-node-cards-and-node-configuration-panel.md",
    "onetest-ai Test Case link",
)
def test_pipeline_view_only_node_cards_and_config_panel(page, pipeline_agent_toolkit_code):
    """Cards are view-only; panel mirrors the card; entrypoint moves; Name validates, commits and persists."""
    pipeline_id, agent_name = pipeline_agent_toolkit_code
    # Tall viewport: the DEV corner banner otherwise covers the panel footer (AFS Preconditions).
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)

    with allure.step("Step 1 — Open the pipeline: cards Agent 1 / Toolkit 1 / Code 1 and End are on the canvas"):
        pp.navigate(pipeline_id)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        canonical_url = page.url
        for node in ("Agent 1", "Toolkit 1", "Code 1"):
            expect(pp.node_card(node)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.all_node_cards()).to_have_count(3)
        expect(pp.end_node()).to_be_visible()
        expect(pp.end_node()).to_contain_text("End")

    with allure.step("Step 2 — Cards show header + summary only; no editable controls on any node (incl. End)"):
        for node, node_type in (("Agent 1", "Agent"), ("Toolkit 1", "Toolkit"), ("Code 1", "Code")):
            expect(pp.node_card_name(node)).to_have_text(node)
            expect(pp.node_card_type(node)).to_have_text(node_type)
            expect(pp.node_summary(node)).to_be_visible()
            expect(pp.node_editable_controls(node)).to_have_count(0)
        expect(pp.node_editable_controls("END")).to_have_count(0)

    with allure.step("Step 3 — Only Agent 1 carries the Entrypoint badge"):
        expect(pp.node_entrypoint_badge("Agent 1")).to_have_count(1)
        expect(pp.all_entrypoint_badges()).to_have_count(1)

    with allure.step("Step 4 — Toolkit 1 card summary is mirrored in the panel's Basic section"):
        primary = pp.node_summary_primary("Toolkit 1")
        expect(primary).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        card_text = (primary.text_content() or "").strip()
        halves = [h.strip() for h in card_text.split(SUMMARY_SEPARATOR.strip())]
        assert len(halves) == 2 and all(halves), f"Toolkit summary should read '<toolkit> › <tool>', got {card_text!r}"
        pp.open_node_panel_by_card("Toolkit 1", timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel()).to_be_visible()
        basic = pp.node_panel_basic_section()
        # The card truncates the toolkit name: compare each card half contained in the panel text.
        for half in halves:
            expect(basic).to_contain_text(half)
        assert "search_issues" in halves[1]

    with allure.step("Step 5 — Clicking the Agent 1 card switches the panel; the agent name is mirrored"):
        agent_primary = (pp.node_summary_primary("Agent 1").text_content() or "").strip()
        assert agent_primary == agent_name, f"Agent card primary should be the agent name, got {agent_primary!r}"
        pp.open_node_panel_by_card("Agent 1", timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_basic_section()).to_contain_text(agent_primary)

    with allure.step("Step 6 — Close the panel"):
        pp.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_name_input).to_have_count(0)

    with allure.step("Step 7 — Make Code 1 the entrypoint from the panel footer"):
        pp.open_node_panel_by_card("Code 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.make_node_entrypoint("Code 1", timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_entrypoint_state()).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_entrypoint_badge("Code 1")).to_have_count(1)
        expect(pp.node_entrypoint_badge("Agent 1")).to_have_count(0)
        expect(pp.all_entrypoint_badges()).to_have_count(1)

    with allure.step("Step 8 — Clearing Name shows 'Name is required'; the card title is not committed"):
        pp.node_panel_name_input.fill("")
        expect(pp.node_panel_name_error()).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_name_input).to_have_attribute("aria-invalid", "true")
        expect(pp.node_card_name("Code 1")).to_have_text("Code 1")

    with allure.step("Step 9 — Typing a new Name clears the error; the card title updates on commit (Enter)"):
        pp.rename_node_in_panel(NEW_NAME, timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_name_error()).to_have_count(0)
        expect(pp.node_card(NEW_NAME)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_card("Code 1")).to_have_count(0)
        expect(pp.node_panel_name_input).to_have_value(NEW_NAME)

    with allure.step("Step 10 — Save and reload: renamed card and Entrypoint badge persist"):
        pp.save_and_wait_for_saved(timeout=SAVE_TIMEOUT)
        page.goto(canonical_url)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        expect(pp.node_card(NEW_NAME)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_card("Code 1")).to_have_count(0)
        expect(pp.node_entrypoint_badge(NEW_NAME)).to_have_count(1)
        expect(pp.all_entrypoint_badges()).to_have_count(1)
