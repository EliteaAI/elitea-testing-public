# Test Case: Pipeline — YAML Editor Edit and Save

## Metadata
- **TMS ID**: ELITEA-2067
- **Priority**: high (as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none — API-token/cookie auth for pipeline seeding/cleanup; localhost `auth_state`
  bypass for the UI session (no Keycloak login involved)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `pipelines-remaining-w3`
- **Status**: extend-existing

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_yaml_flow_sync.py`
  (TMS ELITEA-2028, merged to `origin/automation/base` — commits `2809d52f`/`362cacbe`).
- **Behavioural overlap**: ELITEA-2028's merged test already builds the exact scenario ELITEA-2067
  needs — seed `pipeline_with_llm_id`, navigate, switch to Yaml view, edit a line of the YAML
  directly in the CodeMirror editor (`edit_yaml_line()`), switch back to Flow view and confirm the
  edit is reflected live, and confirm the Save button transitions **disabled → enabled** as a
  result of the YAML-driven edit (captured at a clean pre-edit baseline, exactly like this case's
  own step 5). This is ELITEA-2067's steps 1–5, verbatim mechanics.
- **The gap**: ELITEA-2028's test stops at "Save is enabled" — it never clicks Save, never
  reloads, and never verifies the edit persists. ELITEA-2067's steps 6–7 (click Save; reload and
  verify the YAML edit survives) are genuinely new, previously-unexercised assertion surface on
  the identical fixture/page-object/setup ELITEA-2028 already builds — an **incremental addition**
  (continuing the same proven flow one stage further), not a near-rewrite. ELITEA-2028's own test
  body and assertions are untouched.
  - The two cases also differ in WHICH field is edited (ELITEA-2028: a node's `transition:`
    target; ELITEA-2067: a node's `output:` variable — the case's own worked example, "change a
    node's output variable name") and in WHERE the reflected change is checked (ELITEA-2028: a
    ReactFlow canvas edge; ELITEA-2067: the node's own inline config panel field, per the case's
    own step 4 wording "reflected in **node configuration**"), so this is not a literal duplicate
    of ELITEA-2028's assertions even for steps 1–5 — it exercises a different field and a
    different verification surface end-to-end, then extends into the untested save+reload+persist
    territory.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_yaml_flow_sync.py`), reusing the same `pipeline_with_llm_id` fixture,
  `PipelineDetailPage.edit_yaml_line()`/`switch_to_yaml_view()`/`switch_to_flow_view()`/
  `save_and_wait_for_update()` methods ELITEA-2028 already proved, plus the LLM node's
  `get_llm_node_output_value()` reader (already proven live-working in ELITEA-2004's own test,
  same page object) — new only in what field is edited and that it continues through Save +
  reload. Does not modify ELITEA-2028's existing test body or assertions.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: Keycloak via
  `${TEST_USER}`).
- An existing pipeline is open (case's own precondition) — seeded via the existing
  `pipeline_with_llm_id` fixture (`create_pipeline_with_llm_node()` — single LLM node → END,
  `output: []`, i.e. no Output variable selected yet). No UI-driven setup block is needed before
  the case's own steps: unlike ELITEA-2028 (which needs a SECOND node + a prior Save to establish
  a clean dirty-state baseline before its own steps), this pipeline's single-node, freshly-created,
  never-saved-in-this-session state is ALREADY the clean baseline this case needs — confirmed live
  this session: Save/Discard render disabled immediately on first load with zero edits made.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline seeded via `PipelineAPI.create_pipeline_with_llm_node()` (the fixture-backing method
  for `pipeline_with_llm_id`) — unique name per test function, deleted in teardown via
  `PipelineAPI.delete_pipeline()`.

### reuse-existing
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active project was "Private" (id 399).

