# Test Case: Run Details — Multiple State Variables of Different Types

## Metadata
- **TMS ID**: ELITEA-2453
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case; project convention
  maps medium → `@pytest.mark.p2`, matching sibling ELITEA-2450/ELITEA-2452's own AFS)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-06
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with 4 CUSTOM state variables of the 4 distinct types the STATE
  panel's type-selector offers (`String`/`Number`/`List`/`Json` — internal values
  `str`/`number`/`list`/`dict`, per `l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md`),
  plus the 2 built-in `input`/`messages` variables, and a single LLM node with
  `structured_output: true` whose `output` mapping writes to all 4 custom variables.
  Confirmed live this session via `PipelineAPI.create_pipeline()` (generic, accepts a
  raw `instructions` YAML string — **no new API method needed**, unlike
  `create_pipeline_with_nodes()` which has no `state:` support):
  ```yaml
  entry_point: LLM 1
  state:
    custom_text:
      type: str
    custom_num:
      type: number
    custom_list:
      type: list
    custom_json:
      type: dict
  nodes:
    - id: LLM 1
      type: llm
      input: []
      input_mapping:
        chat_history:
          type: fixed
          value: []
        system:
          type: fixed
          value: 'You populate structured state variables. Always return values for
            custom_text (a short string), custom_num (a number), custom_list (a list
            of 3 short strings), and custom_json (a small JSON object with 2 keys).'
        task:
          type: fstring
          value: '{input}'
      output: [custom_text, custom_num, custom_list, custom_json]
      structured_output: true
      transition: END
  ```
  **CRITICAL — do NOT include `messages` in this node's `output` list.** See Known
  Defects: combining `messages` with `dict`/`list`-typed custom variables in a
  `structured_output: true` node's `output` mapping is a CONFIRMED product defect
  (`EliteaAI/elitea-testing-public#1274`) that makes the run fail with a raw backend
  error string instead of populating state. This AFS's fixture deliberately excludes
  `messages` from `output` — confirmed live this session to execute cleanly.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- The pipeline YAML above, created via `PipelineAPI.create_pipeline(name, description,
  instructions=<yaml above>)` — confirmed live (pipeline id 7746 this session, deleted
  at session end). Recommend a new fixture (e.g. `pipeline_with_typed_state_vars_id`)
  mirroring `pipeline_with_two_llm_nodes_id`'s create/yield/delete pattern
  (`l3_run-details-state-before-after-per-node_ELITEA-2452.md`'s Automation Hints).
- Chat message sent: any short instruction naming all 4 custom variables (this session
  used `"Please populate the state variables now."`, content is irrelevant beyond
  "the LLM populates all 4 typed variables" — the system prompt above already spells
  out what's expected of each).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project was
  "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with 4+ state variables of different types: `custom_text`
   (String), `custom_num` (Number), `custom_list` (List), `custom_json` (Json) —
   plus the built-in `input`/`messages`.
   **Expected**: pipeline created successfully with all 6 state variables present in
   its YAML `state:` section. Confirmed live via the fixture pipeline above (id 7746);
   the type-selection UI mechanics themselves (add-variable "+" button, name-input,
   type dropdown with exactly String/Number/List/Json options) are the SAME already
   automated by ELITEA-2042 — this case doesn't re-verify that UI flow, it consumes
   its outcome (a pipeline with typed custom state) as a precondition, matching how
   the TMS case's step 1 folds "create the variables" and "configure the node" into
   one setup phase before the observable Run Details assertions begin.
2. Configure an LLM node that populates all custom variables with structured output
   enabled.
   **Expected**: node's `output` multi-select lists all 4 custom variables (plus
   `input`/`messages`, not selected — see Known Defects), `structured_output: true`
   set. Confirmed live via DOM read of the LLM node's Output select
   (`pipeline-llm-node-output-select`): exactly `custom_text, custom_num, custom_list,
   custom_json` shown as selected chips, `pipeline-llm-node-structured-output-toggle`
   checked.
3. Execute the pipeline (send a chat message).
   **Expected**: run completes without error; a `"Run 1 details"` indicator appears
   above the Flow canvas (`RunStateNode`, testid `pipeline-run-node-label`, reused
   unmodified from ELITEA-2450), status `"Completed"`. Confirmed live: chat responded
   "State variables populated as requested.", zero error text in the AI response
   bubble (contrast with the excluded-`messages` variant, which fails — see Known
   Defects).
4. Open Run Details, select a node step.
   **Expected**: panel opens (`role="dialog"`, `pipeline-run-details-panel`).
   Confirmed live: panel opened directly via `pipeline-run-node-label` click
   (`open_run_details_panel()`, reused from ELITEA-2450/2452), `"Timeline step:"`
   label reads `LLM1` immediately on open (no explicit step-click required — matches
   ELITEA-2452's confirmed "default-selected step on open is the LAST step" behavior
   for a `Completed` run). **New observation this session**: the timeline shows TWO
   entries both labeled `LLM1` (e.g. `21:39:48` and `21:39:50`) for this single-node
   structured-output pipeline, not one — informational only, not asserted by this
   case (the case's own step 4 only requires "select a node step", which the
   default-selected LAST entry already satisfies); flagged here so the implementer
   doesn't treat 2 timeline entries as a bug or an unexpected pipeline topology.
5. Verify all state variables appear in STATES section (displayed uppercase).
   **Expected — confirmed live with a rendering-mechanism clarification**: all 4
   custom rows (`custom_text`, `custom_num`, `custom_list`, `custom_json`) are present
   as accordion rows (`pipeline-run-details-state-row-{variable}`, reused from
   ELITEA-2452 — dynamic testid, no new plumbing). **The row's DOM text content is
   the RAW lowercase variable name** (`el.textContent === "custom_json"`, confirmed
   via `browser_evaluate`); the visible "uppercase" the case describes is a CSS
   `text-transform: uppercase` applied by `BasicAccordion.jsx`'s `uppercase` prop
   (default `true`, unmodified by `RunStateDialog.jsx`), confirmed via
   `getComputedStyle(el).textTransform === "uppercase"`. **Automation implication**:
   assert presence via the testid/raw text (`"custom_json"`, lowercase), and if the
   case's "uppercase" wording is asserted literally, assert the CSS property
   (`to_have_css("text-transform", "uppercase")`), never `to_have_text("CUSTOM_JSON")`
   — that would fail against the real (lowercase) DOM text despite matching what a
   human sees. Not a defect — documenting the mechanism so the implementer doesn't
   misread a passing assertion as green when it's actually asserting the wrong layer.
6. Expand each variable — verify each is individually expandable (see steps 7-12 for
   the ones covering DISTINCT observable types).
   **Expected — confirmed live**: `custom_text` is auto-expanded on open (accordion's
   `defaultExpanded={!index}`, list index 0 — same mechanism ELITEA-2452 documented);
   `custom_num`/`custom_list`/`custom_json` each require an explicit click on their
   own header, and each expands/collapses independently of the others (confirmed:
   after expanding all 4 in sequence, all 4 remained visibly expanded simultaneously —
   this is a non-exclusive accordion, not a single-open one).
7. INPUT: shows string value in Before/After.
   **Not independently re-verified this session** — `input`'s Before/After rendering
   as a plain string was already confirmed live and automated by
   `l3_run-details-state-before-after-per-node_ELITEA-2452.md` (steps 6-7, same
   `StateItemView` component, same rendering path for any `str`-typed variable). This
   AFS's own step 9 covers the SAME string-type rendering via `custom_text` instead
   (a custom variable, matching this case's actual novel scope — distinguishing types
   — rather than re-proving `input` specifically, which 2452 already owns).
8. MESSAGES: shows list representation in Before/After.
   **Not independently re-verified this session — see Known Defects.** The case's
   own step 2 requires an LLM node that "populates all custom variables with
   structured output enabled"; combining `messages` in that SAME node's `output`
   under `structured_output: true` is the confirmed-broken combination
   (`EliteaAI/elitea-testing-public#1274`). `messages`' list-of-LangChain-message-object
   rendering (`StateItemView`, same component) is covered by
   `l3_run-details-state-before-after-per-node_ELITEA-2452.md`, a 2-node pipeline
   where `messages` is populated via a plain `output: [messages]` mapping WITHOUT
   `structured_output`. **Amended (fix round, 2026-08-06):** the original citation
   to that AFS's "steps 6/8" was inaccurate — those steps only assert box
   visibility and Before≠After/non-emptiness, never a list/array SHAPE check, so
   the "list representation" observable this case's own step 8 names was not
   actually asserted anywhere in the suite. Closed by adding a real shape
   assertion to that spec's Step 8 block (`json.loads(messages_after)` +
   `isinstance(..., list)` + non-empty), confirmed live: `messages`' After value
   is `["content='...' ...", "content='...' ..."]` — a genuine JSON array of
   stringified LangChain message objects. See
   `automation/tests/ui/pipelines/test_pipeline_run_details_state_before_after.py`
   Step 8 (the new shape-check block, immediately after the existing
   Before≠After assertion). This AFS's own step 11 additionally covers the
   list-type observable this case's OWN scope needs distinguished (String vs
   Number vs List vs Json) via `custom_list` — a genuine `list` type, distinct
   from `messages`' LangChain-object-array special case.
