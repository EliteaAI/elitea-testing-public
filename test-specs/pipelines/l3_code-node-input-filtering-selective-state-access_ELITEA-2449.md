# Test Case: Code Node — Input Filtering (Selective State Access)

## Metadata
- **TMS ID**: ELITEA-2449
- **Linked Story**: none
- **Priority**: l3 (medium, as authored in the source TMS case — matches sibling
  ELITEA-2446/2447/2448's own priority mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- **Build via API/raw YAML, NOT the Flow Editor's "Add node" clicks** — same
  CONFIRMED LIVE GOTCHA already documented by ELITEA-2446/2447
  (`EliteaAI/elitea-testing-public#1384`: sequentially-added Flow-Editor nodes
  land as independent `-> END` edges, never actually chaining). This case needs
  THREE custom state variables (`var_a`/`var_b`/`var_c`, all str) plus a `result`
  output variable — `PipelineAPI.create_pipeline()` with a hand-built YAML
  `instructions` string is required, exactly as ELITEA-2446/2447/2453 already
  established.
- **Three `state_modifier` nodes (not LLM nodes) give `var_a`/`var_b`/`var_c` their
  deterministic values** — same reasoning ELITEA-2447 already established
  (`STATE1` node): a fixed Jinja template with no variables produces a stable
  literal, avoiding LLM-nondeterminism entirely. This session used the literals
  `'AAA'`/`'BBB'`/`'CCC'` for `var_a`/`var_b`/`var_c` respectively — content is
  irrelevant to the assertions, only their PRESENCE/ABSENCE in the Code node's
  `elitea_state` matters.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh pipeline built from raw YAML `instructions`, topology
  `STATE_A → STATE_B → STATE_C → CODE1 → END`:
  ```yaml
  entry_point: STATE_A
  state:
    var_a:
      type: str
    var_b:
      type: str
    var_c:
      type: str
    result:
      type: str
  nodes:
    - id: STATE_A
      type: state_modifier
      template: 'AAA'
      variables_to_clean: []
      input: []
      output: [var_a]
      transition: STATE_B
    - id: STATE_B
      type: state_modifier
      template: 'BBB'
      variables_to_clean: []
      input: []
      output: [var_b]
      transition: STATE_C
    - id: STATE_C
      type: state_modifier
      template: 'CCC'
      variables_to_clean: []
      input: []
      output: [var_c]
      transition: CODE1
    - id: CODE1
      type: code
      code:
        type: fixed
        value: |
          available_keys = list(elitea_state.keys())
          has_var_c = 'var_c' in elitea_state
          result = f"Keys: {available_keys}, has_var_c: {has_var_c}"
          {"result": result}
      input: [var_a, var_b]
      output: [result]
      structured_output: true
      transition: END
  ```
  **CRITICAL — same dict-literal-return requirement ELITEA-2446 already
  documented and filed** (`EliteaAI/elitea-testing-public#1383`): the Code
  node's script must end with a bare dict-literal expression, NOT a plain
  assignment, for `structured_output: true` to route the value into `output:`.
  This AFS's script already uses the confirmed-live-working shape.
- Chat message sent: any short text (this session used `"run"`) — content is
  irrelevant; only the pipeline's own Code-node logic produces the assertable
  value.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live exploration was on
  project "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with state variables `var_a`, `var_b`, `var_c` (all String) —
   via the raw-YAML `state:` block above (not the STATE panel's "+" control,
   since this test provisions all three plus `result` at creation time).
   - **Verify**: `pipeline_api.get_pipeline(pid)` → `yaml.safe_load(instructions)`
     → `parsed["state"]` contains `var_a`/`var_b`/`var_c`/`result`, OR the Flow
     Editor's STATE panel lists all four.
2. Add nodes that set all three variables before the Code node — three
   `state_modifier` nodes (`STATE_A`→`STATE_B`→`STATE_C`→`CODE1`→`END`), per the
   YAML above.
   - **Verify**: Flow Editor renders `STATE_A`, `STATE_B`, `STATE_C`, `CODE1`
     on canvas, connected by real edges in that exact chain (NOT independent
     `→ END` edges — see the CONFIRMED LIVE GOTCHA in Preconditions; building
     via YAML/API with explicit `transition:` per node guarantees this, exactly
     as ELITEA-2446/2447 already established for this suite).
3. In Code node, set Input combobox to include ONLY `var_a` and `var_b`
   (exclude `var_c`) — call `select_code_node_input_variable("var_a")` then
   `select_code_node_input_variable("var_b")` (existing `PipelineDetailPage`
   method, ELITEA-2009). **Confirmed live: calling this method twice in a row
   works correctly** — `_select_multi_select_option_and_close()` presses
   `Escape` and waits for the popover to fully close after each selection, so
   the SECOND call's `open_code_node_input_select()` reopens a genuinely-closed
   popover rather than toggling an already-open one shut. No gotcha here; the
   existing single-selection method composes cleanly for multi-selection.
   - **Verify**: `get_code_node_input_value()` — **IMPLEMENTER NOTE (confirmed
     live): for a TWO-variable selection this returns the chips' text
     CONCATENATED WITH NO SEPARATOR** — `"var_avar_b"`, not `"var_a, var_b"`
     or `"var_a,var_b"` (that comma-joined form is the HIDDEN input's value,
     not what `.text_content()` reads off the visible chip container). Assert
     `"var_a" in value and "var_b" in value and "var_c" not in value`, not an
     exact-string match. `get_code_node_output_value() == "result"` (single
     selection, unaffected by this concatenation quirk).
4. In Code node script, read `elitea_state.keys()` and check `var_c`
   membership — confirmed-live-working code (final statement is a bare dict
   literal, per the Preconditions CRITICAL note):
   ```python
   available_keys = list(elitea_state.keys())
   has_var_c = 'var_c' in elitea_state
   result = f"Keys: {available_keys}, has_var_c: {has_var_c}"
   {"result": result}
   ```
   - **Verify**: `get_code_node_value()` reflects the typed multi-line script
     exactly.
5. Open YAML editor — verify Code node shows `input: [var_a, var_b]` (`var_c`
   not listed).
   - **Verify**: `pipeline_api.get_pipeline()` → `yaml.safe_load()` → the
     `Code 1`/`CODE1` node's `input == ["var_a", "var_b"]` —
     **IMPLEMENTER AMENDMENT (confirmed live, same class as ELITEA-2446/2447):
     the Pipeline YAML tab's viewport-truncation defect
     (`EliteaAI/elitea-testing-public#1025`) reproduces on this pipeline's
     4-node YAML too** — the UI YAML tab renders only the first ~26 lines,
     never reaching the Code node's own `input`/`output` fields even though
     the backend persisted them correctly. Use the server-truth readback
     (`pipeline_api.get_pipeline()`), not `pipeline_page.get_yaml_content()`.
6. Execute the pipeline (send any chat message in the embedded chat).
   - **Verify**: run completes (`get_run_details_status() == "Completed"`); no
     console errors (excluding the known, filed `EliteaAI/elitea-testing-public#1267`
     Timeline Stepper prop-leak warning — reproduced live this session on
     opening the Run Details panel, identical signature to every other
     Run-Details-opening case in this suite).
7. Open Run Details, check Code node output.
   - **Verify**: `select_run_details_timeline_step(3, ...)` (index 3 — the
     FOURTH timeline entry: `STATE_A`, `STATE_B`, `STATE_C`, then the Code
     node's step, which — per ELITEA-2446's already-filed implementer
     amendment `EliteaAI/elitea-testing-public#1385` — renders as `"pyodide"`,
     not `"Code1"`/`"CODE1"`) then `expand_run_details_state_row("result")` →
     `get_run_details_state_after_value("result")`.
8. Verify output confirms only `var_a` and `var_b` were accessible in
   `elitea_state`.
   - **Verify**: `get_run_details_state_after_value("result")` — **confirmed
     live, exact deterministic string** (both `var_a`/`var_b` values are fixed
     literals, not LLM-nondeterministic, so an EXACT match is safe here unlike
     ELITEA-2446's LLM-sourced case):
     `'"Keys: [\'var_a\', \'var_b\'], has_var_c: False"'`. Also independently
     confirmed via the chat message's own AI-response bubble text (the
     Code node's structured-output result renders inline in the conversation:
     `"Keys: ['var_a', 'var_b'], has_var_c: False"`) — two independent
     observation points agree.
9. Verify `var_c` was NOT accessible (`has_var_c = False`).
   - **Verify**: same `get_run_details_state_after_value("result")` read as
     step 8 — the `has_var_c: False` substring IS the assertion; this case's
     Expected Final State and step 9 are the same observable as step 8, not a
     second independent check. (Analyst note: `var_c`'s OWN Run Details row
     still exists and shows `"CCC"` Before/After at the `pyodide` timeline step
     — confirmed live — because `var_c` WAS written earlier in THIS run by
     `STATE_C`; a variable having a row/value elsewhere in Run Details is
     unrelated to whether the CODE NODE ITSELF could read it, which is exactly
     what `result`'s `has_var_c: False` proves.)

## Expected Results
- The Code node's Input combobox accepts a 2-variable selection (`var_a`,
  `var_b`) while excluding a third existing state variable (`var_c`) that sits
  earlier in the SAME run's data flow.
- At runtime, `elitea_state` inside the Code node's sandbox contains ONLY the
  variables listed in that node's own `input:` — `list(elitea_state.keys())`
  returns exactly `['var_a', 'var_b']`, and `'var_c' in elitea_state` is
  `False`, even though `var_c` was set by an earlier node in the SAME pipeline
  run and has a real, non-empty value (`"CCC"`) that IS visible in `var_c`'s
  own Run Details row.
- The YAML editor's `nodes[]` array (read via server-truth API, not the
  UI tab) shows the Code node's `input: [var_a, var_b]` with `var_c` absent.
