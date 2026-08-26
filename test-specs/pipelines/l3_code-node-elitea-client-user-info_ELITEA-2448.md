# Test Case: Code Node — elitea_client Access

## Metadata
- **TMS ID**: ELITEA-2448
- **Linked Story**: none
- **Priority**: l3 (medium, as authored in the source TMS case — matches sibling
  ELITEA-2446/ELITEA-2447's own AFS mapping)
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
  reason ELITEA-2446/ELITEA-2447 already established
  (`PipelineAPI.create_pipeline()` with a hand-built YAML `instructions` string;
  `create_pipeline_with_nodes()` has no `state:` support). This case needs only
  ONE custom state variable (`user_info`, type `JSON`) and a single Code node as
  the entry point — the simplest topology in this Code-node family, so the
  build-method gotcha (disconnected `-> END` edges, `#1384`) that forced
  ELITEA-2446/2447 into a 2-node fixture doesn't even apply here, but the raw-YAML
  build is kept for consistency with the sibling fixtures and because
  `create_pipeline_with_nodes()` still can't declare the custom `state:` block.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh pipeline built from raw YAML `instructions`, topology `Code 1 (entry) -> END`:
  ```yaml
  entry_point: Code 1
  state:
    user_info:
      type: JSON
  nodes:
    - id: Code 1
      type: code
      code:
        type: fixed
        value: |
          user_info = elitea_client.get_user_data()
          user_info
      input: []
      output: [user_info]
      structured_output: true
      transition: END
  ```
  **CONFIRMED LIVE (4-turn probe, pipeline id `8820`, project 399 "Private"): the
  case's own literal step-2/3 script — `user_info = elitea_client.get_user_data()`
  followed by a bare `user_info` name reference as the LAST statement — works
  exactly as written.** This is a different shape from ELITEA-2446/2447's
  discovery (a plain ASSIGNMENT as the last statement silently drops the state
  update): here the last statement is a bare *expression* (a name reference to a
  dict-valued variable), not an assignment, and the runtime accepts it the same
  way it accepts a bare dict-literal — both are non-assignment expression
  statements. No CLARIFICATION needed for this case; the case text is
  live-correct.
  - `type: JSON` (backend/YAML state-var type, `.claude/skills/elitea-pipeline/
    references/yaml-schema.md:52`) is a DIFFERENT spelling from the STATE panel
    UI's internal type key for the same concept (`dict`, displayed as "Json" —
    `l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md`'s
    Concrete Handles table). Confirmed live: the API accepts `type: JSON` verbatim
    (echoed back unchanged by `GET .../application/prompt_lib/{project}/{id}`),
    and the STATE panel correctly lists the `user_info` row by name. This AFS
    only asserts the row's NAME (matching ELITEA-2446's own String-type
    assertion depth), not its type-icon rendering — a dedicated type-icon
    assertion for the JSON/dict type is out of scope for this case's own text
    and belongs to ELITEA-2042's existing type-selector coverage if ever needed.
- Chat message sent to trigger execution: any short prompt (this session used
  `"hello"`) — content is irrelevant; the Code node takes no chat input (`input: []`).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live-exploration browser
  was on project "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with a Code node (entry point, single node, `Code 1 -> END`).
   - **Verify**: canvas renders one `code`-type node; `wait_for_node_on_canvas("code")`
     returns an id (`"Code 1"`).
2. In Code node script, use `elitea_client` to read user information:
   `user_info = elitea_client.get_user_data()` then a bare `user_info` reference
   as the final statement.
   - **Verify**: `get_code_node_value()` reflects the two-line script exactly;
     `"elitea_client.get_user_data()"` is present verbatim.
3. Set Output to the `user_info` state variable and enable structured output.
   - **Verify**: `get_code_node_output_value() == "user_info"`;
     `code_node_structured_output_toggle.is_checked() == True`.
4. Execute the pipeline (send any chat message in the embedded chat).
   - **Verify**: run completes (`get_run_details_status() == "Completed"`).
5. Verify Code node executes without errors in Run Details.
   - **Verify**: `select_run_details_timeline_step(0, ...)` (index 0 — the ONLY
     timeline entry, this is a single-node pipeline) then
     `get_run_details_timeline_step_status(0) == "completed"`; the selected
     step's label contains `"pyodide"` (the Python-sandbox executor's name — SAME
     Code-node timeline-label convention ELITEA-2446 already established,
     `EliteaAI/elitea-testing-public#1385`, NOT the space-stripped-id convention).
6. Verify Code node output state variable contains the user information.
   - **Verify**: `expand_run_details_state_row("user_info", ...)` then
     `get_run_details_state_after_value("user_info")` — CONFIRMED LIVE this
     session, the After value is the full JSON-serialized user object:
     `{"api_url":"...","email":"testbot@elitea.ai","id":659,"name":"Test Bot",
     "personal_project_id":399,...}`. Assert the parsed JSON contains non-empty
     `email` and `name` keys (the case's own "contains the user information"
     wording — don't pin exact values, since the test-bot's own account fields
     could legitimately change; assert structure + presence, not a literal string).

