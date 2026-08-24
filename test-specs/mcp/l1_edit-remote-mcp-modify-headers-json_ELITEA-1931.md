# Test Case: Edit Remote MCP — Modify Headers JSON

## Metadata
- **TMS ID**: ELITEA-1931
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body says
  "medium" — same pre-existing inconsistency recorded in the ELITEA-1929 /
  ELITEA-1930 AFS; frontmatter authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project 399
- **User set**: `${TEST_USER}` (localhost: `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated; project id from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists and its detail page is open in Form view.
- Headers default to `{}` on a freshly created Remote MCP — **confirmed live**
  (`settings.headers` renders as `{}` in the Headers editor before any edit).

## Test Data

### generate-shared-with-cleanup

Same reasoning as the sibling ELITEA-1930 (Ssl Verify) AFS: no discoverable
pre-existing Remote MCP on this environment (`ToolkitAPI.list_all_toolkits()`
returns an empty list regardless of auth method), and writing custom headers is
destructive to whatever toolkit is borrowed → the test seeds its own disposable
Remote MCP through the real UI create flow and deletes it in teardown.

| Field | Value | Why |
|---|---|---|
| Seed name | `autotest_mcp_hdr_<6hex>` (23 chars) | ≤ `MAX_NAME_LENGTH = 32` |
| Url | `https://mcp.example.com/sse` | stored only; never dialled (no Load Tools in this case) |
| Headers JSON (case Test Data) | `{"X-Custom-Header": "test-value"}` | the case's literal value |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` (seeded toolkit id 3035,
deleted after the run).

| # | Action | Expected (case) | Observed live |
|---|--------|-----------------|---------------|
| 1 | Open a Remote MCP detail page in Form view | Detail page loads in Form view | `toolkit-form-view-toggle` `aria-pressed == "true"`; `toolkit-detail-title` == seeded name |
| 2 | Expand "Headers" section (click "Headers" accordion) | Headers accordion expands | **DIVERGENCE — there is no "Headers" accordion.** Headers is a JSON-editor *field* inside the single **Configuration** section, which on the detail page is collapsed behind `toolkit-configuration-show-more` (digest § MCP DETAIL page: configuration fields are COLLAPSED). Before expanding, `toolkit-field-headers-editor` count == 0; after `expand_configuration_section()` the editor is visible. Expanding does **not** dirty the form. |
| 3 | Verify JSON editor for headers is visible (default: `{}`) | JSON editor shows empty object `{}` | `toolkit-field-headers-editor-content` `text_content() == "{}"` |
| 4 | Enter valid JSON `{"X-Custom-Header": "test-value"}` | Editor accepts and displays the input | after select-all + Backspace + `keyboard.type(...)` the editor's `text_content()` is **exactly** `{"X-Custom-Header": "test-value"}` — CodeMirror's bracket/quote auto-close does NOT duplicate characters here (type-over). **Save is still DISABLED at this point** — see § Automation Hints (commit-on-blur). |
| 5 | Click Save | Operation completes successfully | after blurring the editor (clicking another field) the editor **re-formats** to pretty-printed JSON (`{\n  "X-Custom-Header": "test-value"\n}`) and Save/Discard become enabled; `PUT /tool/prompt_lib/{project}/{id}` → **200**, response body `settings.headers == {"X-Custom-Header": "test-value"}`. **No success toast on this surface** (digest) — the PUT + persisted state is the confirmation. |
| 6 | Reload page — expand Headers — verify JSON persisted | Headers JSON shows `{"X-Custom-Header": "test-value"}` | after `reload_and_wait()` the field is again count == 0 until re-expanded; after `expand_configuration_section()` the editor's `text_content()` is `{  "X-Custom-Header": "test-value"}` (CodeMirror line `<div>`s concatenate without newlines) → parse with `json.loads` and compare the **dict**, never the raw string |
| 7 | Switch to Raw Json view — verify headers in full JSON config | Full JSON includes the custom headers entry | `get_raw_json_full()["settings"]["headers"] == {"X-Custom-Header": "test-value"}` (nested under `settings`, not at the root); full editor payload 388 chars / 19 lines |

## Expected Results
- The Headers editor defaults to `{}` on a freshly created Remote MCP.
- Typing valid JSON is displayed verbatim by the editor.
- Blurring the editor commits the value (form becomes dirty, Save enabled) and
  pretty-prints it.
- Save issues a `PUT` returning 200 whose body carries the custom header under
  `settings.headers`.