- No console errors (excluding the known `#1267` Stepper prop-leak) at any
  step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create pipeline with state vars var_a/var_b/var_c (String) | state vars exist | step 1 | step 1: `pipeline_api.get_pipeline()` / STATE panel | asserted |
| 2 Add nodes that set all three variables before Code node | 3 nodes, connected in chain | step 2 | step 2: canvas shows real `STATE_A→STATE_B→STATE_C→CODE1` edges | asserted — same build-method gotcha as ELITEA-2446/2447 (Flow-Editor "Add node" does NOT auto-wire; sidestepped via YAML/API build) |
| 3 Code node Input combobox — include ONLY var_a, var_b (exclude var_c) | Input shows var_a, var_b only | step 3 | step 3: `get_code_node_input_value()` substring checks | asserted — **IMPLEMENTER NOTE: multi-select display text has no separator between chips (`"var_avar_b"`), assert via substring/membership, not exact string** |
| 4 Code node script: available_keys/has_var_c/result | script accepted, matches confirmed-working form | step 4 | step 4: `get_code_node_value()` | asserted — the case's own literal script text (a chain of bare statements with no dict-literal-return line break shown) is reproduced here with the SAME confirmed-working dict-literal-return ending ELITEA-2446/2447 already established; no case-text drift found for THIS case (the script as given, once formatted with the required final dict-literal line, works exactly as written — unlike ELITEA-2446 where the case's own script text was a plain assignment) |
| 5 Open YAML editor — verify Code node shows input: [var_a, var_b] (var_c not listed) | YAML matches config | step 5 | step 5: `yaml.safe_load()` field assertion via `pipeline_api.get_pipeline()` | asserted — same already-filed `#1025` viewport-truncation defect as ELITEA-2446/2447 routes this through the server-truth API instead of the UI YAML tab |
| 6 Execute the pipeline | completes without error | step 6 | step 6: `get_run_details_status()` | asserted |
| 7 Open Run Details, check Code node output | Code node step selectable, output visible | step 7 | step 7: `select_run_details_timeline_step(3, ...)` + `expand_run_details_state_row("result")` | asserted — reuses ELITEA-2446/2452's existing timeline-step + state-row methods unmodified; expected label is `"pyodide"` (already-filed `#1385`), not `"Code1"` |
| 8 Verify output confirms only var_a and var_b were accessible | After value shows only var_a/var_b keys | step 8 | step 8: `get_run_details_state_after_value("result")` exact match (deterministic — fixed literals, not LLM-sourced) | asserted |
| 9 Verify var_c was NOT accessible (has_var_c = False) | has_var_c: False | step 9 | step 9: same read as step 8 — `has_var_c: False` substring | asserted — same observable as step 8, not a separate read |
| Expected Final State / Pass-Fail criteria | all steps complete, no errors, var_c not accessible | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 3's assertion is a membership/substring check (`"var_a" in value and
  "var_b" in value and "var_c" not in value`), not an exact-string match —
  *added: confirmed live that `get_code_node_input_value()`'s two-chip display
  text has no separator (`"var_avar_b"`), so an exact-string assertion written
  against an assumed `"var_a, var_b"` shape would fail even when the FEATURE
  behaves correctly — this is a locator/method quirk, not a product defect.*
- Step 8's assertion CAN be an exact-string match (unlike ELITEA-2446's
  LLM-sourced case) — *added: `var_a`/`var_b`/`var_c`'s values are all fixed
  Jinja literals (`state_modifier` nodes), not LLM completions, so
  `"Keys: ['var_a', 'var_b'], has_var_c: False"` is fully deterministic across
  runs.*
- Step 9 is explicitly the SAME read as step 8, not a second independent
  check — *added: the case's own step numbering (8 and 9) describes what looks
  like two verifications, but both read the identical `result` After value;
  documented here so the implementer doesn't write two separate but
  functionally-duplicate assertions, or worse, two DIFFERENT reads that could
  silently diverge.*
- `var_c`'s own Run Details row (Before=After=`"CCC"` at the `pyodide` step)
  is noted as a NON-assertion observation, not part of this case's pass
  criteria — *added: this session confirmed a variable's row-level
  Before/After visibility in Run Details is orthogonal to whether the
  executing NODE ITSELF could read it via `elitea_state` — the two are easy to
  conflate, and a future analyst/implementer should not mistake `var_c`'s
  visible row for evidence against this case's `has_var_c: False` claim.*
- Zero product defects found during this session's exploration — *added: this
  case is a clean confirmation of already-documented platform behavior
  (`.claude/skills/elitea-pipeline/references/yaml-schema.md:238-241`: "A code
  node only RECEIVES the state variables listed in its `input:`... you must
  explicitly list it to that node's `input:` list — this is a silent, common
  bug (the node 'ignores' the value)"). No case-text drift, no defect — the
  case describes exactly the documented, confirmed-live contract.*

## Cleanup
1. This session created two throwaway pipelines during live exploration
   (`autotest_2449_probe`, id `8823`; `autotest_2449_probe_uiselect`, id `8824`,
   both project 399 "Private") to confirm the Code node's input-filtering
   execution semantics and the multi-select UI flow, and **deleted both itself**
   via the API (`DELETE .../application/prompt_lib/399/{id} → 204 No Content`,
   confirmed for both). No residue left behind.
2. Implementer teardown: new fixture (see Automation Hints) built via
   `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)`
   in teardown — same pattern as `pipeline_with_typed_state_vars_id` /
   ELITEA-2446/2447's recommended fixtures.

## Concrete Handles (discovered during exploration)

**Zero new testids needed — every element this case touches already has one
from ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details
panel).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node Input/Output selects, Value field, Structured output toggle | `pipeline-code-node-input-select-combobox` / `pipeline-code-node-output-select-combobox` / `pipeline-code-node-value` / `pipeline-code-node-structured-output-toggle` | **on-`automation/testids` ✓** — added by ELITEA-2009, reused unmodified via `PipelineDetailPage.select_code_node_input_variable()` / `get_code_node_input_value()` / `fill_code_node_value()` / etc. Confirmed live this session (2 probe pipelines). | none needed |
| Individual dropdown option (state var name) | `[data-testid="select-option-{value}"]` | **on-main ✓** — confirmed via prior AFS (`SingleSelectMenuItem.jsx`); confirmed live this session — the popover correctly listed all 4 state vars (`result`, `var_a`, `var_b`, `var_c`) when the Code node's Input select was opened. | none needed |
| Run Details panel, timeline step selector (per index), state row/value boxes | `pipeline-run-details-panel`, `pipeline-run-details-timeline-step-{index}`, `pipeline-run-details-state-row-{variable}`, `pipeline-run-details-state-value-{before,after}-{variable}` | **on-`automation/testids` ✓** — added by ELITEA-2450/2451/2452, reused unmodified via `PipelineDetailPage.select_run_details_timeline_step()` / `expand_run_details_state_row()` / `get_run_details_state_after_value()`. Confirmed live: `result`'s row correctly renders and expands; `var_c`'s row independently confirmed too. | none needed |
| YAML view toggle + editor | `pipeline-yaml-view` / `pipeline-yaml-editor` | **on-main ✓** — added by ELITEA-2026, reused unmodified. Confirmed live this session the tab renders but truncates before the Code node's fields (already-filed `#1025`). | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation;
  **201 Created** confirmed live, twice (both probe pipelines).
