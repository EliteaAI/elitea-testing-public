# Test Case: Pipeline — YAML Editor Invalid Syntax

## Metadata
- **TMS ID**: ELITEA-2068
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case; sibling
  `medium` pipeline cases in this folder use `l3_` + `@pytest.mark.p2`, e.g.
  `l3_entry-point-webhook-trigger-settings-modal_ELITEA-2006.md`, same
  medium→p2 convention)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: none — API-token auth (`ELITEA_API_TOKEN`) for pipeline
  seeding/cleanup; localhost `auth_state` bypass for the UI session (no
  Keycloak login involved)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot,
  batch `elitea-2068`)
- **Status**: ready-for-automation

## Preconditions
- A pipeline with a single LLM node connected to END exists, with a clean
  saved canvas layout (Save/Discard disabled on load) — the existing
  `pipeline_with_llm_id` fixture satisfies this exactly as-is. Unlike the
  related ELITEA-2028 case, this case does NOT need a second node — a
  single `transition: END` line is unambiguous for the edit target.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline seeded via `PipelineAPI.create_pipeline_with_llm_node()` (the
  `pipeline_with_llm_id` fixture) — unique name per test, deleted in
  teardown via `PipelineAPI.delete_pipeline()`.

## Test Steps
(Numbered to match the TMS case's own 6 steps.)

1. Navigate to the pipeline's detail page; confirm default view is Flow,
   then switch to Yaml view.
   - **Verify**: `pipeline-yaml-editor` (YAML CodeMirror) becomes visible.
2. Introduce invalid YAML syntax: edit the LLM node's `transition: END`
   line to `transition: "END` (an unterminated double-quote — a
   confirmed-live YAML scanner error, not a guess) via
   `PipelineDetailPage.edit_yaml_line()` (existing method, reused as-is —
   see AFS ELITEA-2028's Concrete Handles for the method's own docstring
   and ambiguity caveat; not applicable here since this pipeline has only
   ONE `transition: END` line).
   - **Verify**: `get_yaml_content()` contains the literal
     `transition: "END` (confirms the invalid syntax is present in the
     editor's content, matching the case's own Step-2 expected result).
3. Switch back to Flow view.
   - **Verify**: `pipeline-flow-view`'s canvas (`rf__wrapper`) becomes
     visible. Confirmed live: the canvas does NOT error or blank out —
     it keeps rendering the last-known-valid graph (LLM 1 → END edge
     unchanged), since the invalid YAML was never parsed into a new
     graph. This satisfies the case's own "(may show partial or error
     state)" qualifier without over-asserting a specific error rendering
     the live product doesn't actually show on the canvas itself (the
     error surfaces later, on Save — see step 5).
4. Verify the Save button is enabled (indicating unsaved changes).
   - **Verify**: `save_button.is_enabled()` is `True` — AND (Axis-2
     addition) was `False` immediately before the edit, at the clean
     seeded baseline, to prove the enabling is caused by the YAML edit
     and not a pre-existing always-on state (same rationale as AFS
     ELITEA-2028 step 5 — confirmed live via the same seeding path).
5. Attempt to save the pipeline — verify an error message appears
   indicating invalid YAML.
   - **Verify**: clicking Save fires a `PUT
     .../application/prompt_lib/{project}/{pipeline_id}` request that
     returns **400** (confirmed live — not a guess), whose body contains
     `"Invalid pipeline YAML data"` (exact substring, confirmed live: the
     full message is `Value error, Invalid pipeline YAML data: while
     scanning a quoted scalar in "<unicode string>", line N, column M:
     …`). AND the app-wide error toast (`toast-alert` /
     `toast-message`, `Toast.jsx`, confirmed pre-existing testids — no
     EliteaUI change needed) becomes visible with `data-severity="error"`
     and text containing the same `"Invalid pipeline YAML data"`
     substring.
6. Verify the pipeline cannot be saved with invalid YAML.
   - **Verify**: `PipelineAPI.get_pipeline(pipeline_id)`'s stored
     `instructions` (server-side, via a direct API read — NOT just the UI
     state) still contain the ORIGINAL, valid `transition: END` line and
     do NOT contain the invalid `transition: "END` edit — i.e. the
     server genuinely rejected the write, this isn't merely a client-side
     toast with the mutation silently persisted underneath.

