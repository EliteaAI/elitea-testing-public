# Test Case: Code Node — Return Dict to Modify Multiple State Variables

## Metadata
- **TMS ID**: ELITEA-2447
- **Linked Story**: none
- **Priority**: l3 (medium, as authored in the source TMS case — per
  `spec-format.md`'s l1-critical/l2-high/l3-medium/l4-low mapping; matches
  sibling ELITEA-2446/ELITEA-2453's own AFS)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- **Build via API/raw YAML, NOT the Flow Editor's "Add node" clicks** (same
  CONFIRMED LIVE GOTCHA already documented by ELITEA-2446 —
  `EliteaAI/elitea-testing-public#1384`: sequentially-added Flow-Editor nodes
  land as two independent `-> END` edges, never actually chaining). This case
  needs THREE custom state variables (`summary`/str, `count`/number,
  `tags`/list) and a deterministic non-empty starting value for `summary` —
  `PipelineAPI.create_pipeline()` with a hand-built YAML `instructions` string
  is required, exactly as ELITEA-2446/ELITEA-2453 already established.
- **A `state_modifier` node (not an LLM node) gives `summary` its deterministic
  starting value.** The case's own Test Data table says "(none required)" —
  the analyst chose a fixed Jinja template (`state_modifier` node, no
  variables) over an LLM node specifically so `count = len(data.split())`'s
  expected value is a stable literal, not LLM-nondeterministic — confirmed
  live this works exactly like a plain string assignment (see Test Data
  below).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh pipeline built from raw YAML `instructions`, topology
  `STATE1 → CODE1 → END`:
  ```yaml
  entry_point: STATE1
  state:
    summary:
      type: str
    count:
      type: number
    tags:
      type: list
  nodes:
    - id: STATE1
      type: state_modifier
      template: 'Draft summary text'
      variables_to_clean: []
      input: []
      output: [summary]
      transition: CODE1
    - id: CODE1
      type: code
      code:
        type: fixed
        value: |
          data = elitea_state.get('summary', '')
          {'summary': data + ' [processed]', 'count': len(data.split()), 'tags': ['processed', 'automated']}
      input: [summary]
      output: [summary, count, tags]
      structured_output: true
      transition: END
  ```
  **Confirmed live**: the Code node's Output multi-select DOES allow
  re-selecting a variable that is also in its own `input` list (`summary`
  appears in both `input: [summary]` and `output: [summary, count, tags]`)
  — the combobox rendered all 3 chips (`summary`, `count`, `tags`) with no
  validation error, and Run Details correctly shows `summary` updated by
  the SAME node that also read it.
- Chat message sent: any short trigger message (this session used `"go"`) —
  content is irrelevant; the pipeline's entry point (`STATE1`) needs no chat
  input to run, the message only triggers pipeline execution via the Chat
  Message default trigger.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project was
  "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with state variables: `summary` (String), `count` (Number),
   `tags` (List) — via the raw-YAML `state:` block above.
   - **Verify**: `GET .../application/prompt_lib/{project}/{pipeline_id}` (or the
     Flow Editor's STATE panel) lists all three alongside built-in `input`/`messages`.
2. Add a Code node with Input including `summary`.
   - **Verify**: `get_code_node_input_value() == "summary"` (existing
     `PipelineDetailPage` method, ELITEA-2009). Confirmed live: the Code node's
     Input combobox shows exactly `summary`.
3. In Code node script, return a dict updating multiple state vars —
   `data = elitea_state.get('summary', '')` then, as the FINAL statement,
   `{'summary': data + ' [processed]', 'count': len(data.split()), 'tags':
   ['processed', 'automated']}`.
   - **Verify**: `get_code_node_value()` reflects the typed multi-line script
     exactly. **No case-text drift here** — unlike ELITEA-2446's own case text
     (a plain assignment that silently failed), THIS case's literal script text
     already ends with a bare dict-literal expression, matching
     `.claude/skills/elitea-pipeline/references/yaml-schema.md`'s documented
     Code Node rule. Confirmed live: works exactly as written, no fix needed.
4. Set Code node Output combobox to map returned keys to state variables and
   enable structured output — Output = `summary, count, tags`, Structured
   output = enabled.
   - **Verify**: `get_code_node_output_value()` contains all three variable
     names (order-independent set comparison — the combobox chip order is
     insertion order, not alphabetical); `.is_checked()` on
     `code_node_structured_output_toggle` is `True`.
5. Execute the pipeline (send any chat message in the embedded chat).
   - **Verify**: run completes (`get_run_details_status() == "Completed"`); no
     console errors (excluding the known, filed `EliteaAI/elitea-testing-public#1267`
     Stepper prop-leak warning — reproduced live this session, identical
     signature to every other Run-Details-opening case in this suite).
6. Open Run Details, click Code node step.
   - **Verify**: reuse `select_run_details_timeline_step(1, ...)` (index 1 —
     the SECOND timeline entry) and `get_run_details_selected_timeline_step_id()`
     returns text containing `"pyodide"` — same Code-node timeline-label
     convention ELITEA-2446 already confirmed and filed
     (`EliteaAI/elitea-testing-public#1385`: Code nodes show the Python-sandbox
     executor's name, not the space-stripped YAML id). **Confirmed live this
     session, on a DIFFERENT Code-node fixture** — reinforces that this is a
     general Code-node rendering convention, not a one-off. Also confirmed:
     clicking the run label (`pipeline-run-node-label`) opens the panel
     ALREADY on the last timeline step (`pyodide`/`CODE1`) — no explicit
     `select_run_details_timeline_step` call is strictly required to read
     `CODE1`'s own state, but the AFS still names the explicit call for
     robustness against a future multi-run timeline (same caution ELITEA-2453
     documented for its own 2-entries-for-1-node observation).
7. Verify After state shows: `summary` updated with appended text, `count`
   updated with number, `tags` updated with list value.
   - **Verify — confirmed live, exact match**:
     - `summary`: Before = `"Draft summary text"`, After =
       `"Draft summary text [processed]"` — string concatenation confirmed
       via `get_run_details_state_after_value("summary")`.
     - `count`: Before = `""` (empty — `count` is a fresh `number`-typed
       variable, never set before this node runs; confirmed via
       `browser_evaluate` DOM read, same empty-string-is-real-not-missing
       caution ELITEA-2444/2453 already documented), After = `"3"` — a bare,
       unquoted numeral (`JSON.stringify(3)`), matching the word count of
       `"Draft summary text"` exactly.
     - `tags`: Before = `"[]"`, After = `'["processed","automated"]'` — valid
       JSON array syntax, matching the list literal exactly.
   - All three variables update **from the SAME single Code node execution**
     (confirmed: only ONE `pyodide` timeline entry exists for this 2-node
     pipeline, and all three rows change under that one entry) — this is the
     case's own central claim ("Confirm multiple state variables updated in
     single Code node execution", step 8) and it holds.
8. Confirm multiple state variables updated in single Code node execution.
   - **Verify**: same evidence as step 7 — `summary`/`count`/`tags` all
     transition Before→After under the single `pyodide` timeline step; no
     second Code-node execution or timeline entry exists.

## Expected Results
- A Code node whose script's final statement is a bare dict literal with THREE
  keys correctly writes all three declared `output:` state variables
  (`summary`/str, `count`/number, `tags`/list) in ONE execution — confirmed
  live, exact match on all three types' `JSON.stringify` renderings (quoted
  string / bare numeral / bracketed array).
- Run Details shows the Code node's step labeled `"pyodide"` (not `"Code1"` —
  same convention ELITEA-2446 already confirmed), with all three variables'
  rows independently expandable and each showing a Before≠After transition.
- No console errors (excluding the known `#1267` Stepper prop-leak) at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create pipeline with state vars summary/count/tags (String/Number/List) | all 3 vars exist | step 1 | step 1: GET response / STATE panel | asserted |
| 2 Add Code node with Input including summary | Input shows summary | step 2 | step 2: `get_code_node_input_value()` | asserted |
| 3 Code node script: `data = elitea_state.get(...)` then multi-key dict literal | script accepted, works as written | step 3 | step 3: `get_code_node_value()` + step 7's live outcome | asserted — **no case-text drift**: unlike ELITEA-2446, this case's own literal script text already ends with a bare dict-literal expression and is confirmed live to work exactly as written, first try |
| 4 Set Output to map returned keys, enable structured output | Output=3 vars, toggle checked | step 4 | step 4: `get_code_node_output_value()` + `.is_checked()` | asserted |
| 5 Execute the pipeline | completes without error | step 5 | step 5: `get_run_details_status()` | asserted |
| 6 Open Run Details, click Code node step | Code node step selectable, `pyodide` label | step 6 | step 6: `select_run_details_timeline_step(1,...)` + label text | asserted — reuses ELITEA-2446's confirmed `pyodide`-label convention, reconfirmed live on a distinct fixture |
| 7 Verify After state: summary appended, count numeric, tags list | all 3 correct | step 7 | step 7: per-variable Before/After value assertions | asserted, exact-match |
| 8 Confirm multiple state vars updated in single Code node execution | atomic multi-var update | step 8 | step 8: single timeline entry, all 3 rows transition under it | asserted |
| Expected Final State / Pass-Fail criteria | all steps complete, no errors | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- **`count`'s Before value assertion is an explicit empty-string check, not a
  bare "row exists" check** — *added: this session's own live probe
  (`browser_evaluate` DOM read) confirmed the Before value box is a real,
  present, empty-string element, not a missing/absent one — asserting this
  explicitly prevents a future implementer from mistaking "empty" for
  "element not found" (same caution ELITEA-2444's digest entry already
  raised for a different variable).*
- **Output-combobox assertion is an order-independent set comparison**, not an
  exact string match — *added: the chip order in `summary,count,tags` is
  insertion order (the sequence the implementer/analyst clicked each option
  in the popper), not a guaranteed alphabetical or declaration order; pinning
  exact order would make the test brittle to an incidental implementation
  detail, not a real regression.*
  - **IMPLEMENTER AMENDMENT (found while running this test):** `get_code_node_output_value()`'s
    returned text has **no separator character at all** between the selected
    variables' names when 2+ are chipped (confirmed live: 3 selected vars
    rendered as the literal string `"summarycounttags"`, not `"summary, count,
    tags"` or `"summary,count,tags"`) — each variable renders as its own MUI
    chip with no comma/whitespace text node between siblings, so
    `.split(",")` silently produces a single-item set and fails the
    order-independent comparison it was meant to enable. The compliant
    order-independent check is therefore substring-membership + total-length
    equality (`all(v in output_value for v in vars)` AND
    `len(output_value) == sum(len(v) for v in vars)`), not a comma-split set
    comparison — the length check is what keeps it a real assertion (catches
    an extra/wrong variable) rather than a vacuous "contains" check. Same
    technique applies to `get_code_node_input_value()` if a future case ever
    selects 2+ Input variables.
