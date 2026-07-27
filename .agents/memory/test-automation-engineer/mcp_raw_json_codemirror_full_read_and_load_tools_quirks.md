---
name: MCP Raw Json full-read (CodeMirror virtualization) and Load Tools quirks
description: get_raw_json_full() technique for reading the whole Raw Json editor past CodeMirror's rendered-line-window virtualization, plus the Load Tools / tool-chip / Test Settings dropdown testid wiring, from ELITEA-1933 implementer session
type: feedback
---

## get_raw_json_full() — reading past CodeMirror virtualization (ELITEA-1933)

`McpFormPage.get_raw_json()` reads `raw_json_editor_content.text_content()` in
one call — fine for small payloads, but CodeMirror only keeps a
viewport-sized window of `.cm-line` nodes in the DOM (~30 of ~85 lines for a
3-tool `available_mcp_tools` payload), truncating silently (no error; either
raises `json.JSONDecodeError` or, worse, ends on a coincidentally-valid
partial JSON).

Key discovery: the CM6 `.cm-content`/`.cm-scroller` nodes themselves NEVER
overflow (`scrollHeight === clientHeight` always — they grow to fit the full
doc). The real scrollable ancestor is further up the DOM (in this case a MUI
Grid column wrapping the whole Configuration panel, a generated `css-*`
class — don't hardcode it, walk up from the editor testid for the first
ancestor with `scrollHeight > clientHeight`). CM6's viewport-visibility
tracking keys off THAT ancestor's scroll position, not the CM content node's
own (non-existent) overflow.

Working technique — `get_raw_json_full()` on `McpFormPage`:
1. Walk up from `raw_json_editor_content`'s selector for the first ancestor
   with real overflow.
2. Scroll it in `clientHeight // 2`-sized steps (50% overlap — a smaller
   fixed margin like `clientHeight - 40` left an uncovered gap under a
   headless viewport, producing invalid JSON on the reconstructed string).
3. At each step, read every currently-rendered `.cm-line`'s `offsetTop`
   (stable regardless of which scroll position revealed it) paired with its
   text; aggregate into a `dict[offsetTop, text]` — this both de-dupes
   overlapping windows and gives correct order via `sorted()`.
4. **Critical timing gotcha:** a synchronous "set scrollTop, then read
   `.cm-line` in the same tick" sometimes reads the PREVIOUS scroll
   position's rendered lines — CM6's viewport recompute is itself
   rAF-scheduled off the scroll event. This passed when manually probed via
   slow separate `playwright-cli` subprocess calls (each with real wall-clock
   gaps) but FAILED under pytest's faster back-to-back `page.evaluate()`
   calls. Fix: make the per-step `evaluate()` an async JS function that
   `await`s two `requestAnimationFrame`s after setting `scrollTop`, before
   reading `.cm-line` — a condition-based wait on the browser's own render
   pipeline (not a sleep, satisfies Hard Rule 5).
5. A single scroll-to-bottom-then-read does NOT work either — CM6 REPLACES
   its rendered line set on each scroll rather than extending it (confirmed:
   scrolling straight to the bottom surfaced only the last ~53 of ~85 lines).

Added as a NEW method (`get_raw_json_full`), not a modification of
`get_raw_json()` — 3 existing callers (`test_mcp_create_remote.py`,
`test_mcp_edit_raw_json_description.py`, `test_mcp_edit_toggle_enable_caching.py`)
use small payloads where truncation never triggers; per Hard Rule 3
additive-only-on-shared-caller-files, left them untouched and re-ran all 3
green (2 hit the unrelated pre-existing #549 known-defect soft-fail, not a
regression from this change).

## Load Tools / tool-chip / Test Settings testids (added this session)

`ToolActionsSelector.jsx`'s "Load Tools" is a bare `Typography onClick`
(no MUI Button) inside `BasicAccordion`'s `summaryAction`. `EmptyMcpTools.jsx`
is the empty-state `<Box>`. `ToolActionsItems.jsx` renders discovered-tool
pills via the SHARED `src/components/ChipWithCheckIcon.jsx` — being a shared
component, it takes a new `testId` prop (never a hardcoded feature testid)
wired at the call site with the dynamic pattern `toolkit-tool-chip-{tool
value}`; also added `data-selected={isSelected}` on the same Chip per the
testid-is-identity/state-is-a-separate-attribute ruling, so
`is_tool_chip_selected()` reads `data-selected` rather than checking for the
checkmark SVG icon's presence.

`TestToolSettings.jsx`'s "Tool" select is `Select.SingleSelect` (the shared
`src/[fsd]/shared/ui/select/SingleSelect.jsx`) — that component ALREADY
forwards a `data-testid` prop straight to the underlying MUI `<Select>`
(`data-testid={dataTestId}` from a `'data-testid': dataTestId` destructure),
so wiring `toolkit-test-tool-select` there was call-site-only, no shared
component edit needed. Worth checking for this destructure pattern before
assuming every shared MUI wrapper needs a new prop threaded through.

Selecting a tool via `#simple-select-Tool` → `select-option-{tool_name}`
(shared `SingleSelectMenuItem.jsx` pattern) is the affordance that actually
renders the tool's parameter schema fields — clicking a Tools-section pill
only toggles `selected_tools` membership, it does NOT open a schema panel
(case-text clarification, filed as issue #595 by the analyst pass, confirmed
again live this session).

## Test Settings schema-param-field testids (added in PR #596 review-fix pass)

The rendered parameter fields themselves (one per JSON-schema property on the
selected tool — e.g. `ask_question`'s `repoName`/`question`) had ZERO testid
coverage on first implementation; the initial PR used a raw
`page.get_by_text(fieldKey)` (flagged CHANGES_REQUESTED — testid-only policy
violation, not a documented stop+flag exception since these are ordinary
EliteaUI elements). Root component: `ToolFormContainer.jsx` dispatches by
JSON-schema `type` to one of several `src/[fsd]/shared/ui/field/*` renderers
— `CommonStringField.jsx` (plain/enum/codeLanguage string fields) and
`AnyOfPatternField.jsx` (anyOf string-or-array fields, e.g. `repoName`) were
the two touched here. Added `data-testid={\`toolkit-test-param-${fieldKey}\`}`
to the outer `<Box className="index-config-field">` wrapper in ALL THREE
`CommonStringField` render branches (enum/codeLanguage/default) plus
`AnyOfPatternField`'s single branch — `automation/testids` commit `a3c58b93`.

Confirmed these two components are consumed ONLY via `ToolFormContainer.jsx`
(itself used by `TestToolSettings.jsx` + a separate, never-co-rendered
`IndexConfig.jsx` on the Indexes feature) — so the `toolkit-test-param-*`
testid can never collide with the create/detail form's own
`toolkit-field-{k}-*` testids, which come from a completely different
component tree (`ToolBaseProperty.jsx`). Page object: `McpFormPage`'s
`TEST_PARAM_FIELD = '[data-testid="toolkit-test-param-{}"]'` dynamic
template constant + `is_test_param_field_visible(field_key)`.

**Still uncovered** (out of scope for this fix, flag for the next MCP/toolkit
schema-field case that needs them): `CommonNumberField.jsx`,
`CommonBooleanField.jsx`, `CommonObjectField.jsx`, `CommonArrayField.jsx`,
`SecretInputField.jsx` — same `ToolFormContainer.jsx` dispatch, same
`className="index-config-field"` wrapper shape, zero testid today. Same fix
pattern (`data-testid={\`toolkit-test-param-${fieldKey}\`}` on the wrapper)
should apply cleanly when one of those field types is next exercised.