9. CUSTOM_TEXT: shows string values.
   **Expected — confirmed live, exact match**: `custom_text` row's After value
   (`pipeline-run-details-state-value-after-custom_text`, reused testid mechanism
   from ELITEA-2452) reads `"state initialized"` — a JSON-quoted string
   (`JSON.stringify` renders `str` values wrapped in `"..."`), confirmed via
   `browser_snapshot` DOM read.
10. CUSTOM_NUM: shows numeric values.
    **Expected — confirmed live, exact match**: `custom_num` row's After value reads
    `42` — **no surrounding quotes** (`JSON.stringify(42)` → `"42"` as a bare numeral,
    contrasted directly against `custom_text`'s quoted `"state initialized"` in the
    SAME panel) — confirms the panel renders `number`-typed values distinctly from
    `str`-typed ones via `JSON.stringify`'s own type-preserving behavior, not a
    custom per-type renderer.
11. CUSTOM_LIST: shows list/array representation.
    **Expected — confirmed live, exact match**: `custom_list` row's After value reads
    `["alpha","beta","gamma"]` — valid JSON array syntax, confirming `list`-typed
    values render via `JSON.stringify` array formatting (brackets, comma-separated,
    quoted string elements).
12. CUSTOM_JSON: shows JSON object representation.
    **Expected — confirmed live, exact match**: `custom_json` row's After value reads
    `{"status":"ok","version":1}` — valid JSON object syntax (curly braces,
    `"key":value` pairs, mixed string/number field types within the SAME object),
    confirming `dict`-typed (`Json` display label) values render as a genuine JSON
    object, not a string-escaped blob.