- **The dedicated fixture uses a `state_modifier` node (not an LLM node) to
  seed `summary`'s starting value** — *added: this makes `count`'s expected
  value (`3`, from `len("Draft summary text".split())`) a stable literal
  instead of depending on LLM output length, which would make the test
  flaky for a reason that isn't a real regression (same class of caution as
  ELITEA-2446's `"Processed: "`-prefix-only assertion for LLM-sourced text).*
- **Step 5's console-error exclusion for the known `#1267` signature** — *added:
  every other Run-Details-opening case in this suite (ELITEA-2450/2451/2452/
  2453/2446) filters this exact signature; omitting the filter here would make
  this the only Run-Details case in the suite with a spuriously-red
  console-error assertion. Reconfirmed live this session (identical warning
  text/component stack).*

## Cleanup
1. This session created one throwaway pipeline during live exploration
   (`autotest_2447_probe`, id `8816`, project 399 "Private") via
   `PipelineAPI.create_pipeline()` to confirm the multi-key dict-return
   mechanic, and **deleted it itself** via `PipelineAPI.delete_pipeline(8816)`
   before ending the session — confirmed via a follow-up `GET
   .../application/prompt_lib/399/8816` returning no result in the
   subsequent probe (delete call raised no exception; matches the
   established `delete_pipeline()` 204-response pattern used by every
   sibling fixture's own teardown). No residue left behind.
2. Implementer teardown: new fixture (see Automation Hints) built via
   `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)`
   in teardown — same pattern as `pipeline_llm_reads_state_via_code`/
   `pipeline_with_typed_state_vars_id`.

## Concrete Handles (discovered during exploration)

**Zero new testids needed — every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details panel).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node Input/Output selects, Value field, Structured output toggle | `pipeline-code-node-input-select` / `pipeline-code-node-output-select` / `pipeline-code-node-value` / `pipeline-code-node-structured-output-toggle` | **on-`automation/testids` ✓** — added by ELITEA-2009, reused unmodified via `PipelineDetailPage.get_code_node_input_value()` / `get_code_node_output_value()` / `get_code_node_value()` / `.is_checked()` on `code_node_structured_output_toggle`. Confirmed live this session. | none needed |
| Run Details panel, timeline step selector (per index), state row/value boxes | `pipeline-run-details-panel`, `pipeline-run-details-timeline-step-{index}`, `pipeline-run-details-state-row-{variable}`, `pipeline-run-details-state-value-{before,after}-{variable}` | **on-`automation/testids` ✓** — added by ELITEA-2450/2451/2452, reused unmodified via `PipelineDetailPage.select_run_details_timeline_step()` / `expand_run_details_state_row()` / `get_run_details_state_before_value()` / `get_run_details_state_after_value()`. Confirmed live for all 3 custom variable names (`summary`/`count`/`tags`) — the dynamic testid template already handles arbitrary variable names, no new plumbing. | none needed |
| Run node clickable label (opens panel) | `pipeline-run-node-label` | **on-`automation/testids` ✓** — reused unmodified from ELITEA-2450, `open_run_details_panel()`. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation.
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on
  Save (implementer-side, if the test also exercises a UI Save round-trip;
  the API-built fixture itself uses `POST`, no `PUT` needed).
