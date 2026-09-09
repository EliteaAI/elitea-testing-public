"""UI test — Run Details: Multiple State Variables of Different Types.

TMS: ELITEA-2453
(test-specs/pipelines/l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md)

Executes a single-node LLM pipeline with `structured_output: true` that
writes 4 CUSTOM state variables of 4 distinct types (`custom_text`/str,
`custom_num`/number, `custom_list`/list, `custom_json`/dict), opens the Run
Details panel (`RunStateDialog.jsx`, reused from ELITEA-2450/2452), and
verifies:
  - all 4 custom-variable rows appear in the STATES section
  - each row is individually expandable, independent of the others
  - each row's After value renders per its OWN type's `JSON.stringify`
    representation (quoted string / bare number / bracketed array / braced
    object)

Case-text CLARIFICATION: the case's step 5 wording ("displayed uppercase")
describes a CSS `text-transform: uppercase` applied by `BasicAccordion.jsx`,
NOT the row's DOM text content, which is the raw lowercase variable name
(confirmed live via `getComputedStyle`). This test asserts presence via the
raw-lowercase testid/text and the CSS property, never the uppercase text.

Case steps 7 (INPUT string rendering) and 8 (MESSAGES list rendering) are
NOT re-verified here -- both are already covered by
`test_pipeline_run_details_state_before_after.py` (ELITEA-2452) via the SAME
`StateItemView` rendering path. Combining `messages` with `dict`/`list`-typed
custom variables in a `structured_output: true` node's `output` mapping is a
CONFIRMED product defect (`EliteaAI/elitea-testing-public#1274`); this test's
fixture deliberately excludes `messages` from `output` to route around it
(see `pipeline_with_typed_state_vars_id`). Step 8's "list representation" is
asserted by a real shape check (`isinstance(json.loads(after_value), list)`)
in that spec's Step 8 block, not merely by visibility/non-emptiness.

Zero new testids -- every handle this case touches (STATE panel, LLM node
Output-select/structured-output-toggle, Run Details panel/timeline/state-row/
value-box) already exists on `automation/testids`, reused unmodified from
ELITEA-2042/2450/2452.

REPAIRED 2026-09-10 (board card #2120, CI run 34331579791) -- three things a
reader of this file needs to know before changing it:

1. **Steps 9-12 assert the panel against THE RUN'S OWN PRODUCED STATE, not
   against any expected content.** The values in these variables are chosen by
   a live LLM and are nowhere in ELITEA-2453's contract, which only says
   "CUSTOM_TEXT: shows string values" / "CUSTOM_LIST: shows list/array
   representation" and so on. The pre-repair spec asserted `!= '""'`,
   `len(parsed_list) > 0` and `len(parsed_json) > 0` -- premises the case
   never had -- and went red in CI on a run whose backend state was genuinely
   empty while the panel rendered it faithfully. So each step now asserts
   parsed equality against the state the backend reported for THAT RUN
   (`json.loads(after) == backend_state[name]`) plus the case's own per-type
   rendering shape. This is the treatment `.agents/testing.md` § Fidelity
   policy prescribes for a nondeterministic producer: capture the real
   response and make it the oracle. It is strictly STRONGER than the content
   premise it replaces -- a panel showing a different run's values, a mangled
   value, or nothing at all now fails.

2. **The population retry exists because of `EliteaAI/elitea-testing-public#2153`.**
   An LLM node with `structured_output: true` silently writes NO state when
   the model answers in prose instead of JSON -- run status `Completed`, chat
   claims success, no console error, no `socket_validation_error` frame,
   defaults (`""` / absent / `[]` / `{}`) kept. Measured live on DEV: ~25%
   of runs (8 of 32). Case steps 2-3 require a run that POPULATED the
   variables, so that population is now an explicit precondition: bounded at
   `POPULATE_ATTEMPTS` = 3 re-sends, and if all three come back unpopulated
   the test **FAILS LOUDLY naming #2153 and printing the unpopulated state**.
   It never skips, never soft-asserts and never weakens an assertion -- if
   structured output breaks outright, this spec goes red, which is the point.

3. **The Socket.IO capture is OBSERVATION, not substitution.** Nothing is
   routed, fulfilled, intercepted, delayed, rewritten or fabricated: the
   frames are read passively off the live connection, the same class of
   evidence as reading a response body (`utils/websocket_frames.py`). Every
   asserted value is still produced end-to-end by the real system -- the LLM
   writes the state, the backend reports it, the UI renders it, and the test
   compares the two things the product itself produced.
"""

import json
import logging

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

#: Re-sends allowed before the run's structured output is declared broken.
#: Each attempt costs ~20-50 s on DEV (measured 19.5 / 35.8 / 48.3 / 50.0 s).
POPULATE_ATTEMPTS = 3

_CUSTOM_VARIABLES = ["custom_text", "custom_num", "custom_list", "custom_json"]


