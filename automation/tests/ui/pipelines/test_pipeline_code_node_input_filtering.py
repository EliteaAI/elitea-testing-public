"""UI test — Code Node: Input Filtering (Selective State Access).

TMS: ELITEA-2449
(test-specs/pipelines/l3_code-node-input-filtering-selective-state-access_ELITEA-2449.md)

Executes a `STATE_A -> STATE_B -> STATE_C -> CODE1 -> END` pipeline with
THREE custom state variables (`var_a`/`var_b`/`var_c`, all str) plus a
`result` output variable. Three `state_modifier` nodes (NOT LLM nodes, so
all three values stay stable literals) give `var_a`/`var_b`/`var_c` the
fixed values `'AAA'`/`'BBB'`/`'CCC'` respectively, in that order, before the
Code node runs. The Code node's own `input:` DELIBERATELY lists only
`var_a`/`var_b` -- `var_c` is excluded even though STATE_C already set it
earlier in the SAME run. Verifies:
  - the Code node's Input combobox accepts a 2-variable selection while
    excluding the third existing state variable
  - at runtime, `elitea_state` inside the Code node's sandbox contains ONLY
    the variables listed in that node's own `input:` --
    `list(elitea_state.keys())` returns exactly `['var_a', 'var_b']`, and
    `'var_c' in elitea_state` is `False`, even though `var_c` has a real,
    non-empty value visible in its OWN Run Details row
  - the YAML editor's `nodes[]` array (read via server-truth API) shows the
    Code node's `input: [var_a, var_b]` with `var_c` absent

No case-text drift and no product defect found this session (AFS Known
Defects) -- this case is a clean confirmation of already-documented platform
behavior (`.claude/skills/elitea-pipeline/references/yaml-schema.md:238-241`):
a Code node only receives the state variables listed in its own `input:`.

Reused known-defect exclusions/routings (all already-filed, same root causes
as ELITEA-2446/2447 on this same Code-node family):
  - `EliteaAI/elitea-testing-public#1025`: the Pipeline YAML tab silently
    truncates long documents at default viewport size -- this pipeline's
    4-node YAML reproduces it too; step 5's verification reads
    `pipeline_api.get_pipeline()` server-truth instead of the YAML-tab DOM.
  - `EliteaAI/elitea-testing-public#1385`: a Code node's Run Details timeline
    label renders as `"pyodide"` (the Python-sandbox executor's name), NOT
    the space-stripped YAML id (`"Code1"`/`"CODE1"`).
  - `EliteaAI/elitea-testing-public#1267`: Run Details panel's Timeline
    Stepper prop-leak React warning -- same signature as every other
    Run-Details-opening test in this suite; excluded from the console-error
    assertion.

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

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

_CHAT_MESSAGE = "run"
_STATE_VARS = ("var_a", "var_b", "var_c")
_EXPECTED_RESULT_AFTER = '"Keys: [\'var_a\', \'var_b\'], has_var_c: False"'


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
    "ELITEA-2449_code-node-input-filtering-selective-state-access.md",
    "onetest-ai Test Case link",
)
def test_code_node_input_filtering_selective_state_access(
    page, pipeline_code_node_input_filtering, pipeline_api: PipelineAPI
):
    """A Code node's elitea_state only exposes vars listed in its own input:, excluding others set earlier."""
    pipeline_id = pipeline_code_node_input_filtering

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1 — Create pipeline with state variables var_a, var_b, var_c (String) — verify via server-truth API"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        server_pipeline = pipeline_api.get_pipeline(pipeline_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        parsed_server_yaml = yaml.safe_load(server_instructions)
        assert set(_STATE_VARS).issubset(parsed_server_yaml["state"].keys()), (
            f"Pipeline state should contain {_STATE_VARS}, got {list(parsed_server_yaml['state'].keys())!r}"
        )
        assert "result" in parsed_server_yaml["state"], (
            f"Pipeline state should also contain 'result', got {list(parsed_server_yaml['state'].keys())!r}"
        )

    with allure.step(
        "Step 2 — Nodes STATE_A -> STATE_B -> STATE_C -> CODE1 set all three variables before the "
        "Code node, connected by real edges in that exact chain (build-topology gotcha, "
        "EliteaAI/elitea-testing-public#1384, sidestepped via YAML/API build)"
    ):
        node_ids = [node["id"] for node in parsed_server_yaml["nodes"]]
        assert node_ids == ["STATE_A", "STATE_B", "STATE_C", "CODE1"], f"Unexpected node id order: {node_ids!r}"
        code_node_server_yaml = next(node for node in parsed_server_yaml["nodes"] if node["id"] == "CODE1")

        assert pipeline_page.edge_exists("STATE_A", "STATE_B"), "Canvas should show a real edge STATE_A -> STATE_B"
        assert pipeline_page.edge_exists("STATE_B", "STATE_C"), "Canvas should show a real edge STATE_B -> STATE_C"
        assert pipeline_page.edge_exists("STATE_C", "CODE1"), "Canvas should show a real edge STATE_C -> CODE1"
        for node_id in ("STATE_A", "STATE_B", "STATE_C"):
            assert not pipeline_page.edge_exists(node_id, "END"), (
                f"{node_id} should NOT have its own independent edge to END -- that would mean the "
                "topology fell into the disconnected-edge trap this fixture is built to avoid"
            )

    with allure.step(
        "Step 3 — Code node Input combobox includes ONLY var_a and var_b (excludes var_c) -- "
        "membership/substring check, since the two-chip display text is concatenated with no "
        "separator ('var_avar_b'), not 'var_a, var_b'. Verified READ-ONLY: this fixture's Code "
        "node already has input: [var_a, var_b] pre-set via YAML at creation (IMPLEMENTER "
        "AMENDMENT, see AFS Automation Hints -- re-invoking select_code_node_input_variable() on "
        "an ALREADY-selected chip toggles it OFF, confirmed live; the AFS's 'call it twice' note "
        "was confirmed on a probe pipeline whose Input started empty, not this fixture)"
    ):
        input_value = pipeline_page.get_code_node_input_value()
        assert "var_a" in input_value, f"Code node Input should include 'var_a', got {input_value!r}"
        assert "var_b" in input_value, f"Code node Input should include 'var_b', got {input_value!r}"
        assert "var_c" not in input_value, f"Code node Input should NOT include 'var_c', got {input_value!r}"
        assert pipeline_page.get_code_node_output_value() == "result", "Code node Output should show 'result'"

    with allure.step(
        "Step 4 — Code node script reads elitea_state.keys()/checks var_c membership and ends with "
        "a bare dict-literal expression"
    ):
        expected_code_value = code_node_server_yaml["code"]["value"]
        assert pipeline_page.get_code_node_value() == expected_code_value, (
            "Code node Value field should reflect the persisted script exactly"
        )
        assert "list(elitea_state.keys())" in expected_code_value, (
            f"Script should read elitea_state.keys(), got {expected_code_value!r}"
        )
        assert "'var_c' in elitea_state" in expected_code_value, (
            f"Script should check var_c membership in elitea_state, got {expected_code_value!r}"
        )
        last_statement = expected_code_value.rstrip().splitlines()[-1].strip()
        assert last_statement.startswith("{") and last_statement.endswith("}"), (
            f"Script's LAST statement should be a bare dict-literal expression, got {last_statement!r}"
        )

        expect(pipeline_page.code_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 5 — YAML shows Code node input: [var_a, var_b] (var_c not listed), read via "
        "pipeline_api server-truth (NOT the YAML tab -- viewport-truncation defect "
        "EliteaAI/elitea-testing-public#1025, same as ELITEA-2446/2447)"
    ):
        assert code_node_server_yaml["input"] == ["var_a", "var_b"], (
            f"YAML Code node input should be ['var_a', 'var_b'], got {code_node_server_yaml.get('input')!r}"
        )
        assert code_node_server_yaml["output"] == ["result"], (
            f"YAML Code node output should be ['result'], got {code_node_server_yaml.get('output')!r}"
        )

    with allure.step("Step 6 — Execute the pipeline via the embedded chat"):
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

        chat_text = page.inner_text("body")
        assert "has_var_c: False" in chat_text, (
            "AI-response bubble should independently confirm has_var_c: False in the chat text"
        )

    with allure.step(
        "Step 7 — Open Run Details, select the Code node timeline step (index 3 -- the FOURTH "
        "entry: STATE_A, STATE_B, STATE_C, then the Code node, which renders as 'pyodide', not "
        "'CODE1' -- EliteaAI/elitea-testing-public#1385)"
    ):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        pipeline_page.select_run_details_timeline_step(3, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        assert "pyodide" in timeline_text.lower(), (
            f"Timeline label should show the pyodide sandbox name after selecting step 3, got {timeline_text!r}"
        )
        for index in range(4):
            assert pipeline_page.get_run_details_timeline_step_status(index) == "completed", (
                f"Timeline step {index} should show status 'completed'"
            )

    with allure.step(
        "Step 8 — Verify result's After value confirms only var_a and var_b were accessible in "
        "elitea_state (exact match — all three source values are fixed state_modifier literals, "
        "not LLM-sourced, so this is fully deterministic)"
    ):
        pipeline_page.expand_run_details_state_row("result", timeout=UI_ELEMENT_TIMEOUT)
        result_after = pipeline_page.get_run_details_state_after_value("result")
        assert result_after == _EXPECTED_RESULT_AFTER, (
            f"'result' After value should be the exact deterministic string, got {result_after!r}"
        )

    with allure.step(
        "Step 9 — Verify var_c was NOT accessible (has_var_c = False) -- same read as step 8, the "
        "'has_var_c: False' substring IS the assertion, not a second independent check. var_c's OWN "
        "Run Details row still shows a real Before/After value (\"CCC\") -- that row's existence is "
        "orthogonal to whether the Code node itself could read var_c via elitea_state (Axis 2 note)"
    ):
        assert "has_var_c: False" in result_after, (
            f"'result' After value should contain 'has_var_c: False', got {result_after!r}"
        )

        pipeline_page.expand_run_details_state_row("var_c", timeout=UI_ELEMENT_TIMEOUT)
        var_c_before = pipeline_page.get_run_details_state_before_value("var_c")
        var_c_after = pipeline_page.get_run_details_state_after_value("var_c")
        assert var_c_before == '"CCC"', (
            f"'var_c' Before value should be the fixture's fixed literal, got {var_c_before!r}"
        )
        assert var_c_after == '"CCC"', (
            f"'var_c' After value should be unchanged by the Code node (which never read/wrote it), "
            f"got {var_c_after!r}"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during the full flow: {[m.text for m in console_errors]}"
        )
