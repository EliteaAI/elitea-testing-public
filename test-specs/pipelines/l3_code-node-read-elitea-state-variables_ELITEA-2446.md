# Test Case: Code Node — Read elitea_state Variables

## Metadata
- **TMS ID**: ELITEA-2446
- **Linked Story**: none
- **Priority**: l3 (medium, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- **Build via API/raw YAML, NOT the Flow Editor's "Add node" clicks** (see Automation
  Hints — CONFIRMED LIVE GOTCHA). `PipelineAPI.create_pipeline()` with a hand-built
  YAML `instructions` string (same pattern as `_TYPED_STATE_VARS_INSTRUCTIONS` /
  `_CUSTOM_STATE_VAR_INSTRUCTIONS` in `automation/fixtures/data_fixtures.py`) is
  required because `create_pipeline_with_nodes()` has **no `state:` support**
  (confirmed by that helper's own docstring) and this case needs two CUSTOM state
  variables (`user_info`, `code_output`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh pipeline built from raw YAML `instructions` (new fixture recommended —
  see Automation Hints), topology `LLM 1 → Code 1 → END`:
  ```yaml
  entry_point: LLM 1
  state:
    user_info:
      type: str
    code_output:
      type: str
  nodes:
    - id: LLM 1
      type: llm
      input: []
      input_mapping:
        chat_history: {type: fixed, value: []}
        system: {type: fixed, value: "You are a helpful assistant."}
        task: {type: fixed, value: "Say hello to Alex in exactly three words."}
      output: [user_info]
      structured_output: false
      transition: Code 1
    - id: Code 1
      type: code
      code:
        type: fixed
        value: |
          result = elitea_state.get('user_info', '')
          {"code_output": f"Processed: {result}"}
      input: [user_info]
      output: [code_output]
      structured_output: true
      transition: END
  ```
  **CRITICAL — the Code node's script must end with a bare dict-literal
  expression, NOT an assignment** (see Coverage Map / Known Defects CLARIFICATION
  below). `code_output = f"..."` (a plain assignment) silently produces NO state
  update; `{"code_output": f"..."}` (dict literal as the final statement) is the
  confirmed-live-working form, matching `.claude/skills/elitea-pipeline/references/
  yaml-schema.md`'s own documented Code Node rule ("Return a dict literal as the
  LAST expression... Do NOT use a top-level `return`").
- Chat message sent: any short prompt (this session used `"Alex"`/`"Bob"`/`"Carla"`/
  `"Dana"` across 4 probe runs) — content is irrelevant to the assertions beyond
  producing a non-empty `user_info` value for Code 1 to process.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live-exploration browser was
  on project "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with state variable `user_info` (String) — via the raw-YAML
   `state:` block above (not the STATE panel's "+" control, since this test
   provisions BOTH `user_info` and `code_output` at creation time).
   - **Verify**: `GET .../application/prompt_lib/{project}/{pipeline_id}` (or the
     Flow Editor's STATE panel) lists `user_info` alongside built-in `input`/`messages`.
2. Add two nodes: LLM node (sets `user_info`) → Code node → END, per the YAML above.
   - **Verify**: Flow Editor renders `LLM 1` and `Code 1` on canvas, connected by a
     real edge `LLM 1 → Code 1` (NOT two independent `→ END` edges — see the
     CONFIRMED LIVE GOTCHA in Automation Hints; this is exactly what building via
     YAML/API guarantees and what the Flow Editor's "Add node" button does NOT).
3. In Code node, set Input combobox to include `user_info`.
   - **Verify**: `get_code_node_input_value() == "user_info"` (existing
     `PipelineDetailPage` method, ELITEA-2009).
4. In Code node script, read from elitea_state and write the processed value —
   confirmed-live-working code: `result = elitea_state.get('user_info', '')` then a
   bare `{"code_output": f"Processed: {result}"}` as the FINAL statement.
   - **Verify**: `get_code_node_value()` reflects the typed multi-line script exactly.
   - **CLARIFICATION on the case's own literal step-4 text** — see Coverage Map.
5. Set Code node Output to a state variable (`code_output`).
   - **Verify**: `get_code_node_output_value() == "code_output"`.
6. Enable the structured output switch on the Code node.
   - **Verify**: `is_checked()` is `True` — required for the dict-literal return to
     route into the declared `output:` variable (per the Code Node rules doc).
7. Execute the pipeline (send any chat message in the embedded chat).
   - **Verify**: run completes (`get_run_details_status() == "Completed"`); no
     console errors.
8. Open Run Details, click on the Code node step.
   - **Verify**: reuse `select_run_details_timeline_step(1, ...)` (index 1 — the
     SECOND timeline entry, `Code 1`, confirmed live once the transition is wired
     correctly) and `get_run_details_selected_timeline_step_id()` returns text
     containing `"pyodide"` — **IMPLEMENTER AMENDMENT (confirmed live during
     ELITEA-2446 implementation):** the space-stripped-YAML-id convention
     (`"LLM1"`/`"LLM2"`, confirmed ELITEA-2450/2452) does NOT generalize to Code
     nodes — the timeline label instead shows the underlying Python-sandbox
     executor's name (`pyodide`), not `"Code1"`. Filed:
     [EliteaAI/elitea-testing-public#1385](https://github.com/EliteaAI/elitea-testing-public/issues/1385).
     The mechanism itself (selecting index 1, reading that step's state) is
     unaffected — only the expected label text.
9. Verify `code_output` After value contains the processed `user_info` value.
   - **Verify**: `expand_run_details_state_row("code_output", ...)` then
     `get_run_details_state_after_value("code_output")` contains the substring
     `"Processed: "` followed by the chat message's LLM-generated greeting text
     (the exact greeting varies by model response — assert the `"Processed: "`
     prefix + non-empty suffix, not an exact string).
10. Verify no execution errors in timeline.
    - **Verify**: `get_run_details_timeline_step_status(0) == "completed"` AND
      `get_run_details_timeline_step_status(1) == "completed"`; zero console errors
      EXCLUDING the known, filed `EliteaAI/elitea-testing-public#1267` Timeline
      Stepper prop-leak warning (same signature reproduced live this session,
      identical to every other Run-Details-opening case in this suite).
11. Open YAML editor — verify Code node shows `input: [user_info]` and
    `output: code_output`.
    - **Verify**: `yaml.safe_load(pipeline_page.get_yaml_content())`, find the
      `Code 1` entry in `parsed["nodes"]`, assert `node["input"] == ["user_info"]`
      and `node["output"] == ["code_output"]` — same `yaml.safe_load()` +
      field-assertion technique ELITEA-2027/2042 already established for this
      suite (no new pattern to invent). **IMPLEMENTER AMENDMENT (confirmed live
      during ELITEA-2446 implementation): this pipeline's 2-node YAML (multi-line
      Code script + 2 custom state vars) is long enough to hit the ALREADY-FILED
      `EliteaAI/elitea-testing-public#1025` viewport-truncation defect** (the
      Pipeline YAML tab silently clips long documents — same defect
      ELITEA-2045 already routes around) — the UI YAML tab never renders the
      Code node's `input`/`output` fields. Verify via
      `pipeline_api.get_pipeline()` → `yaml.safe_load(instructions)` instead
      (the SAME server-truth-readback pattern ELITEA-2045/ELITEA-2068
      established), not `pipeline_page.get_yaml_content()`.

## Expected Results
- The Code node correctly reads `user_info` via `elitea_state.get(...)` and writes a
  processed value into `code_output`, PROVIDED the script's final statement is a
  bare dict literal (not a plain assignment) and `structured_output` is enabled.
- Run Details shows TWO timeline steps for this 2-node pipeline (`LLM1`, `Code1`),
  each independently selectable, with `code_output`'s Before/After values differing
  at the `Code1` step (Before=`""`, After=the processed string).
- The YAML editor's `nodes[]` array shows the Code node's `input`/`output` fields
  exactly as configured, verifiable via `yaml.safe_load()`.
- No console errors (excluding the known `#1267` Stepper prop-leak) at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create pipeline with state variable `user_info` (String) | state var exists | step 1 | step 1: STATE panel / GET response lists `user_info` | asserted |
| 2 Add LLM node (sets `user_info`) → Code node → END | 3 nodes, connected | step 2 | step 2: canvas shows real `LLM 1 → Code 1` edge | asserted — **CLARIFICATION: building this topology via the Flow Editor's "Add node" button does NOT auto-wire an edge between sequentially-added nodes (confirmed live, 4 probe runs) — see Known Defects/Automation Hints. This is a build-method gotcha, not a product execution defect: the SAME topology built via YAML/API (as every other execution fixture in this suite already does) wires and executes correctly.** |
| 3 Set Code node Input to `user_info` | Input shows `user_info` | step 3 | step 3: `get_code_node_input_value()` | asserted |
| 4 Code node script reads `elitea_state.get('user_info', '')`, builds `output = f"Processed: {result}"` | script accepted | step 4 | step 4: `get_code_node_value()` | asserted — **CLARIFICATION: the case's own literal script text (`... output = f"Processed: {result}" output`) is a plain ASSIGNMENT to a local variable named `output`. Confirmed live (3 probe runs, `EliteaAI/EliteaUI` @ `automation/testids`) this form produces NO state update — `code_output` stays `""`/`""` Before/After. The confirmed-live-WORKING form ends with a bare dict-literal expression (`{"code_output": f"Processed: {result}"}`), per `.claude/skills/elitea-pipeline/references/yaml-schema.md`'s own documented rule ("dict literal as the LAST expression... do NOT use a top-level `return`"). Not a product defect — the runtime behaves exactly as that reference doc specifies; the CASE TEXT is what's stale/ambiguous. Reverse-masking guard applies: assert the live-correct form, file the case-text drift as a CLARIFICATION.** |
| 5 Set Code node Output to `code_output` | Output shows `code_output` | step 5 | step 5: `get_code_node_output_value()` | asserted |
| 6 Enable structured output | switch checked | step 6 | step 6: `.is_checked()` | asserted |
| 7 Execute the pipeline | completes without error | step 7 | step 7: `get_run_details_status()` | asserted |
| 8 Open Run Details, click Code node step | Code node step selectable | step 8 | step 8: `select_run_details_timeline_step(1, ...)` + label text | asserted — reuses ELITEA-2452's existing timeline-step METHOD unmodified, but the expected label text is `"pyodide"` not `"Code1"` (implementer amendment, `EliteaAI/elitea-testing-public#1385`) |
| 9 Verify `code_output` After contains processed `user_info` value | After value correct | step 9 | step 9: `get_run_details_state_after_value("code_output")` | asserted |
| 10 Verify no execution errors in timeline | no errors | step 10 | step 10: per-step `data-status`, console errors (excl. known `#1267`) | asserted |
| 11 YAML editor shows Code node `input: [user_info]`, `output: code_output` | YAML matches config | step 11 | step 11: `yaml.safe_load()` field assertions | asserted — via `pipeline_api.get_pipeline()` server-truth readback, NOT the UI YAML tab (hits the already-filed `EliteaAI/elitea-testing-public#1025` viewport-truncation defect — implementer amendment) |
| Expected Final State / Pass-Fail criteria | all steps complete, no errors | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 9's assertion is a substring/prefix check (`"Processed: "` + non-empty
  suffix), not an exact string match — *added: the LLM's greeting text is
  non-deterministic (different model completions across runs), so pinning an exact
  string would make the test flaky for a reason that isn't a real regression.*
- Step 10 explicitly excludes the known, filed `#1267` Stepper prop-leak console
  warning — *added: every other Run-Details-opening case in this suite (ELITEA-2450/
  2451/2452/2453) filters this exact signature; omitting the filter here would make
  this the only Run-Details case in the suite with a spuriously-red console-error
  assertion.*
- Step 2's edge-topology assertion (`LLM 1 → Code 1`, not two independent `→ END`
  edges) was NOT in the case's own text — *added: this is the exact observable that
  distinguishes a correctly-wired pipeline (which the case's remaining steps
  presuppose) from the build-method trap this session discovered; asserting it
  early makes a future regression to the trap fail loudly at step 2 instead of
  silently at step 9 (empty `code_output`).*

## Cleanup
1. This session created one throwaway pipeline during live exploration
   (`autotest_2446_code_state`, id `8809`, project 399 "Private") to confirm the
   Code node's execution semantics (4 probe runs, iterating the script's final
   statement) and **deleted it itself** via the three-dot menu's "Delete pipeline"
   flow (type-to-confirm dialog) before ending the session — confirmed via the
   `DELETE .../application/prompt_lib/399/8809 → 204 No Content` network response.
   No residue left behind.
2. Implementer teardown: new fixture (see Automation Hints) built via
   `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)` in
   teardown — same pattern as `pipeline_with_custom_state_var_id`/
   `pipeline_with_typed_state_vars_id`.

## Concrete Handles (discovered during exploration)

**Zero new testids needed — every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details panel).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node Input/Output selects, Value field, Structured output toggle | `pipeline-code-node-input-select-combobox` / `pipeline-code-node-output-select-combobox` / `pipeline-code-node-value` / `pipeline-code-node-structured-output-toggle` | **on-`automation/testids` ✓** — added by ELITEA-2009, reused unmodified via `PipelineDetailPage.get_code_node_input_value()` / `select_code_node_input_variable()` / `fill_code_node_value()` / etc. Confirmed live this session (4 probe runs). | none needed |
| Run Details panel, timeline step selector (per index), state row/value boxes | `pipeline-run-details-panel`, `pipeline-run-details-timeline-step-{index}`, `pipeline-run-details-state-row-{variable}`, `pipeline-run-details-state-value-{before,after}-{variable}` | **on-`automation/testids` ✓** — added by ELITEA-2450/2451/2452, reused unmodified via `PipelineDetailPage.select_run_details_timeline_step()` / `expand_run_details_state_row()` / `get_run_details_state_before_value()` / `get_run_details_state_after_value()`. Confirmed live: `code_output`'s row correctly renders and expands. | none needed |
| YAML view toggle + editor | `pipeline-yaml-view` / `pipeline-yaml-editor` | **on-main ✓** — added by ELITEA-2026, reused unmodified via `switch_to_yaml_view()` / `get_yaml_content()`. Confirmed live this session — `nodes:`/`state:`/`entry_point:` all render correctly. | none needed |
| STATE panel toggle / add-variable / close | `pipeline-state-drawer-toggle-button` / `pipeline-state-add-variable-button` / `pipeline-state-add-variable-name-input` / `pipeline-state-drawer-close-button` | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing (ELITEA-2042), reused unmodified. Only needed if the implementer chooses to add state vars via the Flow Editor UI rather than the recommended raw-YAML fixture. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation.
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on
  Save; **201 Created** confirmed live, 4 times across this session's iterations.
- Pipeline execution and all Run Details data (timeline, per-step state) arrive
  entirely over Socket.IO, same as every other Run Details case in this suite
  (ELITEA-2450/2451/2452/2453) — confirmed via `browser_network_requests` showing
  only `socket.io/?EIO=4…` exchanges around send/response, no dedicated REST
  endpoint for timeline/state.
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires
  on pipeline deletion; **204 No Content** confirmed live (session cleanup).

## Known Defects Found During Exploration

**No product defect found.** Two case-text CLARIFICATIONs (both confirmed live,
both explained by documented product behavior — see Coverage Map for the full
writeup):

1. **The case's own literal Code-node script text (step 4) does not work as
   written.** `output = f"Processed: {result}"` is a plain assignment; the runtime
   requires a bare dict-literal expression as the script's LAST statement
   (`{"code_output": f"Processed: {result}"}`) for `structured_output: true` to
   route the value into the declared `output:` variable. This matches
   `.claude/skills/elitea-pipeline/references/yaml-schema.md`'s own documented Code
   Node rule verbatim ("Return a dict literal as the LAST expression... Do NOT use
   a top-level `return`") — the product behaves exactly as documented; the case
   text is stale/ambiguous. Filed:
   [EliteaAI/elitea-testing-public#1383](https://github.com/EliteaAI/elitea-testing-public/issues/1383).
2. **Building the case's topology via the Flow Editor's "Add node" button does
   NOT auto-connect sequentially-added nodes.** 4 live probe runs (pipeline id
   8809) each showed `LLM 1` and `Code 1` landing with two INDEPENDENT
   `transition: END` edges (confirmed via the YAML view: `- id: LLM 1 ... transition:
   END` immediately followed by `- id: Code 1`, with no edge ever connecting them) —
   the Code node never executed as a result (only ONE Run Details timeline entry,
   `LLM1`, ever appeared; `code_output` stayed `""`/`""` across every probe,
   including after fixing the script per CLARIFICATION #1 above). This is a
   build-METHOD gotcha specific to manual Flow-Editor node placement, not a
   pipeline-execution defect: this suite's own `pipeline_llm_code_end` fixture
   (`automation/fixtures/data_fixtures.py:1986`) and every other execution-based
   pipeline fixture already sidestep it entirely by building via
   `PipelineAPI.create_pipeline()`/`create_pipeline_with_nodes()` with an EXPLICIT
   `transition:` field per node — which this AFS's own recommended fixture (see
   Automation Hints) does. Filed:
   [EliteaAI/elitea-testing-public#1384](https://github.com/EliteaAI/elitea-testing-public/issues/1384).

3. **IMPLEMENTER AMENDMENT (confirmed live during implementation): the Run
   Details timeline label for a Code node's step is `"pyodide"` (the Python
   sandbox executor's name), not the space-stripped YAML id `"Code1"`.** The
   convention documented by ELITEA-2450/2452 (id, space stripped —
   `"LLM1"`/`"LLM2"`) does NOT generalize to Code nodes. The mechanism itself
   (index-based `select_run_details_timeline_step(1, ...)`, reading that
   step's state rows) is correct and unaffected — only the expected label
   text. Filed:
   [EliteaAI/elitea-testing-public#1385](https://github.com/EliteaAI/elitea-testing-public/issues/1385).

`elitea_state.get(...)` (the case's literal spelling) IS confirmed valid — NOT a
case-text drift. `.claude/skills/elitea-pipeline/references/yaml-schema.md:212`
documents the sandbox's state preamble as restoring BOTH `elitea_state` AND
`alita_state` (aliases of each other); this session's exploration used
`elitea_state.get('user_info', '')` throughout and it correctly read the value
(confirmed live: `user_info`'s Run Details After value was the LLM's actual
response text, and the fixed Code-node script's `result` variable correctly picked
it up once the dict-literal-return fix was applied — the only remaining blocker
being CLARIFICATION #2's disconnected-edge gotcha, not the state accessor name).

## Blocked Steps

None. All 11 case steps (plus this AFS's own build-topology verification) were
exercised live this session; the two gotchas above were isolated to their root
cause and routed around via the documented fix (dict-literal return) and the
documented build method (YAML/API construction, not Flow-Editor clicks) — no step
remains unexplained or unautomatable.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new
  testids needed (see Concrete Handles).
- **New fixture needed**: no existing fixture builds `LLM 1 → Code 1 → END` with
  TWO custom state variables (`user_info`, `code_output`) and an LLM node whose
  `output` writes to a non-`messages`/non-built-in variable. Recommend
  `pipeline_llm_reads_state_via_code` (or similar) in `automation/fixtures/
  data_fixtures.py`, built via `PipelineAPI.create_pipeline()` with the raw YAML
  `instructions` string in this AFS's § Test Data — mirrors
  `pipeline_with_typed_state_vars_id`'s create/yield/delete pattern (NOT
  `create_pipeline_with_nodes()`, which has no `state:` support).
- **CONFIRMED LIVE GOTCHA (do not rebuild this topology via Flow-Editor clicks)**:
  see Known Defects #2. Always build via YAML/API with explicit `transition:`
  chaining for any case that needs the pipeline to actually EXECUTE end-to-end
  (as opposed to ELITEA-2009's UI-config-persistence-only case, which never
  executes and therefore never hit this gotcha).
- **Code node script convention**: end with a bare dict-literal expression as the
  LAST statement when `structured_output: true` — `{"code_output": f"Processed:
  {result}"}`, not `code_output = f"Processed: {result}"`. See Known Defects #1.
- **Reuse ELITEA-2452's Run Details Before/After methods unmodified**:
  `open_run_details_panel()`, `select_run_details_timeline_step(index)`,
  `get_run_details_selected_timeline_step_id()`, `expand_run_details_state_row()`,
  `get_run_details_state_before_value()`, `get_run_details_state_after_value()`,
  `get_run_details_timeline_step_status(index)`. All confirmed working against a
  Code-node timeline entry once the topology is correctly wired (this session
  confirmed `user_info`'s Before/After correctly reflected the LLM's write at the
  `LLM1` step; the SAME mechanism will show `code_output`'s Before/After at the
  `Code1` step once built via the recommended fixture).
- **Reuse ELITEA-2027/2042's `yaml.safe_load()` + field-assertion pattern**
  unmodified for step 11 — `next(n for n in parsed["nodes"] if n["id"] == "Code
  1")`, then assert `node["input"] == ["user_info"]` and `node["output"] ==
  ["code_output"]`.
- Wait strategy: `wait_for_embedded_chat_response()` after sending the chat
  message (never a fixed sleep), then `expect(pipeline_page.run_node_label).to_be_visible()`
  before opening Run Details — same as every other pipeline-execution case in
  this suite.
- `_surface.md` updated this session — see the new "Code node — execution &
  build-method gotchas" section documenting the disconnected-edge trap and the
  dict-literal-return requirement, so no future analyst/implementer rediscovers
  either by hand.