def _run_final_state(frames) -> dict:
    """State the backend reported on this run's own ``LLM1 -> END`` edge.

    Exactly the object the panel renders for the selected (last) timeline
    step: `parseRunsByEvent.helpers.js:263-278` assigns the transitional
    edge's `response_metadata.state` to the last timeline entry, and
    `StateItemView.jsx` renders
    ``JSON.stringify(timeline[selectedStep].state[name])``. Reading it here
    gives the test the product's OWN answer for what the panel should show.

    OBSERVATION, not substitution: nothing is routed, fulfilled, delayed or
    fabricated (`.agents/testing.md` § Fidelity policy).

    Args:
        frames: The attempt's slice of the live Socket.IO frame list.

    Returns:
        dict: The run's final state mapping (may be empty -- see #2153).
    """
    edges = [
        f for f in frames
        if f.get("type") == "agent_on_transitional_edge"
        and (f.get("response_metadata") or {}).get("next_step") == "END"
    ]
    assert edges, (
        "Run never reported an 'LLM1 -> END' transitional edge. "
        f"Saw {len(frames)} frame(s); distinct (event, type) pairs: "
        f"{sorted({(f.get('event'), f.get('type')) for f in frames})}"
    )
    return (edges[-1].get("response_metadata") or {}).get("state") or {}