## Test Steps
(Numbered to match the TMS case's own 7 steps.)

1. Open the pipeline (`pipeline_with_llm_id`) and switch to "Yaml" view.
   - **Verify**: `pipeline-yaml-editor` (YAML CodeMirror) becomes visible.
2. Click into the YAML editor area.
   - **Verify**: cursor is placed in the editor — folded into `edit_yaml_line()`'s own
     click+Home+Shift+End mechanics in step 3 below (the same "click before edit" sequence
     ELITEA-2028 already uses); no separate standalone assertion is meaningful for "cursor
     placed" beyond the edit itself succeeding — see Coverage Map disposition.
3. Make a valid edit — change the LLM node's `output: []` to `output: [messages]` (selecting the
   built-in `messages` state variable as Output; case's own wording: "e.g., change a node's output
   variable name").
   - **Verify**: `get_yaml_content()` contains `output: [messages]` and no longer contains the
     original `output: []`.
4. Switch to "Flow" view — verify the change is reflected in node configuration.
   - **Verify**: `get_llm_node_output_value()` (the LLM node's inline Output field, rendered
     directly on the canvas card — no click-to-open needed, same as ELITEA-2004's confirmed
     mechanics) reads `"messages"`.
5. Verify "Save" button is enabled.
   - **Verify**: `is_save_enabled()` is `True` — AND (Axis-2 addition, matching ELITEA-2028's own
     pattern) was `False` immediately before the edit, at the clean pre-edit baseline, to prove
     the enabling is caused by the YAML edit and not a pre-existing always-on state.
6. Click "Save".
   - **Verify**: `save_and_wait_for_update()` observes the `PUT
     .../application/prompt_lib/{project}/{pipeline_id}` response return `201 Created` (pipeline
     saves without errors); zero console errors introduced by the save.
7. Reload page — switch to Yaml view — verify the edit persisted.
   - **Verify**: after a full page reload (canonical URL, per the ELITEA-1954 404-on-bare-URL
     gotcha) and switching back to Yaml view, `get_yaml_content()` still contains
     `output: [messages]`.

## Expected Results
- A YAML edit to a node's `output:` field is reflected live in the Flow view's node configuration
  panel (the LLM node's Output field reads the new value) once switched back.
- The Save button transitions from disabled (clean baseline) to enabled once the YAML edit is
  applied.
- Clicking Save persists the pipeline (`201 Created`, no console errors).
- After a full page reload, the YAML editor shows the edit exactly as saved — the change survives
  a browser-level round trip, not just the in-memory client state.
- Zero console errors, zero failed network requests, throughout.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, pipeline open | setup exists | setup (pre-step-1) | fixture + navigate | asserted |
| 1 Open pipeline, switch to Yaml view | YAML editor displayed | step 1 | step 1: `pipeline-yaml-editor` visible | asserted |
| 2 Click into YAML editor area | Cursor placed in editor | step 3 (folded in) | `edit_yaml_line()`'s own click+select sequence succeeding is the observable proxy — no separate DOM "cursor position" testid exists to assert against directly | asserted (via proxy) |
| 3 Make a valid edit (change output variable name) | YAML content modified | step 3 | step 3: `get_yaml_content()` contains new value, no longer contains old | asserted |
| 4 Switch to Flow view; verify change reflected in node configuration | Flow view shows modified configuration | step 4 | step 4: `get_llm_node_output_value() == "messages"` | asserted |
| 5 Verify Save button enabled | Save button active | step 5 | step 5: `is_save_enabled()` True, was False before edit | asserted |
| 6 Click Save | Pipeline saves without errors | step 6 | step 6: `201 Created` + zero new console errors | asserted |
| 7 Reload — switch to Yaml view — verify edit persisted | YAML shows modification after reload | step 7 | step 7: `get_yaml_content()` contains `output: [messages]` post-reload | asserted |
| Expected Final State: YAML edit reflected in Flow view, Save activates, edit persists after save+reload | — | steps 3–7 | steps 3–7 collectively | asserted |
| Pass/Fail: all steps complete without errors; edit reflected/saved/persisted | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 5 also asserts Save/Discard are **disabled** at the clean pre-edit baseline, immediately
  before the YAML edit — *added, mirroring ELITEA-2028's own proven pattern: proves the
  disabled→enabled transition is CAUSED by this specific edit, not a seeding artifact that leaves
  Save always-enabled regardless of edits.*
- Zero console errors / zero failed (≥400) requests, asserted across the whole flow (setup through
  step 7's post-reload read) — *added: standard side-channel discipline per this project's
  `test-case-analysis` skill; none observed in live exploration of this exact sequence.*
- Step 3 additionally asserts the OLD value (`output: []`) is gone, not just that the new value is
  present — *added: rules out a false-positive where the edit merely APPENDED text instead of
  replacing the line, which a bare substring-contains check on the new value alone would miss.*

## Gap Assertions (what ELITEA-2028's covering test does NOT already prove — for the implementer)

1. **Clicking Save and observing the `201` response** — ELITEA-2028's test verifies Save is
   *enabled*, never clicks it.
2. **Reload + persistence of a YAML-editor-driven edit** — never exercised anywhere in the merged
   suite for a raw-YAML edit specifically (as opposed to a UI-form-driven edit, which
   ELITEA-2004/ELITEA-2046 already prove persists). This is the first test to prove the
   YAML-editor-write path itself round-trips through Save + reload.
3. **Node configuration panel reads a YAML-driven change** — ELITEA-2028 verifies the ReactFlow
   *canvas edge* reflects a YAML edit; it never reads an inline node config FIELD (e.g. the Output
   select's displayed value) after a raw-YAML edit. This extension is the first to do so.

## Cleanup
1. Standard `pipeline_with_llm_id` fixture pattern (`PipelineAPI.create_pipeline_with_llm_node()`
   in setup, `PipelineAPI.delete_pipeline(pid)` in teardown) — same as ELITEA-2028, no new fixture
   needed.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/role-overrides.md`,
`.agents/testing.md` § Locator policy). All of the following are CONFIRMED present and already
wired as `LocatorDescriptor` fields / page-object methods on `PipelineDetailPage` — **no new
testid work needed for this case**:

| Element | Testid | Page-object field/method | Notes |
|---|---|---|---|
| Switch to Yaml view button | `pipeline-yaml-view` | `yaml_view_button` / `switch_to_yaml_view()` | existing, proven ELITEA-2026/2028 |
| Switch to Flow view button | `pipeline-flow-view` | `flow_view_button` / `switch_to_flow_view()` | existing, proven ELITEA-2028 |
| YAML editor container | `pipeline-yaml-editor` | `yaml_editor` | existing; wraps CodeMirror |
| Per-line YAML edit | n/a (CodeMirror-internal `.cm-line`, #579 exception) | `edit_yaml_line(current, new)` | existing, proven ELITEA-2028 |
| Read YAML content | n/a | `get_yaml_content()` | existing, proven ELITEA-2026/2028 |
| LLM node inline Output field | `pipeline-llm-node-output-select` (existing) | `llm_node_output_select` / `get_llm_node_output_value()` | existing, proven ELITEA-2004; renders inline on the canvas card, no click-to-open needed |
| Save button | `agent-save-button` | `save_button` / `is_save_enabled()` / `save_and_wait_for_update()` | existing, proven ELITEA-2028 |
| Discard button | `discard-button` | `discard_button` / `is_discard_enabled()` | existing, proven ELITEA-2028 |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires
  on Save; `201 Created` on success (same endpoint ELITEA-2004/2028 already document).
- No request fires on switching to/from the Yaml view, or on the raw-text edit itself — both
  render/mutate client-side in-memory pipeline state (confirmed by ELITEA-2028's own Network
  Behavior note; reconfirmed live this session for the `output:` field specifically).

## Known Defects Found During Exploration

**None.** The raw-YAML `output:` edit reflects correctly in the Flow view's inline Output field,
enables Save exactly like the sibling `transition:` edit ELITEA-2028 already proved, and — newly
confirmed this session — persists correctly through Save + full page reload. No product defect
found on any of the case's 7 steps.

## Blocked Steps

None.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). No
  `add-data-testid` work required.
- New test function goes in the SAME file as ELITEA-2028's test
  (`test_pipeline_yaml_flow_sync.py`) — e.g. `test_yaml_edit_persists_after_save_and_reload` —
  reusing the same `pipeline_with_llm_id` fixture; does not modify the existing test's body.
- `edit_yaml_line("output: []", "output: [messages]")` — flow-style (single-line) YAML list
  syntax keeps the edit on one line, matching `edit_yaml_line()`'s single-line replace contract
  (confirmed live: `output: [messages]` parses identically to `output:\n  - messages` and the app
  round-trips it the same way as a UI-driven `select_llm_node_output_variable("messages")` call).
- Capture `canonical_url = page.url` right after the initial navigate (before any edits) for the
  step-7 reload, same as ELITEA-2028/ELITEA-2004's existing pattern (a bare `/pipelines/all/{id}`
  URL 404s — ELITEA-1954).
- Suggested pytest markers: matches the file's existing `pytestmark` (`ui`, `pipelines`, `p1`,
  `regression`) — no new marker needed, applies file-wide already.
