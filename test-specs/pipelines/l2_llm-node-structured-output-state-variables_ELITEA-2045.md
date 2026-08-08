# Test Case: Pipeline — Structured Output (Parse LLM Response into State Variables)

## Metadata
- **TMS ID**: ELITEA-2045
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline with an LLM node exists — created by this case's own steps 1-2 (fresh
  empty pipeline via `pipeline_id` fixture + an LLM node added via the canvas "+"
  menu, same convention as `l2_llm-node-system-task-chat-history-config_ELITEA-2004.md`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- `pipeline_id` fixture (fresh, empty pipeline; deleted at test end).
- 4 custom STATE variables added via the STATE panel's UI, matching the case's own
  names/types exactly: `name` (String/`str`), `age` (Number/`number`), `hobbies`
  (List/`list`), `metadata` (Json/`dict`).
- SYSTEM prompt value: `"Act as JSON Parser and parse user data into structured fields"`
  (verbatim from the case's Test Data table).
- Chat message sent to trigger execution: any short instruction naming all 4 fields
  with parseable values (this session used a message like `"My name is John, I am
  30 years old, my hobbies are reading and hiking, and my metadata is {\"source\":
  \"test\"}."` — content is LLM-nondeterministic beyond "the 4 fields are present
  and parseable", matching the caution already established in
  `l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md`).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project was
  "Private" (id 399), matching `.env.test`.

## Test Steps
1. Create a pipeline with an LLM node.
   **Expected**: pipeline is created, LLM node appears on the canvas.
   Confirmed live via `pipeline_id` fixture + `add_node("LLM")` +
   `wait_for_node_on_canvas("llm")` — identical mechanism to ELITEA-2004.
2. In State panel, add 4 output variables: `name` (String), `age` (Number),
   `hobbies` (List), `metadata` (Json).
   **Expected**: all 4 variables are added to the STATE panel, each with its
   selected type. Confirmed live this session via `open_state_panel()` +
   `add_state_variable(name)` + `select_state_variable_type(name, type_key)`
   for each of the 4 — same mechanism already automated by ELITEA-2042 for a
   single variable, exercised here 4×.
3. In the LLM node, add all created variables to the Output combobox: `name`,
   `age`, `hobbies`, `metadata`.
   **Expected**: all 4 variables are added to Output. Confirmed live: the
   Output multi-select shows all 4 as chips; **the multi-select requires a
   close (Escape)-then-reopen cycle between EACH selection** — selecting two
   variables back-to-back without closing/reopening the popover silently
   drops the second selection (confirmed live this session: `age` selected
   directly after `name` without closing landed correctly, but attempting
   `hobbies` immediately after in the same open popover did NOT register —
   reopening and re-selecting `hobbies`/`metadata` in separate open/select/
   close cycles fixed it). This matches the existing
   `_select_multi_select_option_and_close()` helper's own docstring warning
   ("left open, the still-visible popover intercepts the next select's
   click") — **automation implication**: call
   `select_llm_node_output_variable(name)` once per variable (it already
   performs the open→select→Escape→wait-closed cycle internally); do NOT
   batch multiple option clicks inside one open popover.
4. Enable "Structured output" switch on the node.
   **Expected**: Structured output switch is enabled (checked). Confirmed
   live via `pipeline-llm-node-structured-output-toggle` — click toggles it
   to `checked`.
5. Configure SYSTEM prompt: "Act as JSON Parser and parse user data into
   structured fields".
   **Expected**: SYSTEM prompt is configured. Confirmed live via
   `fill_llm_node_section_value("system", ...)` / `get_llm_node_section_value("system")`.
6. Save pipeline.
   **Expected**: Pipeline saves without errors. Confirmed live via
   `save_and_wait_for_update()` → `201 Created`; the PUT response body's
   `version_details.instructions` contains the full, correct YAML (verified
   directly from the network response this session — see Known Defects for
   why this matters).
7. Execute with input containing data matching the output schema.
   **Expected**: Pipeline execution completes. Automated the same way as
   ELITEA-2453's fixture pipeline — `send_message_in_embedded_chat()` +
   `wait_for_embedded_chat_response()`, then confirm `run_node_label` /
   Run Details status is `"Completed"`.
   **CRITICAL — do NOT include `messages` in this node's Output list** (only
   `name`/`age`/`hobbies`/`metadata`, exactly as case step 3 specifies). See
   Known Defects: combining `messages` with `dict`/`list`-typed custom
   variables in a `structured_output: true` node's `output` mapping is the
   CONFIRMED, already-filed `EliteaAI/elitea-testing-public#1274` — this
   case's own step 3 never asks for `messages` in Output, so the fixture
   naturally avoids the defect without any special-casing.
8. Verify response correctly parses values into each state variable.
   **Expected — mechanism confirmed by the already-merged, structurally
   identical `l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md`**
   (same single-LLM-node + `structured_output: true` + 4 typed custom
   output-variable shape, different variable names/types only): open the
   Run Details panel (`open_run_details_panel()`), each of `name`/`age`/
   `hobbies`/`metadata` appears as its own accordion row
   (`pipeline-run-details-state-row-{variable}`) with an After value
   rendered per its OWN type's `JSON.stringify` shape — `name` (str) a
   JSON-quoted string, `age` (number) a bare numeral, `hobbies` (list) a
   bracketed JSON array, `metadata` (dict/Json) a braced JSON object. This
   AFS reuses ELITEA-2453's exact assertion shapes (parse-and-type-check,
   not exact literal values — LLM output content is nondeterministic).
