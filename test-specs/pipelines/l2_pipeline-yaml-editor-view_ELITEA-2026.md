# Test Case: Pipeline — YAML Editor View

## Metadata
- **TMS ID**: ELITEA-2026
- **Linked Story**: none (tracking issue `EliteaAI/elitea-testing-public#463`)
- **Priority**: l2 (high, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-07
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with: at least one node, AND at least one **custom**
  state variable. **This is stricter than the case's own Test Data row** —
  see § Known Defects Found During Exploration / clarification
  `EliteaAI/elitea-testing-public#1299`: the built-in `input`/`messages`
  state vars alone do **not** produce a `state:` key in the YAML; only an
  explicit custom variable does. Confirmed live both ways this session (see
  Concrete Handles / Automation Hints for the exact fixture recipe).

## Test Data

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active project was
  "Private" (id 399), matching `.env.test`.

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline created via `PipelineAPI.create_pipeline(name, description,
  instructions=...)` with `instructions` containing an `entry_point:`, one
  `nodes:` entry, **and** a `state:` block with ≥1 custom variable (e.g.
  `custom_text: {type: str}`) — NOT the plain `pipeline_with_llm_id` fixture,
  which has no `state:` key at all (confirmed live, see Preconditions).
  Cleaned up via `pipeline_api.delete_pipeline(pid)`.

## Test Steps
1. Create the precondition pipeline (see Test Data) and navigate to it
   (`PipelineDetailPage.navigate(pipeline_id)`).
   - **Verify**: pipeline loads in Flow view (`is_flow_view_active()` True).
2. Locate the Flow/Yaml toggle group above the canvas.
   - **Verify**: both `flow_view_button` and `yaml_view_button` are visible.
3. Click the `yaml_view_button` (`switch_to_yaml_view()`).
   - **Verify**: `is_yaml_view_active()` returns True (`div.cm-editor` present).
4. Read the YAML editor's line-number gutter.
   - **Verify**: the gutter renders ≥1 `.cm-gutterElement` node, and the
     first one's text is `"1"` (sequential numbering starting at 1 —
     see Concrete Handles for the scoped selector).
5. Locate the "Copy yaml code to clipboard" button.
   - **Verify**: the button is visible above the YAML editor, next to the
     Flow/Yaml toggle group.
6. Read the YAML content (`get_yaml_content()`).
   - **Verify**: the text contains `entry_point:`, `nodes:`, and `state:`
     (substring checks — the fixture from Test Data guarantees all three
     are genuinely present, see Preconditions).
7. Click the "Copy yaml code to clipboard" button.
   - **Verify**: click succeeds (no exception / no console error).
8. Verify copy feedback AND clipboard content.
   - **Verify (feedback)**: the app-wide toast (`toast-alert`,
     `data-severity="info"`) becomes visible with text `"The code has been
     copied to the clipboard."` (`get_toast_alert("info")` / `get_toast_text()`).
   - **Verify (clipboard content)**: `page.evaluate("navigator.clipboard.readText()")`
     returns the same YAML text as `get_yaml_content()` (substring/equality
     check, allowing for whitespace normalization). Safe to call **only**
     inside the real pytest `context` fixture — see Automation Hints for why
     an ad-hoc/scratch browser session must NOT do this.

## Expected Results
- YAML editor view is reachable via the Flow/Yaml toggle, no navigation
  required beyond opening the pipeline.
- Line numbers render sequentially starting at 1.
- The copy-to-clipboard button is present and clickable.
- YAML content contains `entry_point`, `nodes`, `state` (when the pipeline
  has a custom state variable — see Preconditions clarification).
- Clicking Copy produces the `toast-alert` (info severity) success message;
  no console errors anywhere in the flow.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing pipeline with nodes | Pipeline loads in Flow view | step 1 | `step 1`: `is_flow_view_active()` | asserted |
