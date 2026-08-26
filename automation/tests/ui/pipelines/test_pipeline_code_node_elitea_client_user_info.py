"""UI test — Code Node: elitea_client Access.

TMS: ELITEA-2448
(test-specs/pipelines/l3_code-node-elitea-client-user-info_ELITEA-2448.md)

Executes a `Code 1 (entry) -> END` pipeline with ONE custom JSON-typed state
variable (`user_info`). The Code node calls `elitea_client.get_user_data()`
and writes the returned dict into `user_info` via a bare NAME-reference
expression (`user_info`) as the script's LAST statement. Verifies:
  - the STATE panel lists the custom `user_info` variable
  - the canvas shows a single `code`-type node (`Code 1`)
  - the Code node's Value/Output/Structured-output config matches what the
    fixture built, including the script's literal text
  - Run Details shows the ONE timeline step (`Code 1`, labelled `"pyodide"`)
    completed, with `user_info`'s After value containing real account
    fields (`email`, `name`) confirming `elitea_client` resolves to the
    currently-authenticated test user

No case-text drift and no product defect found this session (AFS Known
Defects) -- this case's own literal script text (a bare name-reference last
statement, not an assignment) is confirmed live to work exactly as written,
unlike its close siblings ELITEA-2446/ELITEA-2447 which needed a dict-literal
CLARIFICATION.

Reused known-defect exclusion:
  - `EliteaAI/elitea-testing-public#1267`: Run Details panel's Timeline
    Stepper prop-leak React warning (`StepConnector2`/`Stepper2` in
    `RunStateDialog.jsx`) -- same signature as every other Run-Details
    -opening test in this suite; excluded from the console-error assertion.

Zero new testids -- every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details
panel).
"""

import json
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

_CHAT_MESSAGE = "hello"


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
    "ELITEA-2448_code-node-elitea-client-access.md",
    "onetest-ai Test Case link",
)
def test_code_node_elitea_client_user_info(page, pipeline_code_node_elitea_client_user_info, pipeline_api: PipelineAPI):
    """A Code node calling elitea_client.get_user_data() writes the authenticated user's data into a state variable."""
    pipeline_id = pipeline_code_node_elitea_client_user_info

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Create a pipeline with a Code node — verify it renders on the canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        assert code_node_id == "Code 1", f"Expected Code node id 'Code 1', got {code_node_id!r}"

        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_variable_name_text("user_info", timeout=UI_ELEMENT_TIMEOUT) == "user_info", (
            "STATE panel should list the custom 'user_info' variable"
        )
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 2 — Code node script uses elitea_client.get_user_data() then a bare "
        "'user_info' name reference as the final statement"
    ):
        server_pipeline = pipeline_api.get_pipeline(pipeline_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        parsed_server_yaml = yaml.safe_load(server_instructions)
        code_node_server_yaml = next(node for node in parsed_server_yaml["nodes"] if node["id"] == "Code 1")
        expected_code_value = code_node_server_yaml["code"]["value"]

        code_value = pipeline_page.get_code_node_value()
        assert code_value == expected_code_value, (
            f"Code node Value field should reflect the persisted script exactly, got {code_value!r}"
        )
        assert "elitea_client.get_user_data()" in expected_code_value, (
            f"Script should call elitea_client.get_user_data(), got {expected_code_value!r}"
        )
        last_statement = expected_code_value.rstrip().splitlines()[-1].strip()
        assert last_statement == "user_info", (
            f"Script's LAST statement should be a bare 'user_info' name reference "
            f"(not a dict literal or a plain assignment), got {last_statement!r}"
        )

    with allure.step("Step 3 — Code node Output is set to user_info with structured output enabled"):
        assert pipeline_page.get_code_node_output_value() == "user_info", (
            "Code node Output should show 'user_info'"
        )
        expect(pipeline_page.code_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — Execute the pipeline via the embedded chat"):
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

    with allure.step("Step 5 — Verify Code node executes without errors in Run Details"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        # Index 0 -- the ONLY timeline entry, this is a single-node pipeline.
        pipeline_page.select_run_details_timeline_step(0, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # Code node timeline labels show the Python-sandbox executor's name
        # ("pyodide"), NOT the space-stripped YAML id -- same convention
        # ELITEA-2446/ELITEA-2447 already established.
        assert "pyodide" in timeline_text.lower(), (
            f"Timeline label should show the pyodide sandbox name after selecting step 0, got {timeline_text!r}"
        )
        assert pipeline_page.get_run_details_timeline_step_status(0) == "completed", (
            "Code 1 timeline step should show status 'completed'"
        )

    with allure.step(
        "Step 6 — Verify Code node output state variable contains the user information "
        "(email + name present -- structure, not literal values, since the test-bot's "
        "own account fields could legitimately change)"
    ):
        pipeline_page.expand_run_details_state_row("user_info", timeout=UI_ELEMENT_TIMEOUT)
        user_info_after = pipeline_page.get_run_details_state_after_value("user_info")

        parsed = json.loads(user_info_after)
        assert isinstance(parsed, dict), f"'user_info' After value should parse as a JSON object, got {parsed!r}"
        assert parsed.get("email"), f"'user_info' should contain a non-empty 'email' key, got {parsed!r}"
        assert parsed.get("name"), f"'user_info' should contain a non-empty 'name' key, got {parsed!r}"

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during the full flow: {[m.text for m in console_errors]}"
        )
