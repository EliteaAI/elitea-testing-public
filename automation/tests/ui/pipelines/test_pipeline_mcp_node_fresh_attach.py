"""UI test — Pipeline MCP node integration: fresh attach -> add node -> configure -> persist.

TMS: ELITEA-2037
(test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md)

On a fresh, empty pipeline (no nodes/edges pre-seeded): attaches an MCP
toolkit via the TOOLS section's "+ MCP" button, adds a fresh MCP node via
the canvas "Add node" menu, verifies the node's static config fields render
immediately while the Tool select + Input-mapping accordions stay absent
until a Toolkit is chosen, selects the Toolkit then a Tool with required
parameters, fills the Input-mapping values, sets the tool-agnostic
Input/Output state-variable selects, saves, and confirms everything
persists through a full page reload.

Distinct from the sibling MCP-node cases already automated on this suite:
- ELITEA-1954 (test_pipeline_mcp_node_change_toolkit_and_tool.py) starts from
  an ALREADY-CONFIGURED node and switches Toolkit/Tool.
- ELITEA-1955 (test_pipeline_mcp_node_empty_toolkit_before_attach.py) adds the
  node BEFORE any MCP is attached to TOOLS (inverse ordering).
This case is the "happy path from scratch": attach-to-Tools, then add-node,
in the case's own step order, with full static-field-presence assertions
(Interrupt before/after, Structured output) that neither sibling covers.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# The two Input-mapping parameters "ask_question" requires (raw schema keys —
# NOT the capitalized display labels the case text uses ("RepoName"/"Question");
# see McpNode/InputMapping.jsx: variableName is a display-only capitalization
# of these exact keys — same precedent as the sibling ELITEA-1954/1955 tests).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"

# ELITEA-1952 execution constants. The repo name is sent as the chat message
# and reaches the MCP tool through the node's `repoName` Input-mapping bound to
# the `input` state variable.
_EXECUTION_REPO = "AsyncFuncAI/deepwiki-open"
# A live MCP + LLM round trip measured ~40 s end to end during analysis; the
# wait is on the response-complete marker, never a sleep.
EXECUTION_RESPONSE_TIMEOUT = 180_000
# Shape-only floor for a nondeterministic generated answer — a real DeepWiki
# answer ran ~1 kB; anything under this is a stub, an error string or empty.
MIN_TOOL_ANSWER_LENGTH = 200
# Horizontal drag that clears a freshly-added MCP node of ReactFlow's
# bottom-left Control Panel once its Input-mapping rows render.
MCP_NODE_CLEARANCE_DX = 450


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2037_pipeline-mcp-node-integration.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_fresh_attach(page, pipeline_id, mcp_toolkit_with_tools):
    """Fresh-attach an MCP, add + configure an MCP node, save, verify reload persistence."""
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]  # exact popper row text, not space-stripped
    mcp_toolkit_name = fixture["toolkit_name"]  # cleaned select-option value
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (attach,
    # node add, dropdown opens, tool selection, save, reload) are captured —
    # AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — Navigate to the fresh, empty pipeline; verify configuration panel + canvas load"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — a bare
        # /pipelines/all/{id} URL (no query params) 404s (ELITEA-1954 AFS
        # Known Defects); reloading THIS captured URL avoids that.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )
        assert pipeline_page.get_node_ids() == ["END"], (
            "A fresh pipeline's canvas should show only the END node before any node is added"
        )

    with allure.step('Step 2 — Click TOOLS "+ MCP"; verify the MCP-picker popup opens'):
        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ MCP' popper should open"
        assert pipeline_page.get_mcp_popper_search_input_count(popper) > 0, (
            "'+ MCP' popper should render a toolkit-search-input search field"
        )
        assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (
            "'+ MCP' popper should list at least one toolkit-menu-item result row "
            "(the project's available MCPs, including the freshly-provisioned fixture MCP)"
        )

    with allure.step("Step 3 — Select the fixture MCP from the popup"):
        # Regression check for a fix-round finding (2026-08-04): this AFS
        # originally claimed pipeline-level MCP-attach fires "no persistence
        # request ... only GET calls" (contradicted by ELITEA-1955's sibling
        # test using this same page-object method) — corrected in the AFS's
        # Test Steps step 4 / § Network Behavior. `select_mcp_in_popper()`
        # hard-blocks on `page.expect_response(... PATCH ... status == 201
        # ...)` before returning, so it is itself the regression guard: if a
        # future product change ever stops persisting on attach (reverting to
        # the originally-claimed GET-only behavior, or vice versa breaking
        # the immediate PATCH), this call times out and the step fails
        # loudly instead of silently passing on a stale assumption.
        attach_response = pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "MCP attach should return the persisted toolkit payload from the "
            "immediate PATCH .../tool/prompt_lib/{project}/ 201 response — the "
            "pipeline Tools-section attach auto-persists on selection, same as "
            "the agent-level Tools section (#530), not deferred to pipeline Save"
        )

    with allure.step(
        "Step 4 — Verify the MCP appears attached in TOOLS as a flat-list card (no MCP sub-tab — "
        "CLARIFICATION EliteaAI/elitea-testing-public#1149, sibling of #530)"
    ):
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert not console_errors, f"Attaching the MCP should not introduce console errors: {console_errors}"

    with allure.step(
        'Step 5 — Click "Add node" -> "MCP"; a fresh MCP node appears with no auto-created edge'
    ):
        pipeline_page.add_node("MCP", timeout=UI_ELEMENT_TIMEOUT)
        mcp_node_id = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        assert mcp_node_id, "MCP node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 6 — Static config fields present immediately (before any Toolkit is selected); "
        "Tool select + Input-mapping accordions are absent"
    ):
        assert pipeline_page.entry_point_trigger_select.is_visible(), (
            "Entry-point Trigger select ('Chat Message') should be visible — the fresh MCP node "
            "is the pipeline's only node, so it auto-becomes the entry point"
        )
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible inline on the canvas card"
        )
        assert pipeline_page.mcp_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.mcp_node_output_select.is_visible(), "Output select should be visible inline"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(mcp_node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.mcp_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        assert pipeline_page.mcp_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )
        # Disabled-state assertions (AFS step 6 — confirmed live): Interrupt
        # before is disabled because this node is the entry point
        # (CommonInterruptSettings.jsx entry_point === id gating); Interrupt
        # after is disabled because the node's default transition is END;
        # Structured output has no such gating and stays enabled.
        assert pipeline_page.is_node_interrupt_before_toggle_disabled(mcp_node_id), (
            "Interrupt before should be disabled — this node is the pipeline's entry point"
        )
        assert pipeline_page.mcp_node_interrupt_after_toggle.is_disabled(), (
            "Interrupt after should be disabled — the node's default transition is END"
        )
        assert not pipeline_page.mcp_node_structured_output_toggle.is_disabled(), (
            "Structured output should be enabled (no entry/transition gating)"
        )
        # Negative/absence assertions (AFS Axis 2) — a naive implementation
        # might only assert presence-after-configuration and silently skip
        # the pre-Toolkit-select empty state, which is exactly the state a
        # future regression (Tool select rendering stale/wrong options
        # before a Toolkit is chosen) would need to be caught by.
        assert pipeline_page.get_mcp_node_tool_value(timeout=2000) == "", (
            "Tool select should NOT be rendered (or should read empty) before a Toolkit is selected"
        )
        assert not pipeline_page.is_input_mapping_section_visible(2, timeout=2000), (
            "INPUT MAPPING (required N) should NOT be rendered before a Toolkit is selected"
        )

    with allure.step("Step 7 — Select the attached MCP from the Toolkit dropdown"):
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit select should show {mcp_toolkit_name!r} after selection"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), (
            "A Tool combobox should render on the node once a Toolkit with tools is selected"
        )

    with allure.step(
        "Step 8 — Select 'ask_question' Tool; Input mapping (required 2) appears with repoName/question"
    ):
        pipeline_page.select_mcp_node_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question", (
            "Tool select should show 'ask_question' after selection"
        )
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 2)' section should appear for ask_question's "
            "2 required parameters (repoName, question)"
        )
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "repoName", timeout=UI_ELEMENT_TIMEOUT
        ), "repoName Value field should be visible"
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "question", timeout=UI_ELEMENT_TIMEOUT
        ), "question Value field should be visible"

    with allure.step("Step 9 — Fill the required Input-mapping Value fields (Type left at default Fixed)"):
        pipeline_page.fill_mcp_node_input_mapping_value("repoName", _REPO_NAME_VALUE)
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)

        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

    with allure.step("Step 10 — Set Input combobox to 'input' and Output combobox to 'messages'"):
        pipeline_page.select_mcp_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )
        pipeline_page.select_mcp_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 11 — Save; verify 201 + no console errors across the whole flow"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 12 — Reload via the canonical URL; Tools attachment + full node config persist byte-for-byte"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            "TOOLS section should still show the attached MCP card after reload"
        )
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit should persist as {mcp_toolkit_name!r} after reload"
        )
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question", (
            "Tool should persist as 'ask_question' after reload"
        )
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 2) section should still be present after reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE, (
            "repoName Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE, (
            "question Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-1952_mcp-in-pipeline-add-to-tools-configure-and-execute.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_executes_selected_tool(page, pipeline_id, mcp_toolkit_with_tools):
    """ELITEA-1952 — attach an MCP, configure an MCP node, save, EXECUTE, assert tool output.

    Extends the ELITEA-2037 flow above (same file, same fixtures, same page
    object) with the three observables that case does not assert
    (test-specs/pipelines/lextend_mcp-in-pipeline-add-to-tools-configure-and-
    execute_ELITEA-1952.md § Gap assertions):

      1. the TOOLS section offers ALL FOUR attachment triggers;
      2. the attached MCP card's composition — name text, "Show tools" toggle
         and connection-status indicator;
      3. the pipeline actually EXECUTES and the MCP node returns its selected
         tool's output (the case's § Expected Final State, asserted nowhere on
         this suite before).

    Kept as its own test rather than appended to `test_mcp_node_fresh_attach`
    (the AFS recommended appending gaps 1-2 there): the covering test is a
    merged, fully-deterministic merge-gate participant, and Hard Rule 3's
    additive-only discipline says do not edit it when the same assertions sit
    naturally on this case's own path. It also keeps ELITEA-1952 atomic — one
    case, one test, one verdict.

    Test-data substitution (declared, AFS § Preconditions): the case names MCP
    "EliteaMCP" / tool `get_auth_user` / output `user_info`; neither exists in
    this project and `get_auth_user` takes no parameters (it would skip the
    Input-mapping surface entirely). Substituted with the DeepWiki fixture MCP,
    its `ask_question` tool and output `messages` — the same substitution
    already merged for ELITEA-2037/2065/1954/1955. This is test DATA only:
    every asserted observable (the attach PATCH, the card, the tool chip, the
    answer body) is produced by the live system, nothing is stubbed.
    """
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]
    mcp_toolkit_name = fixture["toolkit_name"]
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Open the fresh, empty pipeline; canvas loads"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        assert pipeline_page.get_node_ids() == ["END"], (
            "A fresh pipeline's canvas should show only the END node before any node is added"
        )

    with allure.step(
        "Steps 2-3 — TOOLS section exposes all four attachment triggers "
        "(+ Toolkit / + MCP / + Agent / + Pipeline)"
    ):
        # Case step 3. The visible labels carry NO leading "+" (the "+" is a
        # separate icon), so these are located by testid, never by a "+ MCP"
        # string — AFS § Case-text drift 3.
        expect(pipeline_page.add_toolkit_button).to_be_visible()
        expect(pipeline_page.add_mcp_button).to_be_visible()
        expect(pipeline_page.add_agent_button).to_be_visible()
        expect(pipeline_page.add_pipeline_button).to_be_visible()

    with allure.step("Steps 4-6 — Open the '+ MCP' picker and select the fixture MCP"):
        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ MCP' popper should open"
        assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (
            "'+ MCP' popper should list the project's available MCPs"
        )
        attach_response = pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "Selecting an MCP should auto-persist via PATCH .../tool/prompt_lib/{project}/ 201"
        )

    with allure.step(
        "Step 7 — The attached card renders the MCP's name, its 'Show tools' toggle "
        "and its connection-status indicator"
    ):
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert pipeline_page.get_toolkit_card_name_text(mcp_display_name) == mcp_display_name, (
            "The card's name element should read the attached MCP's display name"
        )
        assert pipeline_page.is_toolkit_card_tools_toggle_visible(mcp_display_name), (
            "The card should offer its 'Show tools' toggle (the MCP has a non-empty tool list)"
        )
        # The card's connection indicator keeps one stable testid and carries
        # its state in `data-connected` (PR #581 ruling). A freshly-provisioned
        # Remote MCP has never been logged in, so it reads disconnected.
        assert pipeline_page.get_toolkit_card_connection_state(mcp_display_name) == "false", (
            "A freshly-attached, never-authenticated Remote MCP should report a disconnected "
            "connection status on its TOOLS card"
        )

    with allure.step("Steps 8-11 — Add an MCP node from the canvas 'Add node' menu"):
        pipeline_page.add_node("MCP", timeout=UI_ELEMENT_TIMEOUT)
        mcp_node_id = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        assert mcp_node_id, "MCP node should be present on the canvas with a non-empty data-id"
        # Move the node clear of ReactFlow's bottom-left Control Panel: a
        # fresh node spawns above it, and once the Input-mapping rows render
        # they extend down over the panel, whose "Fit View" button then
        # intercepts the pointer on the Type select's click (live-hit this
        # session — Playwright named `rf__controls` as the intercepting
        # subtree). Same `move_node()` remedy as
        # test_pipeline_interrupt_before_after_toggles.py:87.
        pipeline_page.move_node(mcp_node_id, dx=MCP_NODE_CLEARANCE_DX, dy=0)

    with allure.step("Steps 12-16 — Configure the node: Toolkit then Tool"):
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name
        pipeline_page.select_mcp_node_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question"
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 2)' should appear for ask_question's 2 required parameters"
        )

    with allure.step(
        "Step 17 — Bind repoName to the chat input (Type=Variable) and fix the question; "
        "set Input='input' / Output='messages'"
    ):
        # repoName as a Variable bound to `input` makes the chat message the
        # repository under question, so the execution below is self-contained.
        pipeline_page.select_mcp_node_input_mapping_type(
            "repoName", "Variable", timeout=UI_ELEMENT_TIMEOUT
        )
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

        pipeline_page.select_mcp_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_input_value() == "input"
        pipeline_page.select_mcp_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_output_value() == "messages"

    with allure.step("Steps 18-19 — Save; the MCP node is wired to END automatically"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        # Case step 18 says "connect START -> MCP 1 -> END". There is no START
        # node in this product (the entry point is a node PROPERTY), and the
        # MCP 1 -> END edge is created from the node's default transition, not
        # by the user — AFS § Case-text drift 2. The assertion that carries the
        # case's intent is that the edge exists.
        assert pipeline_page.edge_testid_present(mcp_node_id, "EliteAPipelineEnd"), (
            f"An edge {mcp_node_id} -> END should exist after saving (auto-created from the "
            "node's default transition — there is no START node to connect)"
        )

    with allure.step("Step 20 — Execute the pipeline from the embedded chat"):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        # Enter does NOT submit in this composer — the send button is required
        # (AFS § Gotchas); send_message_in_embedded_chat clicks it.
        pipeline_page.send_message_in_embedded_chat(_EXECUTION_REPO)
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count, timeout=EXECUTION_RESPONSE_TIMEOUT
        )

    with allure.step(
        "Step 21 — The MCP node invoked the SELECTED tool and its output came back"
    ):
        # The tool chip is the proof the MCP node ran the configured tool: a
        # non-empty answer alone would also pass if the pipeline silently fell
        # back to a plain LLM reply with no MCP call. Text fills in
        # progressively while the call resolves, so poll before reading.
        tool_chips = pipeline_page.get_last_embedded_chat_tool_chip_locator()
        expect(tool_chips.first).to_contain_text(
            f"{mcp_toolkit_name}: ask_question", timeout=EXECUTION_RESPONSE_TIMEOUT
        )

        answer = pipeline_page.get_last_embedded_chat_message_text()
        # Deliberately NOT an exact-text assertion: the answer is generated by
        # DeepWiki + an LLM. Assert the shape (real content came back), per
        # .agents/testing.md § How to test a NONDETERMINISTIC producer.
        assert len(answer) > MIN_TOOL_ANSWER_LENGTH, (
            "The MCP tool's answer should come back as real, non-trivial content — got "
            f"{len(answer)} chars: {answer[:200]!r}"
        )

        assert not console_errors, (
            f"Attaching, configuring and executing the MCP pipeline should not "
            f"introduce console errors: {console_errors}"
        )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-1953_mcp-node-input-mapping-configuration.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_input_mapping_type_and_toggles_persist(page, pipeline_id, mcp_toolkit_with_tools):
    """ELITEA-1953 — MCP-node Input-mapping Type control, toggle defaults, and their persistence.

    Extends the ELITEA-2037 flow above with what that case never reads
    (test-specs/pipelines/lextend_mcp-node-input-mapping-configuration_
    ELITEA-1953.md § Gap assertions): the per-parameter mapping **Type**
    select — its default, its option set, that a change is per-row, that it
    swaps the row's Value widget — plus the three toggles' default OFF state,
    and all of it surviving Save + a full page reload.

    Reaching the case's precondition ("a pipeline with an MCP node that has a
    Toolkit") is TRANSIT ONLY (AFS § Preconditions) — it is driven through the
    real UI exactly as the covering test drives it, and every observable this
    test asserts is read live off the product afterwards. Nothing is stubbed,
    injected or seeded through a different interface.

    Test-data substitution (declared): the case's own example tool
    `get_auth_user` takes no parameters and would render no input mapping at
    all, making the case unexecutable as literally written. Substituted with
    `ask_question` (2 required string params), the same tool the covering test
    uses. Test data only.
    """
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]
    mcp_toolkit_name = fixture["toolkit_name"]
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Setup (transit) — attach the MCP, add an MCP node and select its Toolkit"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # a bare /pipelines/all/{id} URL 404s; reload THIS one

        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        pipeline_page.add_node("MCP", timeout=UI_ELEMENT_TIMEOUT)
        mcp_node_id = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        # Move the node clear of ReactFlow's bottom-left Control Panel: a
        # fresh node spawns above it, and once the Input-mapping rows render
        # they extend down over the panel, whose "Fit View" button then
        # intercepts the pointer on the Type select's click (live-hit this
        # session — Playwright named `rf__controls` as the intercepting
        # subtree). Same `move_node()` remedy as
        # test_pipeline_interrupt_before_after_toggles.py:87.
        pipeline_page.move_node(mcp_node_id, dx=MCP_NODE_CLEARANCE_DX, dy=0)
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Steps 2-3 — Select the tool; the Input-mapping section appears"):
        pipeline_page.select_mcp_node_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question"
        # The live heading reads "Input mapping (required 2)" — sentence case
        # with a count; the case text's "INPUT MAPPING (REQUIRED)" is CSS
        # uppercasing (AFS § Case-text drift 2), so assert count-aware.
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 2)' should be shown for ask_question's 2 required parameters"
        )

    with allure.step(
        "Step 4 — Every parameter is listed with its mapping Type, defaulting to 'Fixed'"
    ):
        # "Type" here is the MAPPING type (Fixed / Variable / F-String), NOT
        # the parameter's JSON-schema data type — the UI never shows the
        # latter (AFS § Case-text drift 3).
        assert pipeline_page.is_mcp_node_input_mapping_value_visible("repoName")
        assert pipeline_page.is_mcp_node_input_mapping_value_visible("question")
        assert pipeline_page.get_mcp_node_input_mapping_type("repoName") == "Fixed"
        assert pipeline_page.get_mcp_node_input_mapping_type("question") == "Fixed"

    with allure.step("Step 7 — The Type select offers Fixed / Variable / F-String"):
        pipeline_page.open_mcp_node_input_mapping_type_select("repoName")
        option_testids = pipeline_page.get_open_listbox_option_testids()
        assert set(option_testids) == {
            "select-option-fixed",
            "select-option-variable",
            "select-option-fstring",
        }, f"Type select should offer exactly Fixed/Variable/F-String — got {option_testids}"

    with allure.step("Step 7 — Changing repoName's Type to 'Variable' affects that row only"):
        pipeline_page.select_open_listbox_option("variable")
        assert pipeline_page.get_mcp_node_input_mapping_type("repoName") == "Variable"
        # Per-ROW, not global: the two rows render identical `#simple-select-Type`
        # controls, so a regression applying the change to every row would still
        # satisfy the case's literal wording (AFS Axis 2).
        assert pipeline_page.get_mcp_node_input_mapping_type("question") == "Fixed"

    with allure.step(
        "Step 8 — The Variable branch swaps the Value widget and auto-binds the 'input' variable"
    ):
        # Both widget shapes now carry the same value testid
        # (EliteaAI/EliteaUI@5c24ed30), so the swap is proven by WHAT the
        # element yields: a text input has no text content, only an input
        # value — reading "input" as text content can only come from the
        # state-variable select the Variable branch renders.
        assert pipeline_page.get_mcp_node_input_mapping_variable_value("repoName") == "input", (
            "Switching repoName to Variable should swap its Value control to the state-variable "
            "select, auto-populated with 'input'"
        )
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

    with allure.step("Steps 9-10 — All three toggles are OFF by default"):
        # The case says "disabled by default"; live, all three are UNCHECKED,
        # and only two additionally carry `disabled` — for structural reasons
        # (entry point / transition == END), not "by default". Structured
        # output is not disabled at all (AFS § Case-text drift 4).
        assert not pipeline_page.is_node_interrupt_before_toggle_checked(mcp_node_id), (
            "'Interrupt before' should be OFF by default"
        )
        expect(pipeline_page.mcp_node_interrupt_after_toggle).not_to_be_checked()
        expect(pipeline_page.mcp_node_structured_output_toggle).not_to_be_checked()

    with allure.step("Step 11 — Save"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

    with allure.step(
        "Step 12 — Full page reload: per-row Types, both Values and all three toggle "
        "states come back unchanged"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question"
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_mcp_node_input_mapping_type("repoName") == "Variable", (
            "repoName's Type should persist as 'Variable' through a full reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_type("question") == "Fixed", (
            "question's Type should persist as 'Fixed' through a full reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_variable_value("repoName") == "input", (
            "repoName's Variable-branch value should persist as 'input' through a full reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE, (
            "question's Fixed value should persist through a full reload"
        )

        assert not pipeline_page.is_node_interrupt_before_toggle_checked(mcp_node_id)
        expect(pipeline_page.mcp_node_interrupt_after_toggle).not_to_be_checked()
        expect(pipeline_page.mcp_node_structured_output_toggle).not_to_be_checked()

        assert not console_errors, (
            f"Configuring, saving and reloading the MCP node's input mapping should not "
            f"introduce console errors: {console_errors}"
        )