9. Verify in YAML: node has `structured_output: true` and output lists all
   variable names.
   **Expected (case text) / CONFIRMED LIVE DEFECT, already filed
   `EliteaAI/elitea-testing-public#1025`**: the Pipeline YAML tab
   (`pipeline-yaml-editor`, CodeMirror) **silently truncates long documents
   at default viewport size** — for this case's 40-line pipeline YAML, the
   rendered DOM stops dead at line 34 (`output:\n      - name`), NEVER
   rendering `- age`/`- hobbies`/`- metadata`/`structured_output: true`/
   `transition: END`, even though `.cm-scroller`'s `scrollHeight` reports
   equal to `clientHeight` (960px both) — the editor believes there is
   nothing more to scroll to, so there is **no UI-reachable way** to see the
   rest at default viewport. Confirmed via a live A/B this session:
   (a) the PUT-save network response body's `version_details.instructions`
   field contains the full, correct 40-line YAML (`structured_output: true`
   and all 4 output names present — ground truth, the backend persisted
   correctly); (b) the SAME data read via `pipeline-yaml-editor`'s DOM
   (`.cm-line` elements) stops at line 34, missing exactly the fields this
   case's step 9 needs to verify; (c) resizing the browser viewport taller
   (1400×2200) makes the full 40 lines render, confirming the root cause is
   viewport-height-driven, not a data-persistence defect. This is the
   IDENTICAL symptom already described in issue #1025 (filed during
   ELITEA-2010, a different node type/pipeline) — commented this session
   with the ELITEA-2045 reproduction instead of filing a duplicate.
   **Automation implication (per #1025's own documented workaround)**:
   verify `structured_output: true` + the output variable list via
   `pipeline_api.get_pipeline(pipeline_id)["version_details"]["instructions"]`
   (parsed with `yaml.safe_load`), NOT via the YAML-tab DOM — this is the
   SAME `pipeline_api.get_pipeline()` pattern already used by
   `test_pipeline_yaml_editor_invalid_syntax.py` (ELITEA-2068) and
   `test_pipeline_advanced.py` to read server-side truth. The case's own
   intent — "verify structured_output:true and all variable names in the
   YAML" — is satisfied by this read (the YAML string IS what the case
   means by "in YAML"); only the specific act of reading it through the
   on-screen editor DOM is blocked by #1025.

## Expected Final State
The LLM node with Structured output enabled correctly parses a complex response
into 4 named typed state variables (`name`/str, `age`/number, `hobbies`/list,
`metadata`/dict). The persisted pipeline YAML (verified via the API, per Known
Defects #1025) confirms `structured_output: true` and `output: [name, age,
hobbies, metadata]`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline with LLM node | Pipeline created with LLM node | step 1 | step 1 | asserted |
| 2 Add 4 output vars to State panel (name/age/hobbies/metadata) | All 4 added | step 2 | step 2 | asserted |
| 3 Add all 4 vars to LLM node Output combobox | All 4 added to Output | step 3 | step 3 | asserted — **CLARIFICATION**: multi-select requires an open→select→close cycle PER variable, not one open popover with 4 clicks (case text doesn't specify the mechanic; documented as an automation gotcha, not a defect) |
| 4 Enable Structured output switch | Switch enabled (checked) | step 4 | step 4 | asserted |
| 5 Configure SYSTEM prompt | Prompt configured | step 5 | step 5 | asserted |
| 6 Save pipeline | Saves without errors | step 6 | step 6 | asserted |
| 7 Execute with matching input | Execution completes | step 7 | step 7 | asserted |
| 8 Verify response parses into each state variable | Each variable populated correctly | step 8 | step 8 | asserted (mechanism proven by already-merged ELITEA-2453 for the structurally identical shape) |
| 9 Verify in YAML: structured_output:true + output lists all names | YAML confirms both | step 9 | step 9 | asserted — **CONFIRMED LIVE DEFECT `EliteaAI/elitea-testing-public#1025`**: the on-screen YAML tab cannot show this for a document this long (truncates before reaching `structured_output`); verified via `pipeline_api.get_pipeline()` instead — see Known Defects |