13. Verify each variable is individually expandable.
    **Expected — confirmed live**: same observation as step 6 — clicking each of the
    4 rows' own accordion header toggled that row independently; no row's expand/
    collapse affected any other row's state.

## Expected Final State
A pipeline with 4 custom state variables of 4 distinct types (String/Number/List/Json)
plus the 2 built-in variables, executed via an LLM node with `structured_output: true`
writing to all 4 custom variables (excluding `messages` — see Known Defects), shows
all 4 custom-variable rows in the Run Details STATES section; each is individually
expandable; each renders its After value per its OWN type's `JSON.stringify`
representation (quoted string / bare number / bracketed array / braced object).

## Coverage Map

### Axis 1 — Case elements → live behavior

| Case element | Expected result (case text) | Covered by (this AFS) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create pipeline with 4+ typed state vars | Operation completes; state updates, confirmation shown | Precondition + Step 1 (fixture pipeline) | Step 1 | covered — type-CREATION UI mechanics themselves already owned by ELITEA-2042 (not re-verified here; this case consumes the outcome) |
| Step 2: LLM node populates all custom variables with structured output enabled | Action completes without error, expected UI state | Step 2 | Step 2 | covered |
| Step 3: Execute the pipeline | Action completes without error | Step 3 | Step 3 | covered |
| Step 4: Open Run Details, select a node step | Target page/section loads | Step 4 | Step 4 | covered — **NOTE**: 2 timeline entries appear for this single-node pipeline (informational, not a defect against this case's own assertions) |
| Step 5: All state variables in STATES section, uppercase | Condition holds | Step 5 | Step 5 | covered — **CLARIFICATION**: "uppercase" is a CSS `text-transform`, not the DOM text content (which is lowercase); assert accordingly |
| Step 6: Expand each variable | Action completes | Steps 6+13 | Steps 6, 13 | covered |
| Step 7: INPUT shows string value | Field accepts input, displays value | N/A this session — see step 7 note | `l3_run-details-state-before-after-per-node_ELITEA-2452.md` steps 6-7 | already-covered-elsewhere (str-type rendering via `input`, not re-verified — this AFS proves the SAME rendering mechanism via `custom_text`, step 9) |
| Step 8: MESSAGES shows list representation | Action completes | N/A this session — see Known Defects | `test_pipeline_run_details_state_before_after.py` Step 8 (`isinstance(json.loads(messages_after), list)` shape assertion, added fix round 2026-08-06) | already-covered-elsewhere (list-of-message-object rendering via `messages` in a NON-structured-output node, now with a real list/array SHAPE assertion, not just visibility/diff; this case's own structured-output + `messages` combination is a CONFIRMED DEFECT, `#1274` — routed around, not asserted as working) |
| Step 9: CUSTOM_TEXT shows string values | Action completes | Step 9 | Step 9 | covered |
| Step 10: CUSTOM_NUM shows numeric values | Action completes | Step 10 | Step 10 | covered |
| Step 11: CUSTOM_LIST shows list/array representation | Action completes | Step 11 | Step 11 | covered |
| Step 12: CUSTOM_JSON shows JSON object representation | Action completes | Step 12 | Step 12 | covered |
| Step 13: Verify each variable individually expandable | Condition holds | Steps 6+13 | Step 13 | covered |

### Axis 2 — Assertions beyond the case

| Extra observable | Grounded reason |
|---|---|
| **KNOWN DEFECT (filed `EliteaAI/elitea-testing-public#1274`)**: combining `messages` in the SAME `output` list as `dict`/`list`-typed custom variables under `structured_output: true` makes the run fail with a raw backend error (`sequence item 0: expected str instance, dict found`) surfaced directly in the chat UI, instead of populating state. Isolated via a live A/B (identical pipeline, `messages` present vs absent in `output`). | `.agents/testing.md` "no defect masking" — the defect is real, filed, and this AFS's fixture routes around it (excludes `messages` from the structured-output node's `output`) rather than asserting broken behavior as correct. |
| Zero unexpected console errors during navigate→execute→open-panel→expand-rows, EXCEPT the known `EliteaAI/elitea-testing-public#1267` Stepper prop-leak warning (same signature as ELITEA-2450/2452, reproduced again this session) | `.agents/testing.md` "check console even when UI looks fine" discipline; scope the assertion to exclude this one known, filed, deterministic warning signature. |
| `custom_text`'s After value is `"state initialized"` even though the system prompt asked for "a short string" with no specific content — content is LLM-nondeterministic | Automation should assert PRESENCE + JSON-string-shape (`text.startswith('"') and text.endswith('"')`) for `custom_text`/After, not an exact literal string — the exact wording is not a stable contract (same caution as ELITEA-2452's `messages` content assertions, which check shape/non-emptiness, not literal LLM wording). |