## Expected Results
- YAML editor is visible after switching to Yaml view.
- The invalid-syntax edit is reflected live in the editor's own content
  (`get_yaml_content()`).
- Flow view remains renderable (shows the last-known-valid graph, not a
  blank/crashed canvas) after switching back with invalid YAML pending.
- The Save button transitions from disabled (clean baseline) to enabled
  once the invalid edit is applied — same dirty-state detection already
  proven for valid edits (AFS ELITEA-2028), now confirmed to also engage
  for edits that happen to be invalid YAML (the app can't tell the
  difference client-side until Save is attempted).
- Attempting to save invalid YAML is rejected server-side with **400**
  and a `"Invalid pipeline YAML data"` message, surfaced to the user via
  the app-wide error toast.
- The pipeline's server-side stored `instructions` are unchanged by the
  failed save attempt (verified via a direct API read, not just absence
  of a UI success indicator).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| precond: existing pipeline is open | — | setup (pre-step-1) | fixture seeds + navigates | asserted |
| 1 Open pipeline, switch to Yaml view | YAML editor displayed | step 1 | `step 1`: `pipeline-yaml-editor` visible | asserted |
| 2 Introduce invalid YAML syntax | YAML content contains invalid syntax | step 2 | `step 2`: `get_yaml_content()` contains `transition: "END` | asserted |
| 3 Switch to Flow view | Flow view displayed (may show partial/error state) | step 3 | `step 3`: `rf__wrapper` canvas visible | asserted |
| 4 Verify Save button enabled | Save button active | step 4 | `step 4`: `save_button.is_enabled()` True | asserted |
| 5 Attempt save — error message shown, save blocked | Error message shown; save blocked | step 5 | `step 5`: 400 response + toast text assertion | asserted |
| 6 Pipeline cannot be saved with invalid YAML | Save operation fails with error indicating invalid YAML | step 6 | `step 6`: `get_pipeline()` instructions unchanged | asserted |

**Axis 2 — Analyst additions:**
- `step 4` also asserts Save/Discard are **disabled** at the clean seeded
  baseline, immediately before the invalid edit — *added: mirrors AFS
  ELITEA-2028's rationale — proves the disabled→enabled transition is
  caused by the edit, not a seeding artifact that leaves the form always
  dirty (see that AFS's Automation Hints "Seeding gotcha" — not
  applicable to THIS case's precondition since `pipeline_with_llm_id`
  alone, unmodified, is the correct seed here, but the baseline-disabled
  check is still worth asserting rather than assumed).*
- `step 5` also asserts the toast's `data-severity="error"` (state via
  `data-*` filter on the stable `toast-alert` testid, not a
  severity-suffixed testid — `.agents/testing.md` § Locator policy) —
  *added: distinguishes a genuine error toast from a coincidental
  info/success toast that happened to contain similar text.*
- `step 6` asserts via a direct API read (`PipelineAPI.get_pipeline()`),
  not just "no success toast appeared" — *added: a UI-only assertion
  would not rule out a silent partial write; the server-side read is the
  authoritative check that "not saved" really means not saved.*

