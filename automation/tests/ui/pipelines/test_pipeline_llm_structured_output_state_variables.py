"""UI test — Pipeline: LLM Node Structured Output Parses into State Variables.

TMS: ELITEA-2045
(test-specs/pipelines/l2_llm-node-structured-output-state-variables_ELITEA-2045.md)

Builds a pipeline entirely through the UI: adds an LLM node, adds 4 typed
custom STATE variables (`name`/String, `age`/Number, `hobbies`/List,
`metadata`/Json), selects all 4 in the LLM node's Output combobox, enables
Structured output, configures the SYSTEM prompt, saves, executes via the
embedded chat, and verifies:
  - the 4 typed state variables are correctly populated per their own type's
    JSON.stringify representation (mechanism already proven structurally
    identical by the merged `test_pipeline_run_details_multiple_state_variables.py`,
    ELITEA-2453 -- same node shape, different variable names)
  - the persisted pipeline YAML has `structured_output: true` and lists all
    4 variable names in `output`

Known-defect routing (see AFS Known Defects):
  - `EliteaAI/elitea-testing-public#1025` (CONFIRMED, already filed): the
    Pipeline YAML tab (`pipeline-yaml-editor`) silently truncates long
    documents at default viewport size -- this pipeline's 40-line YAML
    renders only its first 34 lines, never reaching `structured_output:
    true` or 3 of the 4 `output` entries, even though the backend persisted
    correctly (confirmed live via the save PUT's response body). Step 9's
    verification therefore reads `pipeline_api.get_pipeline()` instead of
    the YAML-tab DOM -- the same server-truth-readback pattern already used
    by `test_pipeline_yaml_editor_invalid_syntax.py` (ELITEA-2068).
  - `EliteaAI/elitea-testing-public#1274` does NOT apply here: this case's
    Output list never includes the built-in `messages` variable (only the
    4 custom ones), so the messages+structured-output defect is never
    triggered.

Locator/mechanic note: the LLM node's Output multi-select must be driven one
variable at a time via `select_llm_node_output_variable()` (its own
open->select->Escape->close cycle) -- batching multiple option clicks inside
a single held-open popover silently drops selections beyond the first one
or two (confirmed live this session, documented in the pipelines digest).

Zero new testids -- every handle this case touches already exists on
`automation/testids`, reused unmodified from ELITEA-2004/2042/2450/2452/2453.
"""

import json
import logging

import allure
import pytest
import yaml
from api.client import PipelineAPI
from config import settings
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