## Concrete Handles (discovered during exploration — ALL PRE-EXISTING, zero new testids needed)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| STATE panel add-variable / type-select mechanics | `pipeline-state-add-variable-button`, `pipeline-state-add-variable-name-input`, `PIPELINE_STATE_TYPE_SELECT`/`STATE_TYPE_OPTION` templates | **on-`automation/testids` only**, reused unmodified from `l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md` — already wired as `PipelineDetailPage.add_state_variable()` / `.select_state_variable_type()`. This case doesn't re-verify the UI flow (see Coverage Map step 1); if the implementer chooses UI-driven setup over the API fixture, these are the handles. | none needed |
| LLM node Output multi-select | `[data-testid="pipeline-llm-node-output-select"]` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.llm_node_output_select` / `.select_llm_node_output_variable(name)` (called once per variable to add). Confirmed live: selecting `custom_text`/`custom_num`/`custom_list`/`custom_json` produced exactly those 4 chips. | none needed |
| LLM node Structured output toggle | `[data-testid="pipeline-llm-node-structured-output-toggle"]` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.llm_node_structured_output_toggle`. Confirmed live: `checked` after click, node YAML gains `structured_output: true`. | none needed |
| Run node clickable label (opens panel) | `[data-testid="pipeline-run-node-label"]` | **on-`automation/testids` only**, reused unmodified from ELITEA-2450, already wired as `PipelineDetailPage.run_node_label` / `.open_run_details_panel()`. | none needed |
| Run Details panel root | `[data-testid="pipeline-run-details-panel"]` | **on-`automation/testids` only**, reused unmodified from ELITEA-2450. | none needed |
| Timeline selected-step label | Read via `PipelineDetailPage.get_run_details_selected_timeline_step_id()` | **on-`automation/testids` only**, reused unmodified from ELITEA-2450/2452. | none needed |
| State variable accordion row (per variable) | `[data-testid="pipeline-run-details-state-row-{variable}"]` | **on-`automation/testids` only**, reused unmodified from ELITEA-2452 — already wired as `PipelineDetailPage.get_run_details_state_row_locator(variable)` / `.expand_run_details_state_row(variable)`. Confirmed live for all 4 custom variable names (dynamic template, no new plumbing — this case is exactly the "custom variable name" case the template was designed for). | none needed |
| Before/After value box (per variable) | `[data-testid="pipeline-run-details-state-value-{before\|after}-{variable}"]` | **on-`automation/testids` only**, reused unmodified from ELITEA-2452 — `PipelineDetailPage.get_run_details_state_value_locator(variable, direction)` / `.get_run_details_state_before_value(variable)` / `.get_run_details_state_after_value(variable)`. Confirmed live for all 4 custom variables — this is the exact mechanism that renders the 4 distinct type representations (string-quoted / bare-numeric / bracketed-array / braced-object). | none needed |
| Fullscreen value modal (root/header/close/content) | `pipeline-run-details-value-modal*` | **on-`automation/testids` only**, reused unmodified from ELITEA-2452. Not required by this case's own steps (no case step asks for the fullscreen view of a typed value), but available if the implementer wants an extra Axis-2 smoke per type — optional, not mandated by this AFS. | none needed |