- The header survives a full page reload (server-side persistence).
- The Raw Json view shows the header object under `settings.headers`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: existing Remote MCP open in Form view | precondition (seeded) | seeded via the UI create flow — § Test Data; Form view asserted in step 1 |
| Step 1 — detail page loads in Form view | asserted | `form_view_toggle` `aria-pressed == "true"` + `detail_title` == seeded name |
| Step 2 — Headers section expands | asserted (divergent handle) | `headers_editor` count == 0 pre-expand → visible after `expand_configuration_section()`; the case's "accordion" is the Configuration show-more (see § Case-text divergence) |
| Step 3 — editor shows `{}` | asserted | `get_headers_json_text() == "{}"` |
| Step 4 — editor accepts and displays the input | asserted | `get_headers_json_text() == '{"X-Custom-Header": "test-value"}'` immediately after typing |
| Step 5 — Save completes successfully | asserted | PUT 200 + body `settings.headers == {...}` |
| Step 6 — headers persisted after reload | asserted | post-reload (+ re-expand) `json.loads(get_headers_json_text()) == {...}` |
| Step 7 — Raw Json includes the headers entry | asserted | `get_raw_json_full()["settings"]["headers"] == {...}` |
| Expected Final State — saved, persists, visible in Raw Json | asserted | steps 5-7 together |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291 filtered, #549 soft — sibling-spec pattern) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Save-button state assertions (disabled pristine → still disabled with focus in the editor → enabled after blur) | Step 5 presupposes Save is clickable; the commit-on-blur behaviour is the single most likely thing to make an implementation silently fail, and the dirty gate is real on this surface (`ToolkitsTabBarContainer.jsx:102-109`). |
| PUT-response body assertion | Step 5's "operation completes successfully" is otherwise unobservable — no toast is rendered here. |
| Comparing parsed dicts, not raw editor strings, in steps 6-7 | The product legitimately re-formats the JSON on blur; asserting the raw string would assert formatting, not the case's observable. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Case-text divergence
Step 2 says *"Expand 'Headers' section (click 'Headers' accordion)"*. The live
product has **no Headers accordion**: `headers` is one schema-driven field of the
**Configuration** section (label "Headers", rendered as a CodeMirror JSON editor),
and on the detail page that whole section is collapsed behind a single
`toolkit-configuration-show-more` control. The step's *intent* (make the Headers
editor reachable) is executed faithfully by expanding that section; the automation
asserts the live contract, not the case's wording (reverse-masking guard,
`.agents/role-overrides.md`). Filed as a case-text clarification — see § Findings
in the Run Report.

## Cleanup
The seeded toolkit is deleted in a `finally:` block via
`ToolkitAPI.delete_toolkit(id)`. No shared state is mutated.

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Headers editor wrapper | `toolkit-field-headers-editor` | on-main ✓ |
| Headers editor `.cm-content` | `toolkit-field-headers-editor-content` | on-main ✓ |
| Client Id input (blur target only) | `toolkit-field-client_id-input` | on-main ✓ |
| Configuration show-more | `toolkit-configuration-show-more` | on `automation/testids` |
| Detail Save / Discard buttons | `toolkit-detail-save-button` / `toolkit-detail-discard-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Form / Raw Json view toggles | `toolkit-form-view-toggle` / `toolkit-raw-json-view-toggle` | on-main ✓ |
| Raw Json editor content | `toolkit-raw-json-editor-content` | on-main ✓ |
| Detail title | `toolkit-detail-title` | on-main ✓ |

No new testid is required for this case.

## Network Behavior
- `POST /tools/prompt_lib/{project}` → 201 (seed).
- `GET /tool/prompt_lib/{project}/{id}` on detail load and after reload.
- `PUT /tool/prompt_lib/{project}/{id}` → 200 on Save.
- The URL is **never dialled** — nothing in this case triggers `mcp_sync_tools`.

## Known Defects Found During Exploration
None. The commit-on-blur behaviour is a product characteristic (the shared
CodeMirror-backed JSON field propagates on blur), not a defect: a real user
clicking Save moves focus out of the editor as part of that click, and the value
does commit.

## Blocked Steps
None.

## Automation Hints
- **The Headers editor commits on BLUR.** Verified live: with focus still in the
  editor after typing, `toolkit-detail-save-button` stays **disabled**; clicking
  another field flips both Save and Discard to enabled. Same class of behaviour as
  the credentials `scopes` field (`credential_form_fields.py § type_into_field`).
  Do **not** fold the blur into `McpFormPage.fill_headers_json()` — that method has
  a merged caller (`test_mcp_create_remote.py:100`) which reads the editor text
  immediately after filling and would then read the *pretty-printed* form.
- `expand_configuration_section()` is required twice: on first load and again
  after `reload_and_wait()`.
- Switching Raw Json → Form view keeps the configuration section **expanded**
  (no second expand needed after a view toggle — only after a reload).
- `text_content()` on a multi-line CodeMirror concatenates lines with no
  separator (`{  "X-Custom-Header": "test-value"}`) — always `json.loads` it.
- Use `get_raw_json_full()`: cheap here (19 lines) and immune to the CodeMirror
  virtualization trap if a future schema grows the payload.
