---
name: MCP/toolkit create form implementer quirks
description: McpFormPage testid gaps (CodeMirror content, detail title, native checkbox/secret inputs, detail-page Save/Discard buttons), MAX_NAME_LENGTH=32 truncation, select_text+Backspace for pre-populated numeric fields, detail-page placeholder-title race, missing wait_for_page_load meant reload_and_wait() silently fell back to bare networkidle (from ELITEA-1922, updated ELITEA-1929)
type: reference
---

# MCP / toolkit create form — implementer-side gotchas (ELITEA-1922)

`automation/pages/mcp_form_page.py` covers both `/mcps/create/mcp` and
`/mcps/all/{id}` (same schema-driven `toolkit-field-{k}-*` testids on both,
since `ToolBaseProperty.jsx` renders both surfaces).

## Testids that didn't exist yet (all added, all live on `automation/testids`)

- `toolkit-field-{k}-editor-content` / `toolkit-raw-json-editor-content` —
  CodeMirror's real editable `.cm-content` node. `CodeMirrorEditor.jsx`
  already has a `contentTestId` prop wired via
  `EditorView.contentAttributes.of({'data-testid': contentTestId})` — same
  mechanism `skill-instructions-editor-content` uses. Just thread the prop
  through `ResizableCodeMirrorEditor` → `CodeMirrorEditor`'s `...rest`.
  **Never** chain `.locator('.cm-content')` off the wrapper testid — that's
  the exact forbidden shape from the ELITEA-1737 case study in
  `.claude/rules/page-objects.md`.
- `toolkit-detail-title` — the toolkit/detail page's name heading
  (`EditToolkit.jsx` leftPart `<Typography variant="headingSmall">`). No
  accessible heading role, no `<h1>` on this page at all — locate by testid,
  not `get_by_role("heading", ...)`.
- `toolkit-field-client_secret-input-field` — `SecretField.jsx`'s
  Password-view `TextField`'s *native* `<input>`. The existing
  `toolkit-field-client_secret-input` testid lands on the TextField's ROOT
  (a caller-prop named `inputProps` gets spread as top-level TextField props,
  which is NOT the same as TextField's own `inputProps` sub-prop that targets
  the real `<input>` — a real gotcha, same name two meanings). Fixed by
  deriving `nativeInputTestId = inputProps['data-testid'] + '-field'` inside
  `SecretField.jsx` and passing it via TextField's actual `inputProps=` prop.
- `toolkit-field-{k}-checkbox-field` — same pattern for
  `ToolBaseProperty.jsx`'s boolean/checkbox fields: `Checkbox.BaseCheckbox`'s
  `data-testid` lands on the MUI `<span>` wrapper; pass
  `inputProps={{'data-testid': \`toolkit-field-${k}-checkbox-field\`}}` for a
  handle on the real `<input>` (`.checked` lives there).

**Rule of thumb for any MUI TextField/Checkbox testid landing on a wrapper
instead of the native input:** check whether the underlying primitive already
exposes a `contentTestId`/`inputProps`-passthrough seam before reaching for
`.locator('input')` — most of EliteaUI's shared field primitives already have
one, it's just not always wired at the call site that needs it.

- `toolkit-detail-save-button` / `toolkit-detail-discard-button` (ELITEA-1929,
  EliteaUI PR #572) — `ToolkitsTabBar.jsx`'s Save `MuiButton` and
  `Button.DiscardButton` had zero testid on the **detail** page, unlike the
  create-form's `toolkit-form-save-button`. `DiscardButton` already accepted
  a `dataTestId` prop (passthrough to `BaseBtn`'s `data-testid`) — just wire
  it at the call site; the Save `MuiButton` needed a plain `data-testid` add,
  MUI forwards it to the root element as usual.

## `wait_for_page_load` was never defined on `McpFormPage`

`BasePage.reload_and_wait()` calls `self.wait_for_page_load(timeout=...)`
*if the page object defines one* (`hasattr` check), else falls back to a bare
`wait_for_network()` (networkidle). `McpFormPage` never defined
`wait_for_page_load` — any test calling `reload_and_wait()` on it was
silently trusting networkidle alone, which does NOT prove the detail title
has re-rendered past the "Edit Toolkit" placeholder (same race documented
above for `navigate_to_detail`). Added `wait_for_page_load()` as a thin
delegate to the existing `_wait_for_detail_data_rendered()` (ELITEA-1929) —
any future McpFormPage-based test calling `reload_and_wait()` now gets the
real placeholder-aware wait for free. Worth checking any *other* page object
lacking `wait_for_page_load` before trusting its `reload_and_wait()` calls.

## Non-testid gotchas

- **Toolkit Name `MAX_NAME_LENGTH=32`** (`EliteaUI/src/common/constants.js`)
  — silently truncates. `autotest_remote_mcp_full_{uuid4().hex[:8]}` (34
  chars) truncates to 33; use a shorter prefix (`autotest_mcp_full_` +
  6 hex chars = 25 total is safe).
- **Bare `Control+a` does not reliably select pre-populated numeric fields**
  (Timeout/Cache TTL default to `"300"`) before typing — `"600"` typed into
  `"300"` produced `"600300"` (append, not replace). Use `select_text()` +
  `Backspace` instead (same pattern as `SkillFormPage.fill_instructions` /
  `set_description`) — works reliably on both empty and pre-populated fields.
- **Detail page title race**: `toolkit-detail-title` renders a static "Edit
  Toolkit" placeholder until the tool-detail GET resolves AND one more React
  tick passes. Waiting on the GET response alone (`page.expect_response`)
  is not sufficient — poll the title text itself
  (`page.wait_for_function` checking `textContent !== 'Edit Toolkit'`).
- **"Choose the MCP type" / "New Remote MCP" have no accessible heading
  role** (plain `<span>` / tab-label) and no testid — don't add one just to
  assert page-load; the testid-bearing type card / name-input's visibility
  already proves the right page loaded, and adding a testid to a shared
  `GroupedCategory`/`CategoryFilter` title used across Agent/Pipeline/
  Credential/Toolkit type pickers is out of this case's touched-element
  scope (testid policy scope rule).