## Expected Results
- The Code node correctly calls `elitea_client.get_user_data()` and writes the
  full user-data dict into the `user_info` state variable via a bare name
  reference as the script's final statement (no dict-literal rewrap needed).
- Run Details shows ONE timeline step (`Code 1`, labelled `"pyodide"`), completed,
  with `user_info`'s After value containing real account fields (`email`, `name`,
  `id`, `personal_project_id`, etc.) — confirming `elitea_client` resolves to the
  currently-authenticated test user, not a stub/empty object.
- No console errors (excluding the known `#1267` Stepper prop-leak, confirmed to
  recur identically here — same `RunStateDialog.jsx` panel every Run-Details-
  opening case in this suite hits).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create a pipeline with a Code node | node exists on canvas | step 1 | step 1: `wait_for_node_on_canvas("code")` | asserted |
| 2 Code node script uses `elitea_client.get_user_data()` | script accepted | step 2 | step 2: `get_code_node_value()` | asserted — **live-correct as literally written, no CLARIFICATION needed (see Test Data note — distinct from ELITEA-2446's plain-assignment CLARIFICATION, since this script's last statement is a bare expression, not an assignment)** |
| 3 Set Output to a state variable and enable structured output | Output=`user_info`, toggle checked | step 3 | step 3: `get_code_node_output_value()` / `.is_checked()` | asserted |
| 4 Execute the pipeline | completes without error | step 4 | step 4: `get_run_details_status()` | asserted |
| 5 Verify Code node executes without errors in Run Details | timeline step `completed` | step 5 | step 5: `get_run_details_timeline_step_status(0)` | asserted |
| 6 Verify Code node output state variable contains the user information | After value = user dict | step 6 | step 6: `get_run_details_state_after_value("user_info")` parsed as JSON, asserted for `email`/`name` presence | asserted |
| Expected Final State / Pass-Fail criteria | all steps complete, no errors | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 5's label assertion (`"pyodide"` substring, not `"Code1"`) — *added: same
  confirmed-live Code-node timeline-label convention ELITEA-2446 already
  established; omitting it would leave the step's own verification incomplete
  (index-only, no label check).*
- Step 6's assertion parses the After value as JSON and checks key PRESENCE
  (`email`, `name`) rather than pinning exact field values — *added: the test-bot
  account's own fields (`last_login`, etc.) are time-varying and its non-identity
  fields could change between environments; the case's own text ("contains the
  user information") is a presence claim, not an exact-value claim.*
- Console-error assertion excluding the known `#1267` signature — *added: same
  reasoning as every other Run-Details-opening case in this suite
  (ELITEA-2446/2447/2450/2451/2452/2453) — confirmed live this session to recur
  identically (same `RunStateDialog.jsx` stack trace).*

## Cleanup
1. This session created one throwaway pipeline during live exploration
   (`autotest_2448_probe_test_scratch_probe`, id `8820`, project 399 "Private") to
   confirm `elitea_client.get_user_data()`'s live behavior (1 probe run, via a
   scratch pytest test using the project's own `pipeline_api`/`page` fixtures —
   deleted in the probe's own `finally:` block via
   `PipelineAPI.delete_pipeline()`, confirmed `DELETE .../application/prompt_lib/
   399/8820` succeeded). No residue left behind; the scratch test file itself was
   removed (never committed).
2. Implementer teardown: new fixture (see Automation Hints) built via
   `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)` in
   teardown — same pattern as `pipeline_llm_reads_state_via_code`/
   `pipeline_code_node_multi_var_dict_return`.

## Concrete Handles (discovered during exploration)

