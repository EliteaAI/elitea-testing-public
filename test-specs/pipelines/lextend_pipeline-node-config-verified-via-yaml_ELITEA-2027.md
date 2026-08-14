# Test Case: Pipeline — Verify Node Configuration via YAML (Automation Approach)

## Metadata
- **TMS ID**: ELITEA-2027
- **Priority**: l2 (high, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend `dev.elitea.ai`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-08
- **Status**: extend-existing

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_llm_node_system_task_chat_history_config.py`
  (TMS ELITEA-2004, already extended once for ELITEA-2040 — this is a second, independent
  extension of the same file), merged to `origin/automation/base` (`97ac7c97`).
- **Behavioural overlap**: ELITEA-2004's merged test already builds the exact scenario ELITEA-2027
  needs as its precondition — a fresh pipeline, an LLM node added via the canvas "+" menu, its
  SYSTEM/TASK/CHAT HISTORY sections configured (Type + Value) and Input/Output state-variable
  selects set, then Save. `test_pipeline_yaml_editor_view.py` (ELITEA-2026, merged `6972e228`)
  separately proves the Flow/Yaml toggle mechanics and that the YAML text contains the
  `entry_point:`/`nodes:`/`state:` keywords (string presence only). Neither existing spec parses
  the YAML and asserts specific field VALUES (`state.<var>.type`, `entry_point == <node id>`,
  `nodes[].input_mapping.<section>.{type,value}`, `nodes[].output`, `nodes[].structured_output`,
  `nodes[].transition`) — this is the case's actual ask ("establish the automation approach of
  verifying node configuration by reading YAML rather than inspecting individual UI fields").
  `test_pipeline_state_panel_default_and_custom_variables.py` (ELITEA-2042, merged) already
  demonstrates the `yaml.safe_load()`-and-assert-fields technique for the `state:` section only
  (not `nodes:`/`entry_point`) — reused here as the parsing pattern.
- **The gap**: no merged spec ever parses the `nodes[]` array's `input_mapping`/`output`/
  `structured_output`/`transition` fields, nor asserts `entry_point` equals the actual node id
  (`test_pipeline_yaml_editor_view.py` only checks the literal substring `"entry_point:"` is
  present in the text, not what it equals). This is a genuinely new, previously-unexercised
  assertion surface on the identical node/page-object/fixture ELITEA-2004 already builds — an
  **incremental addition** (new assertions on data already flowing through the existing
  configure-and-save flow), not a near-rewrite. ELITEA-2004's own test body, assertions, and
  terminal (Fixed/Fixed) persisted-state checks for SYSTEM/TASK/CHAT HISTORY are untouched.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_llm_node_system_task_chat_history_config.py`), reusing the same `pipeline_id`
  fixture and `PipelineDetailPage` LLM-node-config methods (SYSTEM/TASK/CHAT HISTORY Type+Value,
  Input/Output selects) plus the STATE-panel methods already proven by ELITEA-2042
  (`open_state_panel`/`add_state_variable`/`close_state_panel`) and the YAML methods already
  proven by ELITEA-2026 (`switch_to_yaml_view`/`get_yaml_content`), configures the LLM node with
  THIS case's own literal test data, adds a custom state variable `output1` (so the case's own
  desired Output variable exists to select), saves, then parses the YAML and asserts the specific
  `state`/`entry_point`/`nodes[]` field values the case names. Does not modify ELITEA-2004's or
  ELITEA-2040's existing test bodies.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: Keycloak via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- No pre-existing LLM node or custom state variable is required — starts from a bare empty
  pipeline, same as ELITEA-2004; the `output1` state variable is created live by the test itself
  (case's own Test Data table names `output1` as the desired Output — it does not pre-exist on a
  fresh pipeline, so it must be created via the STATE panel before it can be selected as Output,
  exactly the same "create custom var, then select it downstream" flow ELITEA-2042 already proved
  end-to-end for the Input select).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh empty pipeline (`autotest_<test_name>`), via `PipelineAPI.create_pipeline()` — identical
  pattern to ELITEA-2004's `pipeline_id` fixture (`automation/fixtures/data_fixtures.py:119`).
