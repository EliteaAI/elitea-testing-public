# Test Case: Pipeline — Input Mapping Types (Fixed, F-String, Variable)

## Metadata
- **TMS ID**: ELITEA-2040
- **Linked Story**: `EliteaAI/elitea-testing-public#477` (tracking issue)
- **Priority**: l2 (high, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-04
- **Status**: extend-existing

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_llm_node_system_task_chat_history_config.py`
  (TMS ELITEA-2004), page object `automation/pages/pipeline_detail_page.py:189-232`
  (LLM node section `LocatorDescriptor`s) and `:2312-2362` (`get_llm_node_section_type`,
  `select_llm_node_section_type`, `fill_llm_node_section_value`, `get_llm_node_section_value`).
- **Behavioural overlap**: ELITEA-2004's merged test already exercises the LLM node's Type
  dropdown (`pipeline-llm-node-{system,task,chat_history}-type-select`, all testid'd,
  `TYPE_OPTION_VALUE_BY_LABEL = {"Fixed": "fixed", "F-String": "fstring", "Variable": "variable"}`
  already includes `Variable`) and Value field (`pipeline-llm-node-{section}-value`), including
  switching TASK's Type from default `Fixed` → `F-String`, filling both Fixed and F-String Values,
  saving, and confirming Type + Value persist correctly through a full page reload — for **all
  three** LLM-node sections (SYSTEM/TASK/CHAT HISTORY). This is exactly the "locate a Type
  dropdown, set it, enter a Value, save, reload, verify persistence" mechanic ELITEA-2040 asks for.
- **The gap**: `Variable` is never selected anywhere in ELITEA-2004's test or in any other merged
  pipeline spec (confirmed via `grep -rn '"Variable"' automation/tests/ui/pipelines/` — zero
  matches). Live exploration this session (see below) confirms `Variable` is not just a third
  label in the same widget — selecting it swaps the SYSTEM section's Value field from a
  `<textarea>` to an entirely different MUI `Select` component whose options are the pipeline's
  state variables (`input`/`messages`, the same list `Input`/`Output` use), and that widget swap
  is completely unexercised. This is a genuinely new, previously-blind DOM shape and behaviour on
  the identical node/page-object/fixture ELITEA-2004 already builds — an **incremental addition**,
  not a near-rewrite: ELITEA-2004's own test body, assertions, and terminal (Fixed) persisted state
  for SYSTEM/TASK/CHAT HISTORY are untouched by this extension.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_llm_node_system_task_chat_history_config.py`), reusing the same `pipeline_id`
  fixture and `PipelineDetailPage` methods, that walks the SYSTEM section's Type through
  Fixed → F-String → Variable in one flow (matching the case's own step order) and asserts the
  Variable-mode Value-select behaviour + reload persistence. ELITEA-2004's existing test is not
  modified.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: Keycloak via `${TEST_USER}`).
- A project with Pipelines access exists (localhost dev project id `399`).
- No pre-existing LLM node or toolkit is required — starts from a bare empty pipeline, same as ELITEA-2004.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh empty pipeline (`autotest_<test_name>`), via `PipelineAPI.create_pipeline()` — identical
  pattern to ELITEA-2004's `pipeline_id` fixture (`automation/fixtures/data_fixtures.py:119`).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).
- SYSTEM section walk: Type=`Fixed`/Value=`Extract these four values from the given input`
  (case's own Test Data), then Type=`F-String`/Value=`input: {input}` (case's own Test Data),
  then Type=`Variable`/Value=`input` (the only pre-existing non-`input` state variable besides
  `messages` on a fresh pipeline is `messages`; `input` is chosen as the Variable reference since
  it's the pipeline's own entry-point variable — confirmed present in the Variable Value-select's
  option list this session).

## Test Steps

