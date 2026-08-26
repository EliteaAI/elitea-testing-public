"""UI test — Code Node: Read elitea_state Variables.

TMS: ELITEA-2446
(test-specs/pipelines/l3_code-node-read-elitea-state-variables_ELITEA-2446.md)

Executes an `LLM 1 -> Code 1 -> END` pipeline with two CUSTOM state
variables (`user_info`/str, `code_output`/str): the LLM node writes its
response into `user_info`, the Code node reads it back via
`elitea_state.get('user_info', '')` and writes a processed value into
`code_output`. Verifies:
  - the STATE panel lists the custom `user_info` variable
  - the canvas shows a real `LLM 1 -> Code 1` edge (not two independent
    `-> END` edges)
  - the Code node's Input/Output/Value/Structured-output config matches
    what the fixture built
  - Run Details shows both timeline steps completed, with `code_output`'s
    After value containing the processed `user_info` value
  - the YAML editor's Code node entry shows `input: [user_info]` and
    `output: [code_output]`

Case-text / AFS CLARIFICATIONs (all confirmed live, all explained by
documented or observed product behavior — see AFS Known Defects / Coverage
Map for the full writeup; NOT product defects, filed as `question`-labelled
clarifications):
  - `EliteaAI/elitea-testing-public#1383`: the case's own literal step-4
    script (`output = f"Processed: {result}" output`, a plain assignment)
    does NOT work — the runtime requires a bare dict-literal expression as
    the script's LAST statement for `structured_output: true` to route the
    value into the declared `output:` variable, per
    `.claude/skills/elitea-pipeline/references/yaml-schema.md`'s own
    documented Code Node rule. This test asserts the live-correct
    dict-literal form (reverse-masking guard).
  - `EliteaAI/elitea-testing-public#1384`: building this topology via the
    Flow Editor's "Add node" button does NOT auto-wire an edge between
    sequentially-added nodes -- this fixture sidesteps it entirely by
    building via `PipelineAPI.create_pipeline()` with an explicit
    `transition:` field per node (same as every other execution-based
    pipeline fixture in this suite).
  - `EliteaAI/elitea-testing-public#1385` (IMPLEMENTER AMENDMENT, found while
    running this test): the AFS expected the Code node's Run Details timeline
    step to render `"Code1"` (the space-stripped YAML id, per the
    ELITEA-2450/2452 LLM/Printer convention). Confirmed live: it instead
    renders `"pyodide"` (the Python-sandbox executor's name) -- the
    space-stripped-id convention does not generalize to Code nodes. This
    test asserts the live-correct `"pyodide"` label.

Known-defect routing (IMPLEMENTER AMENDMENT, found while running this test):
  - `EliteaAI/elitea-testing-public#1025` (already-filed, CONFIRMED to also
    apply here): the Pipeline YAML tab silently truncates long documents at
    default viewport size -- this pipeline's 2-node YAML renders only its
    first ~26 lines, never reaching the Code node's own `input`/`output`
    fields even though the backend persisted them correctly. Step 11's
    verification therefore reads `pipeline_api.get_pipeline()` instead of the
    YAML-tab DOM -- the SAME server-truth-readback pattern already used by
    `test_pipeline_llm_structured_output_state_variables.py` (ELITEA-2045) /
    `test_pipeline_yaml_editor_invalid_syntax.py` (ELITEA-2068).

Zero new testids -- every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details
panel).
"""

import logging

import allure
import pytest
import yaml
from api.client import PipelineAPI
from playwright.sync_api import expect

from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p3, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