## Network Behavior
Same as ELITEA-2450/2452: pipeline execution and all Run Details data (timeline,
per-step state snapshots) arrive entirely over Socket.IO — no dedicated REST endpoint
for timeline/state. Not re-verified via `browser_network_requests` this session
(ELITEA-2452 already established this for the SAME panel/mechanism); no reason to
expect it differs for structured-output-populated variables, since the panel reads
already-materialized `data.timeline[step].state[variable]` regardless of HOW that
value was produced upstream.

## Known Defects Found During Exploration

**One CONFIRMED product defect, filed**: `EliteaAI/elitea-testing-public#1274` — an
LLM pipeline node with `structured_output: true` fails at execution with a raw
backend error (`Error: sequence item 0: expected str instance, dict found`) surfaced
directly in the chat response, whenever its `output` mapping combines the built-in
`messages` variable together with `list`/`dict`-typed custom state variables.
Isolated via a live A/B this session (pipeline 7745: `output` included `messages` →
failed; pipeline 7746: identical setup minus `messages` in `output` → succeeded
cleanly, all 4 custom variables populated and correctly typed in Run Details).
**Automation impact**: this AFS's fixture (§ Preconditions) deliberately excludes
`messages` from the structured-output LLM node's `output` list — the case's own
steps (5, 9-13) only require the 4 CUSTOM variables to render correctly, which this
fixture satisfies without tripping the defect. Do not "fix" this by adding `messages`
back to `output` and asserting the (broken) resulting behavior as correct, and do not
skip/weaken step 8 (MESSAGES list representation) — it remains satisfied via the
existing coverage in `l3_run-details-state-before-after-per-node_ELITEA-2452.md`
(§ Coverage Map disposition above).