- Pipeline execution and all Run Details data (timeline, per-step state)
  arrive entirely over Socket.IO, same as every other Run Details case in this
  suite (ELITEA-2446/2450/2451/2452/2453) — confirmed via
  `browser_network_requests` showing only `socket.io/?EIO=4…` exchanges around
  send/response, no dedicated REST endpoint for timeline/state.
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` —
  fires on pipeline deletion; **204 No Content** confirmed live twice (session
  cleanup, both probe pipelines).

## Known Defects Found During Exploration

**No product defect found — this case is a clean, confirmed pass.** The Code
node's input-filtering behavior works exactly as documented in
`.claude/skills/elitea-pipeline/references/yaml-schema.md:238-241` and exactly
as the case describes: `elitea_state` inside the sandbox contains ONLY the
variables listed in the node's own `input:`, and `var_c` (declared in the
pipeline's `state:`, written by an earlier node in the SAME run, but never
added to the Code node's `input:`) is completely absent from
`elitea_state.keys()` — `'var_c' in elitea_state` correctly evaluates `False`.

Two ALREADY-FILED defects from ELITEA-2446/2447 reproduce again on this case's
pipeline (not new findings, same root causes, listed for traceability only):
1. `EliteaAI/elitea-testing-public#1025` (viewport-truncation on the Pipeline
   YAML tab) — reproduced live on this pipeline's 4-node YAML; routed via
   `pipeline_api.get_pipeline()` server-truth readback (AFS step 5).