def _is_populated(state: dict) -> bool:
    """True when the run wrote a usable value to all 4 typed custom variables.

    The case's steps 9-12 cannot observe four DISTINCT type renderings unless
    the run actually wrote all four. A False here is the
    `EliteaAI/elitea-testing-public#2153` no-op write, not a display fault.
    """
    return bool(
        isinstance(state.get("custom_text"), str) and state["custom_text"] != ""
        and isinstance(state.get("custom_num"), (int, float))
        and isinstance(state.get("custom_list"), list) and state["custom_list"]
        and isinstance(state.get("custom_json"), dict) and state["custom_json"]
    )


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as `test_pipeline_run_details_panel.py`'s
    `_is_known_1267_stepper_prop_leak` (`EliteaAI/elitea-testing-public#1267`)
    -- this test opens the same `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2453_run-details-multiple-state-variables-of-different-types.md",
    "onetest-ai Test Case link",
)
def test_run_details_multiple_state_variables_different_types(page, pipeline_with_typed_state_vars_id):
    """Run Details STATES section renders 4 typed custom variables, each independently expandable.

    Steps 9-12 compare each rendered value against the state THIS RUN's own
    backend reported on the wire, never against expected content -- the values
    are LLM-chosen and outside ELITEA-2453's contract (see the module
    docstring, point 1). The Socket.IO capture is passive observation, not
    substitution: nothing routed, fulfilled, delayed or fabricated (point 3).
    The population loop is the `EliteaAI/elitea-testing-public#2153`
    precondition guard -- bounded at 3 attempts, failing loudly and naming
    #2153 rather than skipping or softening anything (point 2).
    """
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    # `capture_websocket_frames()` must be entered BEFORE any navigation --
    # Playwright's "websocket" page event fires once, at connection-open
    # time, so a listener attached later never fires (page-object docstring,
    # confirmed live). Entered ONCE for the whole test; each attempt slices
    # its own window with `frames[before:]`.
    pipeline_page = PipelineDetailPage(page)

    with pipeline_page.capture_websocket_frames() as frames:
        with allure.step(
            "Step 1-3 — Execute the single-node structured-output pipeline "
            "(4 typed custom variables, no 'messages' in output -- see Known Defects)"
        ):
            for attempt in range(1, POPULATE_ATTEMPTS + 1):
                with allure.step(
                    f"Attempt {attempt}/{POPULATE_ATTEMPTS} — send, then read the run's "
                    "own final state off the wire (precondition: it populated all 4 variables)"
                ):
                    before = len(frames)
                    # A fresh page load resets the embedded chat to 0 messages,
                    # so `initial_count` stays valid on every attempt.
                    pipeline_page.navigate(pipeline_with_typed_state_vars_id)
                    pipeline_page.wait_for_canvas()
                    expect(pipeline_page.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                    initial_count = pipeline_page.get_embedded_chat_message_count()
                    pipeline_page.send_message_in_embedded_chat(
                        "Please populate the state variables now.", timeout=UI_ELEMENT_TIMEOUT
                    )
                    pipeline_page.wait_for_embedded_chat_response(
                        initial_count=initial_count,
                        stable_duration_ms=STABLE_DURATION_MS,
                        timeout=PIPELINE_EXECUTION_TIMEOUT,
                    )
                    expect(pipeline_page.run_node_label).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                    assert pipeline_page.get_embedded_chat_message_count() > initial_count, (
                        "Embedded chat should show at least one new message after the run completes"
                    )

                    backend_state = _run_final_state(frames[before:])
                    logger.info(
                        "Attempt %d/%d — run's own final state: %r",
                        attempt, POPULATE_ATTEMPTS, backend_state,
                    )
                    if _is_populated(backend_state):
                        break
            else:
                pytest.fail(
                    f"Structured output wrote no state in {POPULATE_ATTEMPTS} consecutive runs "
                    f"(last state: {backend_state!r}) -- the run reports 'Completed' and the "
                    "chat claims success while the state write silently no-ops. "
                    "Known defect: EliteaAI/elitea-testing-public#2153"
                )

    # The panel is opened exactly ONCE, after the loop: while the MUI Dialog is
    # open it overlays the canvas and intercepts pointer events, so a second
    # `pipeline-run-node-label` click retries to timeout (`_surface.md`).
    # `pipeline-run-node-label` always resolves to the NEWEST run
    # (`RunStateNodeGroup.jsx`), so after a retry the panel shows the retried
    # run -- the same run `backend_state` was read from.
    with allure.step("Step 4 — Open Run Details, node step is selected"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # Node id "LLM 1" renders WITHOUT the YAML id's space (confirmed live, ELITEA-2450);
        # the default-selected step on open is the LAST step (confirmed, ELITEA-2452).
        assert "LLM1" in timeline_text, (
            f"Timeline label should show 'LLM1' on open, got {timeline_text!r}"
        )

    with allure.step(
        "Step 5 — All 4 custom-variable rows appear in the STATES section "
        "(visible 'uppercase' is a CSS text-transform on the label; the row's own "
        "DOM text content is the raw lowercase variable name -- see module docstring)"
    ):
        for variable in _CUSTOM_VARIABLES:
            row = pipeline_page.get_run_details_state_row_locator(variable)
            expect(row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert (row.text_content() or "").strip() == variable, (
                f"Row testid text content should be the raw variable name {variable!r}"
            )

    with allure.step("Step 6, 13 — Expand each variable; each expands independently"):
        # custom_text (list index 0) is auto-expanded on open (accordion's
        # `defaultExpanded={!index}`) -- clicking it again would COLLAPSE it
        # (MUI accordion click toggles). Only the remaining 3 need a click.
        for variable in _CUSTOM_VARIABLES[1:]:
            pipeline_page.expand_run_details_state_row(variable, timeout=UI_ELEMENT_TIMEOUT)

        # All 4 remain visibly expanded simultaneously -- a non-exclusive
        # accordion, not a single-open one (confirmed live).
        for variable in _CUSTOM_VARIABLES:
            expect(
                pipeline_page.get_run_details_state_value_locator(variable, "after")
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    # Steps 9-12: each asserts (a) the panel rendered the value THIS RUN
    # produced, and (b) the case's own per-type rendering shape. PARSED values
    # are compared, never raw strings -- `JSON.stringify` emits no separator
    # spaces (`["a","b"]`) while Python's `json.dumps` does, and that coupling
    # is irrelevant to what the case verifies.
    with allure.step("Step 9 — CUSTOM_TEXT (str): After value renders as a JSON-quoted string"):
        custom_text_after = pipeline_page.get_run_details_state_after_value("custom_text")
        assert json.loads(custom_text_after) == backend_state["custom_text"], (
            f"Panel should render the value the run produced "
            f"({backend_state['custom_text']!r}), got {custom_text_after!r}"
        )
        assert custom_text_after.startswith('"') and custom_text_after.endswith('"'), (
            f"'custom_text' (str) After value should be JSON-string-quoted, got {custom_text_after!r}"
        )

    with allure.step("Step 10 — CUSTOM_NUM (number): After value renders as a bare JSON number"):
        custom_num_after = pipeline_page.get_run_details_state_after_value("custom_num")
        parsed_num = json.loads(custom_num_after)
        assert parsed_num == backend_state["custom_num"], (
            f"Panel should render the value the run produced "
            f"({backend_state['custom_num']!r}), got {custom_num_after!r}"
        )
        assert isinstance(parsed_num, (int, float)), (
            f"'custom_num' (number) After value should parse as a JSON number, got {custom_num_after!r}"
        )
        assert not (custom_num_after.startswith('"') and custom_num_after.endswith('"')), (
            f"'custom_num' After value should NOT be quoted like 'custom_text', got {custom_num_after!r}"
        )

    with allure.step("Step 11 — CUSTOM_LIST (list): After value renders as a bracketed JSON array"):
        custom_list_after = pipeline_page.get_run_details_state_after_value("custom_list")
        parsed_list = json.loads(custom_list_after)
        assert parsed_list == backend_state["custom_list"], (
            f"Panel should render the value the run produced "
            f"({backend_state['custom_list']!r}), got {custom_list_after!r}"
        )
        assert isinstance(parsed_list, list), (
            f"'custom_list' (list) After value should parse as a JSON array, got {custom_list_after!r}"
        )

    with allure.step("Step 12 — CUSTOM_JSON (dict): After value renders as a braced JSON object"):
        custom_json_after = pipeline_page.get_run_details_state_after_value("custom_json")
        parsed_json = json.loads(custom_json_after)
        assert parsed_json == backend_state["custom_json"], (
            f"Panel should render the value the run produced "
            f"({backend_state['custom_json']!r}), got {custom_json_after!r}"
        )
        assert isinstance(parsed_json, dict), (
            f"'custom_json' (Json) After value should parse as a JSON object, got {custom_json_after!r}"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during navigate->execute->open-panel->expand-rows: "
            f"{[m.text for m in console_errors]}"
        )