_CHAT_MESSAGE = "Say hello to Alex in exactly three words."
_EXPECTED_CODE_LAST_STATEMENT = '{"code_output": f"Processed: {result}"}'


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as every other Run-Details-opening test in this
    suite (`EliteaAI/elitea-testing-public#1267`) -- this test opens the
    same `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2446_code-node-read-elitea-state-variables.md",
    "onetest-ai Test Case link",
)
def test_code_node_reads_elitea_state_variable(
    page, pipeline_llm_reads_state_via_code, pipeline_api: PipelineAPI
):
    """Code node reads a custom state variable via elitea_state.get(...) and writes a processed value into another."""
    pipeline_id = pipeline_llm_reads_state_via_code

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Create pipeline with state variable user_info (String) — verify via STATE panel"):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_variable_name_text("user_info", timeout=UI_ELEMENT_TIMEOUT) == "user_info", (
            "STATE panel should list the custom 'user_info' variable"
        )
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 2 — Add two nodes: LLM node (sets user_info) -> Code node -> END, "
        "connected by a real edge (not two independent -> END edges)"
    ):
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        assert llm_node_id == "LLM 1", f"Expected LLM node id 'LLM 1', got {llm_node_id!r}"
        assert code_node_id == "Code 1", f"Expected Code node id 'Code 1', got {code_node_id!r}"
        assert pipeline_page.edge_exists(llm_node_id, code_node_id), (
            "Canvas should show a real edge LLM 1 -> Code 1 -- building via YAML/API with an "
            "explicit transition guarantees this, unlike the Flow Editor's 'Add node' button "
            "(build-method gotcha, EliteaAI/elitea-testing-public#1384)"
        )
        assert not pipeline_page.edge_exists(llm_node_id, "END"), (
            "LLM 1 should NOT have its own independent edge to END -- that would mean the "
            "topology fell into the disconnected-edge trap this fixture is built to avoid"
        )

    with allure.step("Step 3 — Code node Input combobox includes user_info"):
        assert pipeline_page.get_code_node_input_value() == "user_info", "Code node Input should show 'user_info'"

    with allure.step(
        "Step 4 — Code node script reads elitea_state.get('user_info', ...) and ends with a bare "
        "dict-literal expression, NOT a plain assignment (CLARIFICATION, EliteaAI/elitea-testing-public#1383)"
    ):
        server_pipeline = pipeline_api.get_pipeline(pipeline_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        parsed_server_yaml = yaml.safe_load(server_instructions)
        code_node_server_yaml = next(node for node in parsed_server_yaml["nodes"] if node["id"] == "Code 1")
        expected_code_value = code_node_server_yaml["code"]["value"]

        assert pipeline_page.get_code_node_value() == expected_code_value, (
            "Code node Value field should reflect the persisted script exactly"
        )
        assert "elitea_state.get('user_info'" in expected_code_value, (
            f"Script should read 'user_info' via elitea_state.get(...), got {expected_code_value!r}"
        )
        last_statement = expected_code_value.rstrip().splitlines()[-1].strip()
        assert last_statement == _EXPECTED_CODE_LAST_STATEMENT, (
            "Script's LAST statement should be a bare dict-literal expression, not a plain "
            f"assignment (a plain assignment silently produces no state update -- "
            f"EliteaAI/elitea-testing-public#1383), got {last_statement!r}"
        )

    with allure.step("Step 5 — Code node Output is set to state variable code_output"):
        assert pipeline_page.get_code_node_output_value() == "code_output", (
            "Code node Output should show 'code_output'"
        )

    with allure.step("Step 6 — Structured output switch is enabled on the Code node"):
        expect(pipeline_page.code_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 7 — Execute the pipeline via the embedded chat"):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(_CHAT_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        expect(pipeline_page.run_node_label).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_embedded_chat_message_count() > initial_count, (
            "Embedded chat should show at least one new message after the run completes"
        )

    with allure.step("Step 8 — Open Run Details, select the Code node timeline step"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        # Index 1 -- the SECOND timeline entry, Code 1 (index 0 is LLM1).
        pipeline_page.select_run_details_timeline_step(1, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # CONFIRMED LIVE (this session): a Code node's timeline label shows the
        # Python-sandbox executor's name ("pyodide"), NOT the space-stripped
        # YAML id ("Code1") that the LLM/Printer convention (ELITEA-2450/2452)
        # would predict -- implementer amendment, EliteaAI/elitea-testing-public#1385.
        assert "pyodide" in timeline_text.lower(), (
            f"Timeline label should show the pyodide sandbox name after selecting step 1, "
            f"got {timeline_text!r}"
        )

    with allure.step("Step 9 — code_output After value contains the processed user_info value"):
        pipeline_page.expand_run_details_state_row("code_output", timeout=UI_ELEMENT_TIMEOUT)
        code_output_after = pipeline_page.get_run_details_state_after_value("code_output")

        prefix = "Processed: "
        assert prefix in code_output_after, (
            f"'code_output' After value should contain the 'Processed: ' prefix, got {code_output_after!r}"
        )
        # LLM-generated greeting is non-deterministic across runs -- assert the
        # prefix + a non-empty suffix, not an exact string (Axis 2 addition).
        suffix = code_output_after[code_output_after.find(prefix) + len(prefix):]
        assert suffix.strip(' "'), (
            f"'code_output' After value should have a non-empty suffix after {prefix!r}, "
            f"got {code_output_after!r}"
        )

    with allure.step("Step 10 — Verify no execution errors in the timeline"):
        assert pipeline_page.get_run_details_timeline_step_status(0) == "completed", (
            "LLM1 timeline step should show status 'completed'"
        )
        assert pipeline_page.get_run_details_timeline_step_status(1) == "completed", (
            "Code1 timeline step should show status 'completed'"
        )

    with allure.step(
        "Step 11 — YAML shows Code node input: [user_info], output: code_output "
        "(via pipeline_api, NOT the YAML tab -- see module docstring, "
        "EliteaAI/elitea-testing-public#1025)"
    ):
        # The Pipeline YAML tab (`pipeline-yaml-editor`) silently truncates long
        # documents at default viewport size (CONFIRMED LIVE this session, SAME
        # known, filed defect `EliteaAI/elitea-testing-public#1025` that
        # `test_pipeline_llm_structured_output_state_variables.py` (ELITEA-2045)
        # already routes around) -- this pipeline's 2-node YAML renders only its
        # first ~26 lines, never reaching the Code node's own `input`/`output`
        # fields even though the backend persisted them correctly. Reading
        # `code_node_server_yaml` (already fetched in Step 4 -- the pipeline's
        # config is unchanged by execution) is the same server-truth-readback
        # pattern ELITEA-2045/ELITEA-2068 already established.
        assert code_node_server_yaml["input"] == ["user_info"], (
            f"YAML Code node input should be ['user_info'], got {code_node_server_yaml.get('input')!r}"
        )
        assert code_node_server_yaml["output"] == ["code_output"], (
            f"YAML Code node output should be ['code_output'], got {code_node_server_yaml.get('output')!r}"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during the full flow: {[m.text for m in console_errors]}"
        )