## Cleanup
1. Delete the seeded pipeline via `PipelineAPI.delete_pipeline(pipeline_id)`
   in fixture teardown (`pipeline_with_llm_id` — no extra cleanup needed).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/role-overrides.md`,
`.agents/testing.md` § Locator policy). All testids below are CONFIRMED
present live — no EliteaUI testid work needed for this case:

| Element | Testid | Page-object field | Notes |
|---|---|---|---|
| Switch to Yaml view button | `pipeline-yaml-view` | `yaml_view_button` | existing |
| Switch to Flow view button | `pipeline-flow-view` | `flow_view_button` | existing |
| YAML editor container | `pipeline-yaml-editor` | `yaml_editor` | existing |
| Save button | `agent-save-button` | `save_button` (inherited from `PipelineFormPage`) | existing |
| Discard button | `discard-button` | `discard_button` (inherited) | existing |
| ReactFlow canvas wrapper | `rf__wrapper` | `canvas_wrapper` | existing; sanctioned #579 exception |
| App-wide toast Alert root | `toast-alert` | **NEW field needed**: `toast_alert` | confirmed live in `../EliteaUI/src/components/Toast.jsx:61` — app-wide shared component, testid pre-exists; only a page-object field is new (same per-page-declares-its-own-field precedent as `ChatPage.toast_alert`) |
| App-wide toast message text | `toast-message` | **NEW field needed**: `toast_message` | `Toast.jsx:80`, same as above |
| Toast severity state filter | `[data-testid="toast-alert"][data-severity="{}"]` | **NEW class constant needed**: `TOAST_ALERT_SEVERITY` | testid-identity + `data-*` state filter, per the "testid=identity, state via data-*" policy — mirrors `ChatPage.TOAST_ALERT_SEVERITY` |

**Reused as-is (no changes needed):**
- `PipelineDetailPage.edit_yaml_line()` — existing method from AFS
  ELITEA-2028, used here to introduce the invalid edit. This case's
  pipeline (single `transition: END` line) sidesteps that method's
  documented ambiguity caveat entirely.
- `PipelineDetailPage.get_yaml_content()` — existing.
- `PipelineFormPage.is_save_enabled()` / `is_discard_enabled()` — existing.

**New page-object method needed** — waiting on a FAILING save response (no
existing method does this; `save_and_wait_for_update()` only waits for a
201):
- Add `PipelineDetailPage.save_and_wait_for_error_response(project_id,
  pipeline_id, timeout)` — mirrors `save_and_wait_for_update()`'s existing
  shape (`expect_response` + JS-evaluate click) but matches `r.status >=
  400` instead of `r.status == 201`, returning `{"status": ..., "body":
  ...}` (raw text, not assumed-JSON, since the 400 body may not always be
  valid JSON — confirmed live it currently is a JSON `{"detail": [...]}`
  Pydantic-style validation error, but reading it as text and letting the
  caller substring-match is more robust than assuming a schema).

## Network Behavior
- Clicking Save with invalid YAML in the editor fires `PUT
  /api/v2/elitea_core/application/prompt_lib/{project_id}/{pipeline_id}`,
  which returns **400** (confirmed live) with a body containing
  `"Invalid pipeline YAML data"` — a Pydantic-style validation error
  surfaced from the backend's own YAML parse attempt, not a client-side-only
  check.
- No other network requests fire during the view-switch/edit steps
  (client-side CodeMirror/ReactFlow state only, consistent with AFS
  ELITEA-2028's own Network Behavior finding).

## Known Defects Found During Exploration
None found. All 6 case steps executed cleanly against the live product;
invalid YAML is correctly rejected server-side with a clear error message,
and the pipeline's stored instructions are genuinely left unchanged. No bug
filed.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, project standard).
- Page object: extend `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`) — add `toast_alert`/`toast_message`/
  `TOAST_ALERT_SEVERITY`/`save_and_wait_for_error_response()` as described
  above; everything else is reused as-is.
- Fixture: `pipeline_with_llm_id` is the correct seed — a single LLM node
  is sufficient (no second-node setup needed, unlike ELITEA-2028).
- Test placement: this is a **fresh spec**
  (`test_pipeline_yaml_editor_invalid_syntax.py`), NOT an extension of
  `test_pipeline_yaml_flow_sync.py` (ELITEA-2028's covering spec) — despite
  sharing the same page object and YAML-editor surface, the observable
  under test (invalid-YAML rejection + error toast + unchanged server
  state) has ZERO assertion overlap with ELITEA-2028's observable (valid
  edit syncs to the Flow canvas + Save enables). Per
  `test-case-analysis` SKILL.md § Classify findings, `extend-existing` is
  reserved for Rule-6 *partial-overlap* dedup on the SAME observable — this
  is not that; treating it as `extend-existing` here would be the "false
  extend" anti-pattern the skill explicitly warns is more expensive than a
  duplicate fresh spec. Recorded in `test-specs/pipelines/_surface.md` for
  future analysts on this surface.
- Wait strategy: same confirmed-live timings as ELITEA-2028
  (`switch_to_flow_view()`/`switch_to_yaml_view()` already settle ~1s;
  `edit_yaml_line()` already waits for content-stability internally). The
  Save-error path needs `expect_response` on the PUT (see new method
  above), not a fixed wait — the 400 arrives well within the existing
  15s timeout budget used elsewhere in this file (`save_and_wait_for_update`).