2. `EliteaAI/elitea-testing-public#1385` (Run Details timeline label for a
   Code node's step renders as `"pyodide"`, not the space-stripped YAML id)
   — reproduced live; AFS step 7 asserts the correct `"pyodide"` label.
3. `EliteaAI/elitea-testing-public#1267` (Timeline Stepper prop-leak console
   warning on opening Run Details) — reproduced live, identical signature;
   AFS step 6 excludes it from the console-error assertion.

## Blocked Steps

None. All 9 case steps (plus this AFS's own build-topology verification) were
exercised live this session via two disposable probe pipelines — no step
remains unexplained or unautomatable.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new
  testids needed (see Concrete Handles).
- **New fixture needed**: no existing fixture builds a 3-`state_modifier`-node
  chain feeding a Code node with a DELIBERATELY-NARROWED `input:` list.
  Recommend `pipeline_code_node_input_filtering_id` (or similar) in
  `automation/fixtures/data_fixtures.py`, built via `PipelineAPI.create_pipeline()`
  with the raw YAML `instructions` string in this AFS's § Test Data — mirrors
  ELITEA-2447's `state_modifier`-chain pattern (deterministic literals, no LLM
  nondeterminism) combined with ELITEA-2446's create/yield/delete fixture shape.
- **Multi-select Input flow, confirmed live and safe to use as-is**: call
  `select_code_node_input_variable("var_a")` then
  `select_code_node_input_variable("var_b")` — each call's internal
  `_select_multi_select_option_and_close()` presses `Escape` and waits for the
  popover to fully close before returning, so the two calls compose cleanly
  with no toggle-closed race. No new method needed.
- **`get_code_node_input_value()` multi-selection display quirk**: confirmed
  live returns `"var_avar_b"` (chips concatenated, no separator) for a
  2-variable selection. Assert via substring/membership checks
  (`"var_a" in value`, `"var_b" in value`, `"var_c" not in value`), not an
  exact-string match.
- **Code node script convention**: end with a bare dict-literal expression as
  the LAST statement when `structured_output: true` — same rule ELITEA-2446/
  2447 already established. This AFS's script already uses the confirmed-live
  form.
- **Reuse ELITEA-2446/2452's Run Details Before/After methods unmodified**:
  `open_run_details_panel()`, `select_run_details_timeline_step(index)`,
  `get_run_details_selected_timeline_step_id()`, `expand_run_details_state_row()`,
  `get_run_details_state_after_value()`, `get_run_details_timeline_step_status(index)`.
  For THIS pipeline's 4-node topology, the Code node's step is index 3 (0:
  `STATE_A`, 1: `STATE_B`, 2: `STATE_C`, 3: `pyodide`/Code1) — confirmed live.
- **Reuse ELITEA-2027/2042/2446's `yaml.safe_load()` + field-assertion
  pattern** unmodified for step 5 — `next(n for n in parsed["nodes"] if
  n["id"] == "CODE1")`, then assert `node["input"] == ["var_a", "var_b"]`.
- Wait strategy: `wait_for_embedded_chat_response()` after sending the chat
  message (never a fixed sleep), then
  `expect(pipeline_page.run_node_label).to_be_visible()` before opening Run
  Details — same as every other pipeline-execution case in this suite.
- `_surface.md` updated this session — see the new "Code node — input
  filtering (elitea_state scoping)" entry documenting the confirmed platform
  contract and the `get_code_node_input_value()` multi-select display quirk,
  so no future analyst/implementer rediscovers either by hand.