- A custom state variable `output1` (type `String`, left at its default type — the case's own
  step 4 wants `output1 (type: str)`, and `String` is the STATE panel's default type for a newly
  added variable, confirmed live and already exercised by ELITEA-2042's `custom_output` variable).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).
- Exact case Test Data table values, all confirmed to work as typed with no substitution needed:
  - SYSTEM Type=`Fixed`, Value=`Act as helper`
  - TASK Type=`F-String`, Value=`{input}`
  - CHAT HISTORY Type=`Fixed`, Value=`[]`
  - Input=`input`, Output=`output1` (the freshly-created custom state variable)

## Test Steps

1. Create a pipeline via `PipelineAPI.create_pipeline()`, navigate to
   `${BASE_URL}/pipelines/all/{pipeline_id}?destTab=configuration&viewMode=owner`.
   - **Verify**: configuration panel + canvas load (reuse of ELITEA-2004's step 1 mechanics).
2. Open the STATE panel (`pipeline-state-drawer-toggle-button`) and add a custom variable named
   `output1` via `add_state_variable()` (the panel's `+` control, commit via Enter — same
   mechanism ELITEA-2042 already proved), then close the panel.
   - **Verify**: `output1` appears in the STATE panel's variable list alongside the default
     `input`/`messages` rows (same assertion shape ELITEA-2042 already uses).
3. Add an LLM node via the canvas "+" menu (`pipeline-add-node-button` →
   `pipeline-add-node-menu-item-llm`).
   - **Verify**: LLM node appears on canvas with a non-empty `data-id` (`wait_for_node_on_canvas`).
4. Configure SYSTEM: Type already `Fixed` by default (no action) — fill Value
   (`pipeline-llm-node-system-value`) with `Act as helper`.
   - **Verify**: `input_value()` reflects the typed text.
5. Configure TASK: switch Type to `F-String` (`select-option-fstring`), fill Value
   (`pipeline-llm-node-task-value`) with `{input}`.
   - **Verify**: Type select shows `F-String`; Value `input_value()` is `{input}`.
6. Configure CHAT HISTORY: Type already `Fixed` by default (no action) — fill Value
   (`pipeline-llm-node-chat-history-value`) with `[]`.
   - **Verify**: `input_value()` is `[]`.
7. Set Input select (`pipeline-llm-node-input-select`) to `input`; set Output select
   (`pipeline-llm-node-output-select`) to `output1` (now available since step 2 created it —
   confirmed live: the Output select's option list includes `select-option-output1` once the
   custom state variable exists, same mechanism ELITEA-2042 confirmed for the Input select).
   - **Verify**: Input select shows `input`; Output select shows `output1`.
8. Confirm the Structured output toggle (`pipeline-llm-node-structured-output-toggle`) is
   unchecked (case's own Test Data: `structured_output: false` — the field's default, no action
   needed).
   - **Verify**: `is_checked()` is `False`.
9. Save the pipeline (`agent-save-button`).
   - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}`
     returns `201 Created`; zero console errors from before step 1 through after step 9.
10. Switch to Yaml view (`switch_to_yaml_view`) and parse the editor's content with
    `yaml.safe_load()`.
    - **Verify** (case step 4 — `state:` section): `state.input.type == "str"`,
      `state.messages.type == "list"`, `state.output1.type == "str"` — confirmed live this
      session, exact match.
    - **Verify** (case step 5 — `entry_point`): `entry_point` equals the LLM node's own `data-id`
      (captured in step 3) — confirmed live this session (`entry_point: LLM 1` for a node whose
      `data-id` is `LLM 1`; a fresh pipeline's first/only node auto-becomes the entry point).
    - **Verify** (case step 6 — `nodes[]`): the parsed `nodes` list contains exactly one entry
      whose `id` equals the captured node id, and on that entry: `type == "llm"`,
      `input == ["input"]`, `input_mapping["system"] == {"type": "fixed", "value": "Act as helper"}`,
      `input_mapping["task"]["type"] == "fstring"` and `"{input}" in input_mapping["task"]["value"]`,
      `input_mapping["chat_history"]["type"] == "fixed"` — see the CLARIFICATION below for the
      `chat_history` value's exact assertion shape — `output == ["output1"]`,
      `structured_output is False`, `transition == "END"` — all confirmed live this session,
      exact match to the case's own field list.

## Expected Results
- Parsing the pipeline's YAML view is a viable, fully-automatable technique for verifying node
  configuration end-to-end (state variables, entry point, and every `input_mapping`/`output`/
  `structured_output`/`transition` field of a configured node) without touching any individual UI
  form field for the verification itself — confirmed live this session by constructing exactly
  this assertion set from a real saved pipeline.
- Every field the case names in its Test Data table round-trips through Save → YAML exactly as
  configured via the Flow editor.
- No console errors, no failed (≥400) network requests, at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, project with Pipelines access | setup exists | step 1 | step 1: panel visible | asserted |
| 1 Create a pipeline with an LLM node configured via Flow view (SYSTEM/TASK/CHAT HISTORY + Input/Output) | LLM node configured, pipeline ready to save | steps 2–7 | steps 4–7 | asserted |
| 2 Save pipeline | Pipeline saves without errors | step 9 | step 9: `201` + zero console errors | asserted |
| 3 Switch to "Yaml" view | YAML editor displays the pipeline definition | step 10 | step 10: `switch_to_yaml_view()` + non-empty parse | asserted |
| 4 Parse YAML content and verify state section: input(str), messages(list), output1(str) | State section matches expected variables/types | step 10 | step 10, first sub-check | asserted |
| 5 Verify entry_point matches the LLM node id | entry_point references the correct node | step 10 | step 10, second sub-check | asserted |
| 6 Verify nodes array contains the LLM node with all named fields | All LLM node fields in YAML match Flow editor config | step 10 | step 10, third sub-check | asserted |
| 7 Confirm this YAML-based approach should be used for all node types in automation | YAML accurately represents node config | — | steps 10's sub-checks collectively | **CLARIFICATION — not an independently-automatable assertion.** This is a methodological/process statement about the TEAM's automation approach going forward, not a product behavior with a pass/fail predicate of its own. It is satisfied by steps 10's assertions existing as a working, reusable example (`yaml.safe_load()` + field-level asserts on `state`/`entry_point`/`nodes[]`) — the same pattern any future node-type case can copy. No separate assertion is added for this step. |
| Expected Final State: YAML accurately reflects LLM node config; all state vars/node fields/mappings/transitions match | — | step 10 | step 10 | asserted |
| Pass/Fail: all steps complete without errors; all YAML fields match configured values exactly | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 8 explicitly confirms the Structured output toggle is unchecked BEFORE save, rather than
  silently assuming the default and only checking the YAML's `structured_output: false` after the
  fact — *added so a regression that flips the UI's default checked-state would be caught at the
  UI layer too, not just via the YAML round-trip (same "confirm the pre-action default explicitly"
  pattern ELITEA-2004 already uses for SYSTEM/CHAT HISTORY's default Fixed type).*
- No console-error / no-failed-request assertion was in the original case text; added it to
  step 9 (checked across the whole flow, steps 1–10) — standard practice per this project's
  `test-case-analysis` skill; zero console errors and zero ≥400 responses observed this session.
- **CLARIFICATION — CHAT HISTORY's YAML `value` field is an actual empty LIST, not the string
  `"[]"`, once explicitly typed** (case Test Data literally reads `CHAT HISTORY type/value: fixed
  / "[]"`, implying a string). Confirmed live this session via a controlled before/after probe:
  typing the two-character text `[]` into the Value textarea and saving serializes to YAML as
  `value: []` (unquoted flow-sequence — parses as `[]`, an empty `list`, under `yaml.safe_load()`),
  while typing a control string that is NOT valid YAML on its own (`[][]`) serializes as
  `value: '[][]'` (quoted, parses as the `str` `"[][]"`). This means the backend does not force a
  string type for this field — it stores/serializes whatever was typed as YAML, and `"[]"`
  happens to be syntactically valid YAML for an empty list. **This is not a defect** — per the
  reverse-masking guard (`test-automation-implementation` skill § Hard Rules → 2), the correct
  assertion is the LIVE representation (`input_mapping["chat_history"]["value"] == []`, an empty
  Python list), not a naive string comparison against the case's literal `"[]"` wording, which
  would fail against the live, correctly-functioning product.

## Gap Assertions (what ELITEA-2004's covering test does NOT already prove — for the implementer)

1. **`nodes[].input_mapping` field-level assertions** — ELITEA-2004 asserts these via the UI
   (`get_llm_node_section_type`/`get_llm_node_section_value`), never via the persisted YAML. This
   extension asserts the SAME configured values through the YAML instead (step 10).
2. **`entry_point` equals the actual node id** — `test_pipeline_yaml_editor_view.py` (ELITEA-2026)
   only checks the substring `"entry_point:"` is present, never what it equals.
3. **`nodes[].output`/`structured_output`/`transition` fields** — never asserted via YAML anywhere
   in the merged suite (ELITEA-2004 asserts Output only via the UI combobox; structured_output and
   transition are never asserted at all on the LLM node, in any existing spec).
4. **A custom state variable used as a node's Output (not just Input)** — ELITEA-2042 proves a
   custom var is selectable as *Input*; this extension is the first to prove one is selectable as
   *Output* and that it appears correctly in `state:` alongside the built-in `input`/`messages`.
5. **The reusable "verify config via YAML" pattern itself** — the case's stated purpose (step 7)
   is establishing this AS the approach; this extension IS that established, reusable example.

## Cleanup
1. This session created one throwaway pipeline during exploration (`autotest_explore_2027_yaml`,
   id `8389`, project `399`) to confirm the exact YAML shape (state/entry_point/nodes fields,
   including the chat_history value-type probe above) and **deleted it itself** via the three-dot
   menu's Delete pipeline flow (type-to-confirm dialog) before ending the session — confirmed via
   the post-delete redirect to `/pipelines/all`. No residue left behind.
2. Implementer teardown: standard `pipeline_id` fixture pattern (`PipelineAPI.create_pipeline()`
   in setup, `PipelineAPI.delete_pipeline(pid)` in teardown) — same as ELITEA-2004, no new fixture
   needed. The custom `output1` state variable lives inside the pipeline's own JSON and is deleted
   with it — no separate cleanup call.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| STATE panel toggle / add-variable / name input / close | `pipeline-state-drawer-toggle-button` / `pipeline-state-add-variable-button` / `pipeline-state-add-variable-name-input` / `pipeline-state-drawer-close-button` — all pre-existing, confirmed working (ELITEA-2042); page object already exposes `open_state_panel()`/`add_state_variable(name)`/`close_state_panel()` | none needed |
| LLM node SYSTEM/TASK/CHAT HISTORY Type+Value, Input/Output selects | `pipeline-llm-node-{system,task,chat_history}-{type-select,value}` / `pipeline-llm-node-input-select` / `pipeline-llm-node-output-select` — all pre-existing, confirmed working (ELITEA-2004) | none needed |
| Output select's new-variable option | `[data-testid="select-option-output1"]` — confirmed live: appears in the Output select's popover once the STATE panel's `output1` variable exists, same `select-option-{value}` mechanism already used for `input`/`messages` | `[data-testid^="select-option-"]` to enumerate |
| Structured output toggle | `pipeline-llm-node-structured-output-toggle` — pre-existing `LocatorDescriptor`; read via the field's own `.is_checked()` (no new page-object method needed — same direct-Playwright-call-on-a-field pattern ELITEA-2004 already uses for `.is_visible()`) | none needed |
| YAML view toggle + editor | `pipeline-yaml-view` / `pipeline-yaml-editor` — pre-existing, confirmed working (ELITEA-2026); page object already exposes `switch_to_yaml_view()`/`get_yaml_content()`/`switch_to_flow_view()` | none needed |
| Add LLM node | `pipeline-add-node-button` → `pipeline-add-node-menu-item-llm` — pre-existing, confirmed working | none needed |
| Pipeline Save button | `agent-save-button` — pre-existing, confirmed working, reused from ELITEA-2004 | none needed |

No new testids are needed for this extension — every element it touches already carries one from
ELITEA-2004/ELITEA-2026/ELITEA-2042's prior work.

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires
  on Save; `201 Created` on success; persists the LLM node's full config (SYSTEM/TASK/CHAT
  HISTORY/Input/Output/structured_output) AND the `output1` state variable in one payload —
  confirmed via live network capture this session.
- No request fires on switching to/from the Yaml view — it renders client-side from the same
  in-memory pipeline state the Flow view uses (confirmed: `useExport`/YAML view read from
  `yamlJsonObject` context, no XHR).

## Known Defects Found During Exploration

**None.** All case steps produced the expected result end-to-end: the STATE panel's custom
variable flow, the LLM node's SYSTEM/TASK/CHAT HISTORY/Input/Output configuration, Save, and the
YAML view's `state`/`entry_point`/`nodes[]` sections all matched the case's own expected values
exactly, field-for-field. Zero console errors, zero failed (≥400) network requests, across the
entire session.

The CHAT HISTORY value-type nuance documented in Axis 2 (empty-list vs literal-string YAML
serialization) is NOT a product defect — it is correct, unsurprising YAML behavior (an unquoted
string that happens to be valid list syntax parses as a list) and is handled by asserting the
live-contract value rather than the case's literal wording.

## Blocked Steps

None. All case steps were executed to completion against the live local environment (via a
dedicated throwaway pipeline, cleaned up afterward — see § Cleanup).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). No
  `add-data-testid` work is required — every element this case touches already has a testid from
  prior cases (ELITEA-2004/2026/2042).
- New test function goes in the SAME file as ELITEA-2004's/ELITEA-2040's tests
  (`test_pipeline_llm_node_system_task_chat_history_config.py`) — e.g.
  `test_llm_node_config_verified_via_yaml` — reusing the same `pipeline_id` fixture; does not
  modify either existing test's body or assertions.
- Parse with `import yaml; parsed = yaml.safe_load(pipeline_page.get_yaml_content())` — the exact
  pattern already proven by `test_pipeline_state_panel_default_and_custom_variables.py`
  (ELITEA-2042). Find the target node via
  `next(n for n in parsed["nodes"] if n["id"] == node_id)` rather than assuming index `0` (the
  case only asserts "the nodes array contains the LLM node with…", not its position).
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}` response
  (`201`) before switching to Yaml view (same as ELITEA-2004's `save_and_wait_for_update`).
- Suggested pytest markers: `@pytest.mark.p1` (case priority `high`), `@pytest.mark.pipelines`,
  `@pytest.mark.regression` (matches ELITEA-2004/ELITEA-2040's markers, same file).