### Axis 2 — Assertions beyond the case

- No unexpected console errors across the full flow (node add, state-var add,
  output-select, structured-output toggle, save, execute, Run Details open,
  YAML-tab open), excluding the known, filed, deterministic
  `EliteaAI/elitea-testing-public#1267` Stepper prop-leak warning (same
  signature already excluded by `test_pipeline_run_details_multiple_state_variables.py`
  and `test_pipeline_run_details_panel.py`) — *added: this flow touches enough
  distinct UI surfaces (State panel, LLM node config, Run Details, YAML tab)
  that a regression in any one is worth guarding globally, not just per-step.*
- Each typed variable's After value is asserted by TYPE SHAPE (JSON-quoted
  string / bare number / bracketed array / braced object), never an exact
  literal — *added: LLM output content is nondeterministic; only the
  type-rendering contract is stable (same caution ELITEA-2453 already
  established for this identical mechanism).*

## Cleanup
1. Delete the pipeline via `pipeline_id` fixture teardown (automatic).

## Concrete Handles (discovered during exploration — ALL PRE-EXISTING, zero new testids needed)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| STATE panel open/add-variable/type-select | `pipeline-state-drawer-toggle-button`, `pipeline-state-add-variable-button`, `pipeline-state-add-variable-name-input`, `pipeline-state-variable-type-select-{name}` (template), `pipeline-state-type-option-{type_key}` (template) | **on-`automation/testids` only**, reused unmodified from ELITEA-2042 — already wired as `PipelineDetailPage.open_state_panel()`/`.add_state_variable()`/`.select_state_variable_type()`. Confirmed live this session for all 4 of this case's own variable names/types. | none needed |
| LLM node Output multi-select | `pipeline-llm-node-output-select` + dynamic `select-option-{variable}` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.llm_node_output_select` / `.select_llm_node_output_variable(name)`. Confirmed live for `name`/`age`/`hobbies`/`metadata` — **must be called once per variable** (see step 3 clarification). | none needed |
| LLM node Structured output toggle | `pipeline-llm-node-structured-output-toggle` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.llm_node_structured_output_toggle`. Confirmed live: `checked` after click; node YAML gains `structured_output: true` (verified via API, not the YAML tab — see Known Defects). | none needed |
| LLM node SYSTEM Value field | `pipeline-llm-node-system-value` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.fill_llm_node_section_value("system", ...)` / `.get_llm_node_section_value("system")`. | none needed |
| LLM node TASK Type/Value (for execution — F-String `{input}`) | `pipeline-llm-node-task-type-select-combobox`, `pipeline-llm-node-task-value` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.select_llm_node_section_type("task", "F-String", ...)` / `.fill_llm_node_section_value("task", "{input}")`. Confirmed live this session: without this, the chat message text never reaches the LLM node (TASK stays empty). | none needed |
| Save button | `agent-save-button` | reused unmodified, already wired as `PipelineDetailPage.save_and_wait_for_update()`. | none needed |
| Embedded chat send/wait | (page-object methods, no raw testid needed here) | already wired as `PipelineDetailPage.send_message_in_embedded_chat()` / `.wait_for_embedded_chat_response()` / `.get_embedded_chat_message_count()`, reused unmodified from ELITEA-2453. | none needed |
| Run node label / Run Details panel / status / state rows / value boxes | `pipeline-run-node-label`, `pipeline-run-details-panel`, `pipeline-run-details-state-row-{variable}`, `pipeline-run-details-state-value-{before\|after}-{variable}` | **on-`automation/testids` only**, reused unmodified from ELITEA-2450/2452/2453 — already wired as `PipelineDetailPage.open_run_details_panel()` / `.get_run_details_status()` / `.get_run_details_state_row_locator()` / `.expand_run_details_state_row()` / `.get_run_details_state_after_value()`. | none needed |
| Server-side YAML readback (workaround for `#1025`) | `pipeline_api.get_pipeline(pipeline_id)["version_details"]["instructions"]` | API client method, already used by `test_pipeline_yaml_editor_invalid_syntax.py` / `test_pipeline_advanced.py` for the same server-truth-readback pattern. | none needed |