**Zero new testids needed — every element this case touches already has one from
ELITEA-2009 (Code node config) and ELITEA-2450/2451/2452 (Run Details panel) —
same zero-new-testid finding as ELITEA-2446/2447, which touch the identical Code
node config controls and Run Details panel.**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node Output select, Value field, Structured output toggle | `pipeline-code-node-output-select-combobox` / `pipeline-code-node-value` / `pipeline-code-node-structured-output-toggle` | **on-`automation/testids` ✓** — added by ELITEA-2009, reused unmodified via `PipelineDetailPage.get_code_node_output_value()` / `get_code_node_value()` / `code_node_structured_output_toggle`. Confirmed live this session (1 probe run). | none needed |
| Run Details panel, timeline step selector (index 0), state row/value boxes | `pipeline-run-details-panel`, `pipeline-run-details-timeline-step-0`, `pipeline-run-details-state-row-user_info`, `pipeline-run-details-state-value-after-user_info` | **on-`automation/testids` ✓** — added by ELITEA-2450/2451/2452, reused unmodified via `PipelineDetailPage.open_run_details_panel()` / `select_run_details_timeline_step(0)` / `expand_run_details_state_row()` / `get_run_details_state_after_value()`. Confirmed live: `user_info`'s row correctly renders and expands with the full user-data JSON. | none needed |
| STATE panel toggle / variable-name text | `pipeline-state-drawer-toggle-button` / (row name text via `get_state_variable_name_text`) | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing (ELITEA-2042), reused unmodified. Confirmed live: `user_info` row name renders correctly for the JSON-typed state variable. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation.
- Pipeline execution and all Run Details data (timeline, per-step state) arrive
  entirely over Socket.IO, same as every other Run Details case in this suite
  (ELITEA-2446/2450/2451/2452/2453) — no dedicated REST endpoint for
  timeline/state observed for this pipeline either.
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` —
  fires on pipeline deletion; confirmed live (probe cleanup, this session).
- `elitea_client.get_user_data()` itself is a Code-node-internal (sandbox-side)
  call — it does NOT appear as a separate browser-visible network request; its
  result only becomes observable via the Run Details state panel after the run
  completes, exactly as for `elitea_state.get(...)` in ELITEA-2446.

## Known Defects Found During Exploration

**No product defect found. No case-text CLARIFICATION needed** — unlike
ELITEA-2446/2447, this case's own literal script text (a bare name-reference last
statement, not an assignment) is confirmed live to work exactly as written; see
the Test Data note for why this differs from ELITEA-2446/2447's plain-assignment
CLARIFICATION.

`elitea_client.get_user_data()` (the case's literal spelling) IS confirmed valid —
NOT a case-text drift. `.claude/skills/elitea-pipeline/references/workflows.md`
§ "Code Node Special Capabilities" documents `alita_client.get_user_data()` (the
`alita_`-prefixed alias) under **User:**; this session's live exploration used the
case's own `elitea_client.get_user_data()` spelling and it correctly resolved and
returned the authenticated test user's full data dict (`email`, `name`, `id`,
`personal_project_id`, `api_url`, `default_context_management`,
`default_summarization`, `personalization`, `suspended`, `last_login`) — both
spellings are aliases of the same runtime-injected client, matching
`.claude/skills/elitea-pipeline/SKILL.md`'s own note ("`alita_client` is an alias
for some operations... prefer `elitea_*`") and the bundled
`examples/getuserdetails.yaml` reference pipeline (which uses the `elitea_client`
spelling identically).

## Blocked Steps

None. All 6 case steps were exercised live this session (1 probe run, pipeline id
`8820`) — the script worked on the first attempt with no iteration needed, unlike
ELITEA-2446/2447's multi-probe discovery process.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new
  testids needed (see Concrete Handles).
- **New fixture needed**: no existing fixture builds a single-Code-node pipeline
  calling `elitea_client.get_user_data()`. Recommend
  `pipeline_code_node_elitea_client_user_info` (or similar) in
  `automation/fixtures/data_fixtures.py`, built via `PipelineAPI.create_pipeline()`
  with the raw YAML `instructions` string in this AFS's § Test Data — mirrors
  `pipeline_llm_reads_state_via_code`'s create/yield/delete pattern (NOT
  `create_pipeline_with_nodes()`, which has no `state:` support). This is the
  SIMPLEST fixture in the Code-node family so far — one node, no chained
  transition to get wrong, no LLM-nondeterminism to route around.
- **Code node script convention for THIS case**: a bare NAME-reference expression
  (`user_info`) as the last statement works identically to a bare dict-LITERAL
  expression (ELITEA-2446/2447's convention) — both are non-assignment expression
  statements, and the runtime routes either into the declared `output:` variable
  when `structured_output: true`. Do NOT rewrap this case's script into a dict
  literal "to be safe" — the case's own two-line form (`user_info = ...` then
  bare `user_info`) is the live-correct, already-confirmed shape; keep it as
  specified.
- **Parse the After value as JSON** (`json.loads(get_run_details_state_after_value(...))`)
  before asserting on individual keys — the panel renders it as a JSON-serialized
  string, not a pretty-printed dict repr (confirmed live: the raw string starts
  with `{"api_url":...`).
- **Reuse ELITEA-2452's Run Details Before/After methods unmodified**:
  `open_run_details_panel()`, `select_run_details_timeline_step(0)` (index 0 —
  the ONLY timeline entry for this single-node pipeline, unlike ELITEA-2446/2447's
  2-node pipelines which use index 1), `get_run_details_selected_timeline_step_id()`,
  `expand_run_details_state_row()`, `get_run_details_state_after_value()`,
  `get_run_details_timeline_step_status(0)`.
- Wait strategy: `wait_for_embedded_chat_response()` after sending the chat
  message (never a fixed sleep), then `expect(pipeline_page.run_node_label).to_be_visible()`
  before opening Run Details — same as every other pipeline-execution case in
  this suite.
- `_surface.md` NOT updated with a new section this session — the confirmed
  behavior (bare name-reference last statement works; `elitea_client`/
  `alita_client` are aliases) is narrow enough to live in this AFS alone; nothing
  here contradicts or extends the existing Code-node-execution gotchas already
  documented against ELITEA-2446/2447 (which this AFS cites directly instead of
  duplicating).