_STATE_VARIABLES = {
    "name": "str",
    "age": "number",
    "hobbies": "list",
    "metadata": "dict",
}
_SYSTEM_PROMPT = "Act as JSON Parser and parse user data into structured fields"
_TASK_TEMPLATE_VALUE = "{input}"
_CHAT_MESSAGE = (
    'My name is John, I am 30 years old, my hobbies are reading and hiking, '
    'and my metadata is {"source": "test"}.'
)


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as `test_pipeline_run_details_multiple_state_variables.py`
    (`EliteaAI/elitea-testing-public#1267`) -- this test opens the same
    `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2045_pipeline-structured-output-parse-llm-response-into-state-variables.md",
    "onetest-ai Test Case link",
)
def test_llm_structured_output_parses_into_state_variables(page, pipeline_id, pipeline_api: PipelineAPI):
    """LLM node with Structured output enabled parses a response into 4 typed state variables."""
    project_id = str(settings.elitea_project_id)

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    # This LLM node renders 8 stacked sections (Trigger/SYSTEM/TASK/CHAT HISTORY/
    # Input/Output/Toolkits/Interrupt+Structured-output) -- at the project's default
    # 1366x768 headless viewport, the node's Output row ends up positioned directly
    # under the canvas's own pinned bottom-left controls panel (zoom/fit-view/etc.),
    # even after fit_canvas_view(), intercepting clicks meant for the Output select
    # (same overlap class as fit_canvas_view()'s own ELITEA-2010 docstring, just not
    # fully cleared by re-fitting alone for a node this tall). A taller viewport gives
    # the node room to render without the overlap -- confirmed live this session.
    page.set_viewport_size({"width": 1366, "height": 1400})

    with allure.step("Step 1 — Create a pipeline with an LLM node"):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        pipeline_page.add_node("LLM")
        node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "LLM node should appear on the canvas with a non-empty data-id"

    with allure.step(
        "Step 2 — In the State panel, add 4 typed output variables: "
        "name (String), age (Number), hobbies (List), metadata (Json)"
    ):
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        for variable_name, type_key in _STATE_VARIABLES.items():
            pipeline_page.add_state_variable(variable_name, timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.select_state_variable_type(variable_name, type_key, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.get_state_variable_name_text(variable_name, timeout=UI_ELEMENT_TIMEOUT) == (
                variable_name
            ), f"STATE panel row {variable_name!r} should be present after adding it"
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 3 — In the LLM node, add all 4 created variables to the Output combobox "
        "(one variable per open/select/close cycle -- see module docstring)"
    ):
        # The LLM node grows tall enough (SYSTEM/TASK/CHAT HISTORY + Input/Output +
        # Toolkits + Interrupt/Structured-output) that its Output field can end up
        # positioned directly under the canvas's own pinned bottom-left controls
        # panel, intercepting the reopen click for later variables -- same class of
        # overlap already documented by fit_canvas_view()'s own docstring (ELITEA-2010).
        # Each added chip can shift the node's layout enough to reintroduce the
        # overlap, so re-fit before EVERY selection, not just once.
        for variable_name in _STATE_VARIABLES:
            pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.select_llm_node_output_variable(variable_name, timeout=UI_ELEMENT_TIMEOUT)
        output_value = pipeline_page.get_llm_node_output_value()
        for variable_name in _STATE_VARIABLES:
            assert variable_name in output_value, (
                f"LLM node Output should include {variable_name!r} after selection, got {output_value!r}"
            )
        assert "messages" not in output_value, (
            "Output should NOT include 'messages' -- combining it with dict/list-typed "
            "custom variables under structured_output would trip the confirmed "
            "EliteaAI/elitea-testing-public#1274 defect"
        )

    with allure.step('Step 4 — Enable the "Structured output" switch on the node'):
        pipeline_page.llm_node_structured_output_toggle.click(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        'Step 5 — Configure SYSTEM prompt: "Act as JSON Parser and parse user data into '
        'structured fields"'
    ):
        pipeline_page.fill_llm_node_section_value("system", _SYSTEM_PROMPT, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_value("system") == _SYSTEM_PROMPT, (
            "SYSTEM Value field should reflect the configured prompt"
        )
        # TASK must reference the chat input via F-String so the user's message actually
        # reaches the LLM node -- the case's own steps don't name this explicitly, but
        # without it there is no data for the LLM to parse (ELITEA-2453's fixture
        # establishes the same convention for this exact node shape).
        pipeline_page.select_llm_node_section_type("task", "F-String", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.fill_llm_node_section_value("task", _TASK_TEMPLATE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_value("task") == _TASK_TEMPLATE_VALUE, (
            "TASK Value field should reflect the F-String template referencing {input}"
        )

    with allure.step("Step 6 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step("Step 7 — Execute with input containing data matching the output schema"):
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

    with allure.step("Step 8 — Verify the response correctly parses values into each state variable"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )

        # Exactly one row (accordion's defaultExpanded={!index}, list index 0) is
        # auto-expanded on open -- but WHICH variable lands at index 0 depends on
        # the backend's own state-dict ordering, not this test's insertion order:
        # the persisted YAML's `state:` keys came back alphabetically sorted
        # (age/hobbies/input/messages/metadata/name), not in the name/age/hobbies/
        # metadata order they were added in (confirmed live this session -- unlike
        # ELITEA-2453's raw-API-authored fixture, where the insertion order WAS
        # preserved). Rather than assume which one is pre-expanded, check each
        # row's value box and only click to expand if it isn't already visible.
        for variable_name in _STATE_VARIABLES:
            after_locator = pipeline_page.get_run_details_state_value_locator(variable_name, "after")
            if after_locator.count() == 0 or not after_locator.is_visible():
                pipeline_page.expand_run_details_state_row(variable_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(after_locator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        name_after = pipeline_page.get_run_details_state_after_value("name")
        assert name_after.startswith('"') and name_after.endswith('"'), (
            f"'name' (str) After value should be JSON-string-quoted, got {name_after!r}"
        )
        assert name_after != '""', "'name' After value should be non-empty"

        age_after = pipeline_page.get_run_details_state_after_value("age")
        parsed_age = json.loads(age_after)
        assert isinstance(parsed_age, (int, float)), (
            f"'age' (number) After value should parse as a JSON number, got {age_after!r}"
        )
        assert not (age_after.startswith('"') and age_after.endswith('"')), (
            f"'age' After value should NOT be quoted like 'name', got {age_after!r}"
        )

        hobbies_after = pipeline_page.get_run_details_state_after_value("hobbies")
        parsed_hobbies = json.loads(hobbies_after)
        assert isinstance(parsed_hobbies, list), (
            f"'hobbies' (list) After value should parse as a JSON array, got {hobbies_after!r}"
        )
        assert len(parsed_hobbies) > 0, "'hobbies' After value should be a non-empty array"

        metadata_after = pipeline_page.get_run_details_state_after_value("metadata")
        parsed_metadata = json.loads(metadata_after)
        assert isinstance(parsed_metadata, dict), (
            f"'metadata' (Json) After value should parse as a JSON object, got {metadata_after!r}"
        )
        assert len(parsed_metadata) > 0, "'metadata' After value should be a non-empty object"

    with allure.step(
        "Step 9 — Verify in YAML: node has structured_output: true and output lists all "
        "variable names (via pipeline_api, NOT the YAML tab -- see module docstring, "
        "EliteaAI/elitea-testing-public#1025)"
    ):
        server_pipeline = pipeline_api.get_pipeline(pipeline_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        parsed_yaml = yaml.safe_load(server_instructions)
        llm_node = next(node for node in parsed_yaml["nodes"] if node["id"] == "LLM 1")
        assert llm_node.get("structured_output") is True, (
            f"Node YAML should have structured_output: true, got: {llm_node.get('structured_output')!r}"
        )
        assert set(llm_node.get("output", [])) == set(_STATE_VARIABLES), (
            f"Node YAML output should list all 4 variable names {set(_STATE_VARIABLES)!r}, "
            f"got {llm_node.get('output')!r}"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during the full flow: {[m.text for m in console_errors]}"
        )