## Network Behavior
- `PUT /elitea_core/application/prompt_lib/{project}/{id}` — fires on Save,
  `201 Created`; response body's `version_details.instructions` is the
  authoritative persisted YAML (confirmed correct and complete this session,
  in contrast to the YAML-tab's own truncated DOM rendering — see Known
  Defects).
- Pipeline execution + Run Details data arrive over Socket.IO (same as every
  other pipeline-execution case in this family — ELITEA-2450/2452/2453); no
  dedicated REST endpoint for the run timeline/state snapshots.

## Known Defects Found During Exploration

1. **CONFIRMED, already filed `EliteaAI/elitea-testing-public#1025`** (commented
   with this session's reproduction, not re-filed): the Pipeline YAML tab
   (`pipeline-yaml-editor`) silently truncates rendering of long node YAML at
   default viewport size — this case's 40-line document stops rendering after
   line 34, never showing `structured_output: true` or the trailing 3 of 4
   `output` list items, with no scrollbar offered (`.cm-scroller` reports
   `scrollHeight === clientHeight`, i.e. the editor itself believes nothing is
   being cut off). Confirmed display-only (not a persistence bug) via the PUT
   save response body, which contains the full correct YAML. **Automation
   impact**: this AFS's step 9 verifies `structured_output`/`output` via
   `pipeline_api.get_pipeline()` instead of the YAML-tab DOM, per #1025's own
   documented workaround ("Verify persistence via the API ... instead of the
   YAML tab for configurations this long").
2. **Not triggered, confirmed by design**: `EliteaAI/elitea-testing-public#1274`
   (LLM node `structured_output: true` + `messages` combined with dict/list
   custom vars in `output` → raw backend error) does not apply here — this
   case's own step 3 only ever asks for `name`/`age`/`hobbies`/`metadata` in
   Output, never `messages`, so the fixture naturally avoids it.

## Blocked Steps
None. All 9 case steps are automatable — step 9's literal "read the on-screen
YAML tab" sub-mechanic is blocked by `#1025`, but the case's actual intent
(verify `structured_output: true` + the output variable list are correctly
persisted) is fully verifiable via the API, which this AFS does.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Zero new testids needed — every handle is already wired on
  `automation/testids`, reused from ELITEA-2004/2042/2450/2452/2453.
- Reuse `pipeline_id` fixture (fresh empty pipeline) + `add_node("LLM")` +
  `wait_for_node_on_canvas("llm")`, same as ELITEA-2004 — no new fixture
  needed (unlike ELITEA-2453, which needed a pre-seeded-state-vars fixture;
  this case's own steps 1-2 create the state vars via UI, which IS the case's
  scope, so no shortcut fixture is appropriate here).
- **Call `select_llm_node_output_variable(name)` once per variable, not 4
  clicks inside one open popover** — see step 3's clarification.
- **Set TASK Type=F-String, Value=`{input}`** so the chat message content
  actually reaches the LLM node (the case's steps don't mention this
  explicitly, but without it there is no way for the LLM to receive the
  user's data to parse — same convention ELITEA-2453's fixture YAML already
  established for this exact node shape).
- **Read `structured_output`/`output` via `pipeline_api.get_pipeline(pid)`,
  never via the YAML tab** — see Known Defects #1025.
- Reuse `open_run_details_panel()`, `get_run_details_state_row_locator()`,
  `expand_run_details_state_row()`, `get_run_details_state_after_value()`
  unmodified from ELITEA-2452/2453 for step 8 — same type-shape assertion
  pattern (`startswith('"')`/`json.loads()` + `isinstance()`) as
  `test_pipeline_run_details_multiple_state_variables.py`.
- Wait discipline: `wait_for_embedded_chat_response()` for run completion,
  `expect(locator).to_be_visible()` after accordion-expand clicks (same as
  ELITEA-2453).