**One informational observation, NOT filed as its own ticket** (doesn't contradict
any case assertion): the timeline shows 2 entries both labeled `LLM1` for this
single-node structured-output pipeline, rather than the 1 entry a single execution
of a single node would suggest. Not investigated further this session (not required
by any case step); flagged in step 4's note and in Automation Hints for whoever next
touches structured-output + Run Details timeline semantics.

## Blocked Steps

None. All 13 case steps were satisfied — either newly executed this session (steps
1-6, 9-13) or already covered by a merged sibling AFS for the SAME underlying
component/mechanism (steps 7-8, explicitly cited above) with this case's fixture
deliberately avoiding the one combination that's a confirmed product defect
(step 8's literal "MESSAGES + structured output" combination).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Zero new testids needed** — every handle this case touches (STATE panel
  add/type-select, LLM node Output-select/structured-output-toggle, Run Details
  panel/timeline/state-row/value-box) already exists on `automation/testids`,
  wired as `PipelineDetailPage` methods, from ELITEA-2042/2450/2452. No
  `add-data-testid` pass required before implementation.
- **New fixture needed**: no existing fixture builds a pipeline with a `state:`
  block of custom typed variables. Recommend `pipeline_with_typed_state_vars_id`
  (or similar) in `automation/fixtures/data_fixtures.py`, built via
  `PipelineAPI.create_pipeline(name, description, instructions=<yaml>)` — the
  GENERIC `create_pipeline()` already accepts a raw `instructions` string (unlike
  `create_pipeline_with_nodes()`, which only supports `entry_point`+`nodes`, no
  `state:`), confirmed live this session. Mirrors `pipeline_with_two_llm_nodes_id`'s
  create/yield/delete pattern (ELITEA-2452's Automation Hints).
- **Do NOT include `messages` in the structured-output LLM node's `output` list** —
  confirmed live product defect `#1274` when combined with `list`/`dict`-typed
  custom variables. Step 8 (MESSAGES list representation) is satisfied by
  ELITEA-2452's existing coverage instead (cite it in a code comment, don't
  re-implement).
- **Assert `custom_text`/After as a shape, not an exact string** — the LLM's
  actual text content is nondeterministic; assert JSON-string quoting
  (`value.startswith('"') and value.endswith('"')`) and non-emptiness, matching
  the caution already established in ELITEA-2452 for `messages` content.
- **Assert `custom_num`/`custom_list`/`custom_json`'s After values by parsing as
  JSON and checking `type()`** (`int`/`float`, `list`, `dict` respectively) rather
  than exact literal values — the LLM's specific number/list-length/JSON-keys are
  also not a stable contract, only "each renders as ITS type's JSON shape,
  distinct from the others" is.
- **"Displayed uppercase" (case step 5) is CSS `text-transform`, not DOM text** —
  see step 5's Coverage Map clarification. Assert via testid presence (raw
  lowercase name) or `to_have_css("text-transform", "uppercase")`; never
  `to_have_text("CUSTOM_JSON")`.
- **Wait discipline**: same as ELITEA-2450/2452 — `wait_for_embedded_chat_response()`
  for run completion, `expect(locator).to_be_visible()` after each accordion-expand
  click (client-side React re-render, not guaranteed synchronous with the click).
- Reuse `PipelineDetailPage.open_run_details_panel()`, `.expand_run_details_state_row()`,
  `.get_run_details_state_after_value()` unmodified from ELITEA-2452 — no new
  page-object methods needed either, only a new fixture.
- `_surface.md` updated this session — see the new "Run Details panel — Multiple
  typed custom state variables" section covering the `messages`+structured-output
  defect, the uppercase-via-CSS mechanism, and the duplicate-timeline-entry
  observation.