- Pipeline execution and all Run Details data (timeline, per-step state) arrive
  entirely over Socket.IO, same as every other Run Details case in this suite
  (ELITEA-2446/2450/2451/2452/2453) — confirmed via `browser_network_requests`
  this session: only a `GET .../application/prompt_lib/399/8816` (page-load
  fetch of the pipeline's own config) fired outside Socket.IO around
  execute→open-panel→expand-rows.
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires
  on pipeline deletion (session cleanup).

## Known Defects Found During Exploration

**No product defect found, and no case-text drift found.** This case's own
literal script text is exactly the confirmed-live-working form (bare
dict-literal as the final statement) — unlike its close sibling ELITEA-2446,
whose case text described a plain-assignment form that silently failed. All
8 case steps executed and matched their expected results exactly, first try.

One re-confirmation of an already-filed, non-blocking observation:
- Console shows the known, already-filed `EliteaAI/elitea-testing-public#1267`
  Timeline Stepper prop-leak React warning (`Warning: Received \`%s\` for a
  non-boolean attribute...`, `StepConnector2`/`Stepper2` in
  `RunStateDialog.jsx`) — same signature reproduced live this session on this
  case's own fixture, consistent with every other Run-Details-opening case in
  this suite. Not re-filed (already tracked); scope the console-error
  assertion to exclude it, per established convention.

## Blocked Steps

None. All 8 case steps were exercised live this session against a real
pipeline (id 8816, deleted at session end) — no defect, no case-text drift,
no blocker.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new
  testids needed (see Concrete Handles).
- **New fixture needed**: no existing fixture builds a `STATE1 (state_modifier)
  → CODE1 (code, multi-key dict return) → END` topology. Recommend
  `pipeline_code_node_multi_var_dict_return` (or similar) in
  `automation/fixtures/data_fixtures.py`, built via
  `PipelineAPI.create_pipeline()` with the raw YAML `instructions` string in
  this AFS's § Test Data — mirrors `pipeline_llm_reads_state_via_code`'s
  create/yield/delete pattern (NOT `create_pipeline_with_nodes()`, which has
  no `state:` support, confirmed again this session).
- **Reuse ELITEA-2446's confirmed gotchas verbatim** — build via YAML/API
  (never Flow-Editor "Add node" clicks) for any multi-node pipeline that must
  actually EXECUTE; Code node script must end with a bare dict-literal
  expression as its LAST statement for `structured_output: true` to route
  values into `output:`; Run Details timeline label for a Code node step is
  `"pyodide"`, not the space-stripped YAML id.
- **New observation this session, not previously documented**: a Code node's
  Output multi-select accepts a variable that is ALSO in that same node's own
  `input` list (`summary` in both here) — no validation error, no rendering
  issue, Run Details correctly attributes the update to the single node that
  both read and wrote it. Useful precedent for any future case needing a node
  to both read and overwrite the same variable.
- **Assert `count`'s Before value as an explicit empty string**, not merely
  "row exists" — see Coverage Map Axis 2. Use `browser_evaluate`/a real
  Playwright text assertion on the value box's `textContent`, not
  presence-in-accessibility-snapshot alone (same caution ELITEA-2444
  documented — empty-text value boxes are omitted from the a11y snapshot,
  which looks identical to "not found" at a glance).
- **Assert Output-combobox contents as a set, not an ordered string** — chip
  insertion order is not a stable contract.
- Reuse `PipelineDetailPage.open_run_details_panel()`,
  `select_run_details_timeline_step(index)`,
  `get_run_details_selected_timeline_step_id()`, `expand_run_details_state_row()`,
  `get_run_details_state_before_value()`, `get_run_details_state_after_value()`,
  `get_code_node_input_value()`, `get_code_node_output_value()`,
  `get_code_node_value()` unmodified — all confirmed working against this
  case's fixture this session. No new page-object methods needed, only a new
  fixture.
- Wait strategy: `wait_for_embedded_chat_response()` after sending the chat
  message (never a fixed sleep), then `expect(pipeline_page.run_node_label).to_be_visible()`
  before opening Run Details — same as every other pipeline-execution case in
  this suite.
- `_surface.md` updated this session — see the "Code node — multi-key dict
  return updates several state vars in one execution" section, documenting
  the input/output self-overlap observation and reconfirming the `pyodide`
  timeline-label convention on a second, independent fixture.