| 2 Locate Flow/Yaml toggle | Toggle group visible above canvas | step 2 | `step 2`: both buttons visible | asserted |
| 3 Click "Yaml" button | YAML editor view activated | step 3 | `step 3`: `is_yaml_view_active()` | asserted |
| 4 YAML editor appears with line numbers | Editor shown with 1,2,3,... | step 4 | `step 4`: gutter element text | asserted |
| 5 "Copy yaml code to clipboard" button appears | Button visible | step 5 | `step 5`: button visible | asserted |
| 6 YAML content contains entry_point/nodes/state | All 3 keywords present | step 6 | `step 6`: substring checks on `get_yaml_content()` | asserted *(precondition changed — see clarification `#1299`; case's own "(or any pipeline with nodes)" wording does not, by itself, guarantee `state:` — a custom state var must be seeded)* |
| 7 Click Copy button | Copy action triggered | step 7 | `step 7`: click succeeds | asserted |
| 8 Verify clipboard contains YAML text (or success feedback) | Toast or clipboard confirms copy | step 8 | `step 8`: `toast-alert` text AND `navigator.clipboard.readText()` | asserted *(both branches — see Automation Hints: the real pytest `context` fixture already grants `clipboard-read`, so this case can assert the primary clipboard-content branch, not just the fallback)* |

**Axis 2 — Analyst additions.**
- `step 3`/`step 6` assert zero console errors across the whole Flow→Yaml→Copy
  flow — *added: side-channel check per skill discipline; confirmed clean
  (0 errors, 0 warnings) across two independent probe pipelines this session.*
- (nothing else added beyond the case.)

## Cleanup
1. Delete the precondition pipeline via `pipeline_api.delete_pipeline(pid)`
   (fixture teardown, mirrors `pipeline_with_llm_id`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Yaml toggle button | `PipelineDetailPage.yaml_view_button` (testid `pipeline-yaml-view`) | pre-existing, confirmed live this session |
| Flow toggle button | `PipelineDetailPage.flow_view_button` (testid `pipeline-flow-view`) | pre-existing |
| YAML editor content | `PipelineDetailPage.yaml_editor` (testid `pipeline-yaml-editor`) | pre-existing; `get_yaml_content()` already reads it correctly (see `_surface.md`) |
| Line-number gutter | **testid needed** — no `data-testid` anywhere on the CodeMirror gutter (confirmed via `document.querySelector('.cm-gutters')` → `data-testid: null`). Sanctioned #579 exception applies (CodeMirror internal render nodes, library-internal DOM, not app JSX) — scoped raw handle: `self.yaml_editor.locator(".cm-gutters .cm-lineNumbers .cm-gutterElement:visible")`, confirmed **inside** the `pipeline-yaml-editor` testid parent (`editorTestidEl.contains(gutter)` → `true`, live-verified). Same shape/precedent as the existing `YAML_LINE_SELECTOR = ".cm-line"` class constant — added as sibling class constant `YAML_GUTTER_LINE_SELECTOR`, same docstring-declared #579 exception. | **Resolved/added during ELITEA-2026 implementation:** the `:visible` filter is REQUIRED, not optional. Live-verified CodeMirror renders a HIDDEN zero-height spacer `cm-gutterElement` FIRST in DOM order (`style="height: 0px; visibility: hidden; pointer-events: none;"`) whose text is a width-measurement placeholder (observed `"99"` — sized to reserve gutter width for the largest expected line-number digit count), not line 1's real number. Without `:visible`, `.nth(0)` reads that spacer and step 4's "first gutter element is '1'" assertion fails on a false negative. Confirmed via `page.evaluate()` dump of all `.cm-gutterElement` nodes (text/class/style) during implementation. |
| "Copy yaml code to clipboard" button | **testid needed**: `pipeline-yaml-copy-button`. Confirmed live: the button has `aria-label="Copy yaml code to clipboard"` but **no `data-testid`** at all (`document.querySelectorAll('button')` grep, confirmed). `add-data-testid` work item — this is genuinely new ground, not a pre-existing gap already flagged elsewhere. | **Resolved during ELITEA-2026 implementation:** testid added to `EliteaUI/src/pages/Pipelines/Components/EditorPanel.jsx` (the `IconButton` wrapped by the "Copy yaml code to clipboard" `StyledTooltip`), committed + pushed to `automation/testids` (`EliteaAI/EliteaUI@dcbd33ef`). `PipelineDetailPage.copy_yaml_button` / `click_copy_yaml_button()` added. |
| Copy success toast | `PipelineDetailPage.get_toast_alert("info")` / `get_toast_text()` (testid `toast-alert` + `data-severity="info"` state filter) | pre-existing, shared app-wide toast component — confirmed live text: `"The code has been copied to the clipboard."` |

## Network Behavior
- Switching Flow⇄Yaml is client-side only — no request fires (confirmed via
  `browser_network_requests` during the toggle).
- Clicking Copy is a pure client-side clipboard write (`navigator.clipboard`
  or `document.execCommand` fallback) — no request fires.

## Known Defects Found During Exploration
- **None found** — the feature works as designed. One **CLARIFICATION**
  filed (case-text drift, not a product defect, per the reverse-masking
  guard): `EliteaAI/elitea-testing-public#1299` — the case's Test Data row
  ("any pipeline with nodes" ⇒ YAML has `entry_point`/`nodes`/`state`) is
  imprecise; `state:` is only emitted once ≥1 **custom** state variable
  exists (confirmed both directions live: `pipeline_with_llm_id`-shaped
  pipeline → no `state:` key at all; same pipeline + a `state:` block in
  `instructions` → `state:` round-trips correctly). This AFS's Preconditions
  seed a custom state var explicitly so step 6's assertion is genuinely
  meaningful rather than an accidental pass/fail depending on fixture choice.

## Blocked Steps
- None. All 8 case steps were executed live and are covered above.

## Automation Hints
- Framework: Playwright/pytest, `PipelineDetailPage` (`automation/pages/pipeline_detail_page.py`)
  — reuse `switch_to_yaml_view()`, `is_yaml_view_active()`, `get_yaml_content()`,
  `get_toast_alert()` / `get_toast_text()` unmodified; only the gutter selector
  and the copy-button testid are genuinely new.
- **Fixture**: no existing fixture seeds a pipeline with a custom `state:`
  block minimally (only `l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md`'s
  richer 4-variable recipe touches this). Build a small dedicated
  `instructions` string (entry_point + one LLM node + one `state:` var) and
  call `pipeline_api.create_pipeline(name, description, instructions=...)`
  directly in test setup — do not reuse `pipeline_with_llm_id` for this case,
  it will make step 6's `state` assertion fail for a reason unrelated to the
  feature under test (see Preconditions clarification).
- **`navigator.clipboard.readText()` is SAFE inside the real test, but NEVER
  in an ad-hoc/scratch browser session.** `automation/conftest.py`'s
  `context` fixture (line ~281) already grants
  `permissions=["clipboard-read", "clipboard-write"]` for the whole suite —
  so `page.evaluate("navigator.clipboard.readText()")` resolves immediately
  inside any real pytest test built on that fixture (this is why step 8
  automates the clipboard-content branch, not just the toast fallback).
  Confirmed live this session (existing role memory, `qa-engineer` /
  `clipboard_read_hangs_without_permission_grant.md`, from ELITEA-2280): a
  bare unprivileged `page.evaluate(() => navigator.clipboard.readText())` in
  an ad-hoc MCP/scratch browser session (no `context` fixture, no
  permissions grant) hangs indefinitely — no error, no timeout, silently
  stalled the calling tool for the full 1800s idle timeout; the page itself
  stayed fully responsive throughout. If any future scratch/exploration
  session needs clipboard-content verification, grant the permission
  explicitly first (`context.grant_permissions(["clipboard-read"])`) —
  never call `readText()` unprivileged.
- Line-number verification: assert the gutter's `.cm-gutterElement` COUNT
  matches `get_yaml_content()`'s own line count (via `YAML_LINE_SELECTOR`)
  and that the first element's text is `"1"` — don't hardcode an absolute
  expected line count, the exact YAML serialization is an implementation
  detail that will drift.
- Toast auto-dismisses fast (~1-2s observed) — assert via
  `get_toast_alert("info")` with an explicit `wait_for(state="visible")`
  immediately after the click, not a snapshot taken a step later.
