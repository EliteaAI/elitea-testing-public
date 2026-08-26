"""UI test — Code Node: Return Dict to Modify Multiple State Variables.

TMS: ELITEA-2447
(test-specs/pipelines/l3_code-node-return-dict-multiple-state-vars_ELITEA-2447.md)

Executes a `STATE1 (state_modifier) -> CODE1 (code) -> END` pipeline with
THREE custom state variables (`summary`/str, `count`/number, `tags`/list).
STATE1 seeds `summary` with a deterministic fixed template (NOT an LLM node,
so `count`'s expected value stays a stable literal). CODE1 reads `summary`
via `elitea_state.get('summary', '')` and, as its script's LAST statement,
returns a bare THREE-key dict literal updating `summary` (appended text),
`count` (word count), and `tags` (a fixed list) -- all from the SAME single
Code node execution. Verifies:
  - the pipeline's 3 custom state variables (summary/count/tags) all exist
  - the Code node's Input/Output/Value/Structured-output config matches
    what the fixture built
  - Run Details shows a single `pyodide`-labelled timeline step for CODE1,
    with all three variables' Before/After rows transitioning under it
  - no second Code-node timeline entry exists (atomic multi-var update)

No case-text drift and no product defect found this session (AFS Known
Defects) -- unlike its close sibling ELITEA-2446, this case's own literal
script text is exactly the confirmed-live-working form (bare dict-literal
as the final statement), first try.

Reused known-defect exclusion:
  - `EliteaAI/elitea-testing-public#1267`: Run Details panel's Timeline
    Stepper prop-leak React warning (`StepConnector2`/`Stepper2` in
    `RunStateDialog.jsx`) -- same signature as every other Run-Details
    -opening test in this suite; excluded from the console-error assertion.

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

_CHAT_MESSAGE = "go"
_STATE_VARS = ("summary", "count", "tags")


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
    "ELITEA-2447_code-node-return-dict-multiple-state-vars.md",
    "onetest-ai Test Case link",
)
def test_code_node_return_dict_multiple_state_vars(
    page, pipeline_code_node_multi_var_dict_return, pipeline_api: PipelineAPI
):
    """A Code node whose script's final statement is a 3-key dict literal writes all 3 state vars in one execution."""
    pipeline_id = pipeline_code_node_multi_var_dict_return

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1 — Create pipeline with state variables summary (String), count (Number), "
        "tags (List) — verify via STATE panel"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        for var_name in _STATE_VARS:
            assert pipeline_page.get_state_variable_name_text(var_name, timeout=UI_ELEMENT_TIMEOUT) == var_name, (
                f"STATE panel should list the custom {var_name!r} variable"
            )
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 2 — Code node Input combobox includes summary"):
        assert pipeline_page.get_code_node_input_value() == "summary", "Code node Input should show 'summary'"

    with allure.step(
        "Step 3 — Code node script reads elitea_state.get('summary', ...) and ends with a bare "
        "3-key dict-literal expression as its LAST statement"
    ):
        server_pipeline = pipeline_api.get_pipeline(pipeline_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        parsed_server_yaml = yaml.safe_load(server_instructions)
        code_node_server_yaml = next(node for node in parsed_server_yaml["nodes"] if node["id"] == "CODE1")
        expected_code_value = code_node_server_yaml["code"]["value"]

        assert pipeline_page.get_code_node_value() == expected_code_value, (
            "Code node Value field should reflect the persisted script exactly"
        )
        assert "elitea_state.get('summary'" in expected_code_value, (
            f"Script should read 'summary' via elitea_state.get(...), got {expected_code_value!r}"
        )
        last_statement = expected_code_value.rstrip().splitlines()[-1].strip()
        assert last_statement.startswith("{") and last_statement.endswith("}"), (
            f"Script's LAST statement should be a bare dict-literal expression, got {last_statement!r}"
        )
        for key in ("'summary'", "'count'", "'tags'"):
            assert key in last_statement, f"Dict-literal statement should update {key}, got {last_statement!r}"

    with allure.step(
        "Step 4 — Code node Output combobox maps returned keys to summary, count, tags "
        "(order-independent membership check — the combobox renders each selected "
        "variable as its own chip with NO textual separator between chips, confirmed "
        "live this session, so a comma-split can't be used; chip order is insertion "
        "order, not a stable contract) and structured output is enabled"
    ):
        output_value = pipeline_page.get_code_node_output_value()
        for var_name in _STATE_VARS:
            assert var_name in output_value, (
                f"Code node Output should include {var_name!r}, got {output_value!r}"
            )
        assert len(output_value) == sum(len(v) for v in _STATE_VARS), (
            f"Code node Output should contain exactly summary+count+tags and nothing else "
            f"(order-independent), got {output_value!r}"
        )
        expect(pipeline_page.code_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 5 — Execute the pipeline via the embedded chat"):
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

    with allure.step("Step 6 — Open Run Details, select the Code node timeline step"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        # Index 1 -- the SECOND timeline entry, CODE1 (index 0 is STATE1).
        pipeline_page.select_run_details_timeline_step(1, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # Code node timeline labels show the Python-sandbox executor's name
        # ("pyodide"), NOT the space-stripped YAML id -- same convention
        # ELITEA-2446 already confirmed (EliteaAI/elitea-testing-public#1385),
        # reconfirmed live this session on a DIFFERENT Code-node fixture.
        assert "pyodide" in timeline_text.lower(), (
            f"Timeline label should show the pyodide sandbox name after selecting step 1, "
            f"got {timeline_text!r}"
        )

    with allure.step(
        "Step 7 — Verify After state: summary updated with appended text, count updated with "
        "number, tags updated with list value"
    ):
        pipeline_page.expand_run_details_state_row("summary", timeout=UI_ELEMENT_TIMEOUT)
        summary_before = pipeline_page.get_run_details_state_before_value("summary")
        summary_after = pipeline_page.get_run_details_state_after_value("summary")
        # 'summary' is a str-typed var, rendered via JSON.stringify -- the
        # value box's text includes the literal wrapping quote characters
        # (same convention as 'tags' below), confirmed live this session.
        assert summary_before == '"Draft summary text"', (
            f"'summary' Before value should be the fixture's fixed template, got {summary_before!r}"
        )
        assert summary_after == '"Draft summary text [processed]"', (
            f"'summary' After value should be the concatenated form, got {summary_after!r}"
        )

        pipeline_page.expand_run_details_state_row("count", timeout=UI_ELEMENT_TIMEOUT)
        count_before = pipeline_page.get_run_details_state_before_value("count")
        count_after = pipeline_page.get_run_details_state_after_value("count")
        # 'count' is a fresh number-typed variable never set before this node
        # runs -- assert the Before box explicitly as an empty string, not
        # merely "row exists" (empty-text value boxes are omitted from the
        # a11y snapshot, which looks identical to "not found" at a glance —
        # Axis 2 addition, same caution ELITEA-2444 documented).
        assert count_before == "", f"'count' Before value should be empty (never set), got {count_before!r}"
        assert count_after == "3", (
            f"'count' After value should be the bare numeral 3 (word count of 'Draft summary text'), "
            f"got {count_after!r}"
        )

        pipeline_page.expand_run_details_state_row("tags", timeout=UI_ELEMENT_TIMEOUT)
        tags_before = pipeline_page.get_run_details_state_before_value("tags")
        tags_after = pipeline_page.get_run_details_state_after_value("tags")
        assert tags_before == "[]", f"'tags' Before value should be an empty list, got {tags_before!r}"
        assert tags_after == '["processed","automated"]', (
            f"'tags' After value should be the JSON-array literal, got {tags_after!r}"
        )

    with allure.step(
        "Step 8 — Confirm multiple state variables updated in a single Code node execution "
        "(exactly one pyodide timeline entry, not a second one per variable)"
    ):
        assert pipeline_page.get_run_details_timeline_step_count() == 2, (
            "Timeline should show exactly 2 steps (STATE1 + CODE1) — a second Code-node "
            "execution/timeline entry would mean the multi-var update was not atomic"
        )
        assert pipeline_page.get_run_details_timeline_step_status(0) == "completed", (
            "STATE1 timeline step should show status 'completed'"
        )
        assert pipeline_page.get_run_details_timeline_step_status(1) == "completed", (
            "CODE1 timeline step should show status 'completed'"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during the full flow: {[m.text for m in console_errors]}"
        )