1. Create a pipeline via `PipelineAPI.create_pipeline()`, navigate to
   `${BASE_URL}/pipelines/all/{pipeline_id}?destTab=configuration&viewMode=owner`.
   - **Verify**: configuration panel + canvas load (reuse of ELITEA-2004's step 1 mechanics).
2. Add an LLM node via the canvas "+" menu (`pipeline-add-node-button` →
   `pipeline-add-node-menu-item-llm`, both testid'd — confirmed live this session, supersedes
   ELITEA-2004's older positional `button.MuiIconButton-colorPrimary` + `role=menuitem` locator).
   - **Verify**: LLM node appears (`.react-flow__node-llm`).
3. Open the SYSTEM section's Type select (`pipeline-llm-node-system-type-select`) and confirm
   the option list is **exactly** `Fixed`/`F-String`/`Variable` — read via
   `[data-testid^="select-option-"]` inside the open popover.
   - **Verify**: exactly 3 options, testids `select-option-fixed`/`select-option-fstring`/`select-option-variable`,
     labels `Fixed`/`F-String`/`Variable` — confirmed live this session, in that DOM order.
4. SYSTEM Type defaults to `Fixed` (no action needed) — fill the Value field
   (`pipeline-llm-node-system-value`, a `<textarea>` at this point) with
   `Extract these four values from the given input`.
   - **Verify**: `input_value()` reflects the typed text.
5. Switch SYSTEM's Type to `F-String` (select `select-option-fstring`) — confirmed live: the
   Fixed value is **preserved** across a Fixed↔F-String switch (see Coverage Map / source note),
   so clear and re-fill the Value field with `input: {input}`.
   - **Verify**: Type select shows `F-String`; Value `input_value()` is `input: {input}`.
6. Switch SYSTEM's Type to `Variable` (select `select-option-variable`).
   - **Verify**: the Type select shows `Variable`. The Value field's underlying DOM element
     **changes from a `<textarea>` to a MUI `Select` combobox** (`role="combobox"`,
     `id="simple-select-Value"`) — confirmed live this session via direct DOM inspection
     (`element.tagName` before/after). The prior F-String text (`input: {input}`) is gone (see
     Coverage Map Axis 2 — this is the component's documented `shouldPreserveValue` behaviour,
     not a defect).
7. Open the (now-Select) Value field and confirm its option list is the pipeline's current state
   variables — `input`/`messages` — via `[data-testid^="select-option-"]`, then select `input`
   (`select-option-input`).
   - **Verify**: exactly 2 options (`input`, `messages`) offered — confirmed live, identical
     mechanism/list to the node's own `Input`/`Output` selects (ELITEA-2004 § Concrete Handles).
     After selection, the Value select's text reads `input`.
8. Save the pipeline (`agent-save-button`).
   - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}`
     returns `201 Created`; zero console errors from before step 1 through after step 8 (confirmed
     live this session — 0 console errors, 0 failed/≥400 network requests across the entire flow).
9. Reload at the captured canonical URL (all query params, per the ELITEA-1954 AFS's Known
   Defects entry re: bare `/pipelines/all/{id}` 404ing).
   - **Verify**: SYSTEM's Type select shows `Variable` and its Value (now again a Select) shows
     `input` — confirmed live this session: both survived a full page reload unchanged.

## Expected Results
- The Type select for any LLM-node section offers exactly `Fixed`/`F-String`/`Variable`, all
  selectable.
- Selecting `Fixed` or `F-String` renders the Value field as a free-text `<textarea>`; the typed
  text is preserved across a Fixed↔F-String switch.
- Selecting `Variable` renders the Value field as a completely different widget — a `Select`
  listing the pipeline's own state variables — and clears whatever text value was previously
  entered (switching away from `Variable` clears it again, symmetrically).
- Saving persists the selected Type and its Value (whichever widget shape) for every one of the
  three types; a full reload with the pipeline's canonical URL confirms both survive unchanged.
- No console errors, no failed (≥400) network requests, at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, pipeline with Type+Value fields exists | setup exists | steps 1–2 | step 2: LLM node visible | asserted |
| 1 Open a pipeline with a node that has Type+Value fields | Pipeline open, node has Type+Value fields | steps 1–2 | step 2 | asserted |
| 2 Locate any Type dropdown (SYSTEM/TASK/CHAT HISTORY/CODE/PRINTER/INPUT MAPPING) | Type dropdown visible | step 3 | step 3: `pipeline-llm-node-system-type-select` visible | asserted — **scope: SYSTEM section on the LLM node chosen as the one representative field, per the case's own precondition wording ("e.g., LLM node SYSTEM section") and per role-overrides.md's "scope is exactly the elements the case's test touches" — TASK/CHAT HISTORY/CODE/PRINTER/INPUT MAPPING Type dropdowns are the SAME shared component (`SimpleLLMInputItem.jsx`/`InputMappingItem.jsx`) and not independently re-verified here** |
| 3 Set Type to "Fixed" — Value field accepts plain text | Value field accepts plain text | step 4 | step 4: `input_value()` | asserted — Type already `Fixed` by default, same as ELITEA-2004's SYSTEM section |
| 4 Enter a fixed value | Value field shows the entered text | step 4 | step 4 | asserted |
| 5 Change Type to "F-String" — Value field allows `{variable}` syntax | Value field accepts f-string syntax | step 5 | step 5: `input_value()` | asserted |
| 6 Enter f-string value | Value field shows the f-string value | step 5 | step 5 | asserted |
| 7 Change Type to "Variable" — Value field behavior changes (references state variable directly) | Value field behavior changes to variable-reference mode | steps 6–7 | step 6: DOM element type changes (textarea → Select, confirmed live); step 7: option list = pipeline state variables, selection reflected | asserted — this is the case's central, previously-unexercised assertion (see Covering Spec § The gap) |
| 8 Save pipeline | Pipeline saves without errors | step 8 | step 8: `201` + zero console errors | asserted |
| 9 Reload — Type and Value persist correctly | Type and Value restored after reload | step 9 | step 9: Type=`Variable`, Value=`input` re-read | asserted |
| Expected Final State: all 3 types functional; Type+Value persist after reload | — | steps 3–9 | steps 3–9 | asserted |
| Pass/Fail: all 3 Type options available and selectable; Type/Value persist | — | step 3 (options), steps 4–9 (persist) | — | asserted |

### Axis 2 — Analyst additions

- Step 3 explicitly enumerates the Type select's 3 options via their `select-option-*` testids
  before ever choosing one — *ELITEA-2004's covering test never asserts the full option set
  (it goes straight to selecting `F-String`); added here because it's exactly what case step 2
  ("Type dropdown appears") is checking, and it's free once the popover is open.*
- Step 6 asserts the Value field's underlying DOM element identity (`tagName`/`role`) changes
  between Type states, not just its displayed text — *added because a regression that silently
  left the OLD textarea mounted (with a leftover, stale value) instead of swapping to the new
  Select would otherwise look like a passing test if only text content were checked; this is the
  literal mechanism behind the case's own step-7 wording ("Value field behavior changes").*
- Noted (not asserted as a new persistence check, since it's out of the case's stated final-state
  scope) that switching Type away from `Variable` clears the Value **symmetrically** — confirmed
  both directions live (Variable→Fixed cleared `input`; the earlier F-String→Variable switch also
  cleared `input: {input}`) and via source (`SimpleLLMInputItem.jsx`'s `shouldPreserveValue`
  logic: preserves only Fixed↔F-String, clears for any transition involving `Variable`). Recorded
  here for the implementer's awareness — if the implementer wants an extra defensive assertion,
  this is the exact mechanism to check, but it is not required by the case's own Pass/Fail
  criteria.
- No console-error / no-failed-request assertion was in the original case text; added it to
  step 8 (checked across the whole flow, steps 1–9) — standard practice per this project's
  `test-case-analysis` skill; zero console errors and zero ≥400 responses observed this session.

## Gap Assertions (what ELITEA-2004's covering test does NOT already prove — for the implementer)

1. **`Variable` is a selectable Type option** — ELITEA-2004 never selects it; assert the full
   3-option list (step 3).
2. **Selecting `Variable` swaps the Value field's DOM widget from `<textarea>` to a MUI `Select`**
   — a distinct DOM-shape assertion (`tagName`/`role="combobox"` before/after), not just a text
   check (step 6).
3. **The Variable-mode Value-select's option list is the pipeline's state variables**
   (`input`/`messages`) — same mechanism as `Input`/`Output`, never previously asserted for this
   specific field (step 7).
4. **Type=`Variable` + Value=`input` persists through Save + reload** — ELITEA-2004 only ever
   reload-asserts `Fixed`/`F-String` states for SYSTEM/TASK/CHAT HISTORY; the `Variable` state's
   reload-persistence is entirely new coverage (step 9).
5. **A `data-testid` is currently MISSING on the Value field's Variable-mode Select branch** —
   see § Concrete Handles / § Automation Hints; this blocks steps 6–9 until `add-data-testid`
   lands a one-line fix (the prop is already threaded, just not rendered on this branch).

## Cleanup
1. This session added an LLM node to the shared scratch pipeline `probe-pipeline` (id `6934`,
   project `399`) to observe the Variable-mode Value-field behaviour, then **deleted the node and
   saved**, restoring `probe-pipeline` to its prior empty (`END`-only) state — confirmed via a
   final `react-flow__node-*` DOM read (only `END` remains). No residue left behind.
2. Implementer teardown: standard `pipeline_id` fixture pattern (`PipelineAPI.create_pipeline()`
   in setup, `PipelineAPI.delete_pipeline(pid)` in teardown) — same as ELITEA-2004, no new fixture
   needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| LLM node Type select (SYSTEM) | `[data-testid="pipeline-llm-node-system-type-select"]` — pre-existing, confirmed working (ELITEA-2004) | none needed |
| Type select's 3 options | `[data-testid="select-option-fixed"]` / `-fstring` / `-variable` — confirmed live this session, exact 3, in that DOM order | `[data-testid^="select-option-"]` to enumerate/count |
| SYSTEM Value field, Fixed/F-String modes | `[data-testid="pipeline-llm-node-system-value"]` (a `<textarea>`) — pre-existing, confirmed working (ELITEA-2004) | none needed |
| **SYSTEM Value field, Variable mode** | **Currently NO `data-testid`** — confirmed live via direct DOM inspection: the element is a MUI `Select` (`id="simple-select-Value"`, `role="combobox"`, **no `data-testid` attribute at all**) when Type=`Variable`. **Root cause confirmed via source**: `EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/settings/SimpleLLMInputItem.jsx` — the component already receives a `valueFieldTestId` prop (threaded from `LLMNode.jsx`'s `testIdsByKey.system.valueFieldTestId = 'pipeline-llm-node-system-value'`) and correctly applies it to the Fixed/F-String branch's `<NodeFieldInput dataTestId={valueFieldTestId} .../>`, but the `else` branch's `<SingleSelect label="Value" ... />` (the Variable-mode widget) is **missing `data-testid={valueFieldTestId}` entirely** — a one-line fix that reuses the SAME testid name already wired at every call site (SYSTEM/TASK/CHAT HISTORY on the LLM node, and HITL's `user_message`), consistent with "one testid identifies the Value field regardless of which widget renders it." | **Flag to `add-data-testid`**: add `data-testid={valueFieldTestId}` to the `SingleSelect` in `SimpleLLMInputItem.jsx`'s Variable-mode branch (confirmed exact location this session). No new testid *name* is needed — the existing `pipeline-llm-node-system-value` is reused. |
| Variable-mode Value-select's options | `[data-testid="select-option-input"]` / `[data-testid="select-option-messages"]` — confirmed live, identical `select-option-{value}` mechanism already used by Input/Output selects | `[data-testid^="select-option-"]` to enumerate |
| Add LLM node | `[data-testid="pipeline-add-node-button"]` → `[data-testid="pipeline-add-node-menu-item-llm"]` — confirmed live this session (supersedes ELITEA-2004's older positional locator; both testids on `automation/testids` per `_surface.md`, not yet on `main`) | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed, reused from ELITEA-2004 | none needed |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires
  on Save; `201 Created` on success; persists the SYSTEM section's `type`/`value` fields
  (`{"type": "variable", "value": "input"}` in the Variable case) — confirmed via live network
  capture this session.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires
  on load/reload; the reloaded canvas renders SYSTEM's Type/Value from this response.

## Known Defects Found During Exploration

**None.** All case steps produced the expected result end-to-end once the correct interaction
was used: all 3 Type options are present and selectable, Fixed/F-String share a preserved-value
textarea, Variable swaps to a distinct state-variable Select (by design — confirmed via source,
not a regression), and Type+Value for all three types persist correctly through Save + a full
page reload. Zero console errors, zero failed (≥400) network requests, across the entire session.

The **missing `data-testid` on the Variable-mode Value Select** (§ Concrete Handles) is NOT
classified as a product defect — it is a test-automation gap (a UI element the team hasn't yet
instrumented), routed to `add-data-testid` per this project's locator policy, not to the bug
tracker.

## Blocked Steps

None. All case steps were executed to completion against the live local environment (via the
shared `probe-pipeline` scratch pipeline, cleaned up afterward — see § Cleanup).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). **This
  case requires exactly one `add-data-testid` fix** before steps 6–9 can be implemented: add
  `data-testid={valueFieldTestId}` to the `SingleSelect` in `SimpleLLMInputItem.jsx`'s Variable-mode
  branch (see § Concrete Handles for the exact file/prop). This is a single-line, already-wired-prop
  fix — no new testid name, no call-site changes needed at `LLMNode.jsx`.
- **Two new `PipelineDetailPage` methods are needed** (the existing `get_llm_node_section_value`
  uses `.input_value()`, which throws on a non-input/-textarea element — it cannot read the
  Variable-mode Select):
  - `get_llm_node_section_variable_value(section, timeout=5000)` — read the Value locator's
    `text_content()` with the zero-width-space strip, mirroring `get_llm_node_section_type`'s
    existing pattern (both target the exact same `LocatorDescriptor`, `_llm_node_value_locator`,
    that `get_llm_node_section_value` uses — only the read mechanism differs by widget).
  - `select_llm_node_section_variable_value(section, variable_name, timeout=5000)` — click the
    Value locator, then click `SELECT_OPTION.format(variable_name)`, mirroring
    `select_llm_node_section_type`'s existing pattern.
  Both reuse the SAME `_llm_node_value_locator(section)` / `llm_node_{section}_value`
  `LocatorDescriptor` that already exists — no new locator field, just new methods that treat it
  as a select instead of a text field.
- New test function goes in the SAME file as ELITEA-2004's test
  (`test_pipeline_llm_node_system_task_chat_history_config.py`) — e.g.
  `test_llm_node_system_type_walks_fixed_fstring_variable` — reusing the same `pipeline_id`
  fixture; does not modify ELITEA-2004's existing test body or assertions.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}` response
  (`201`) before reloading/asserting persistence — not a fixed timeout (same as ELITEA-2004).
- Suggested pytest markers: `@pytest.mark.p1`, `@pytest.mark.pipelines`, `@pytest.mark.regression`
  (matches ELITEA-2004's markers, same file).
