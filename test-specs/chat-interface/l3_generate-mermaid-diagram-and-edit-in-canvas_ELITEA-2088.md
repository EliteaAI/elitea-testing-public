# Test Case: Chat – Generate Mermaid Diagram and Open in Canvas Mode

## Metadata
- **TMS ID**: ELITEA-2088
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private")
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — all 11 case steps executed live against the real app. No product defect found. Shares the generic canvas chrome (`Canvas.jsx`/`CanvasEditHeader.jsx`/`EditingPlaceholder.jsx`) with ELITEA-2086/2087 (zero testids, see that AFS) plus its own zero-testid component, `MermaidCodeBlock.jsx`. The mermaid CodeMirror editor is a **sanctioned #579 exception** (third-party editor library internal render nodes) — same category as the project's existing `mcp_form_page.py:121` precedent.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied via the `conversation_id` fixture.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test
- **New conversation** via the `conversation_id` fixture; cleaned up by the fixture's own teardown.
- Message text: `"generate a mermaid diagram"` (case's literal Test Data).
- Edit target: case step 8 says "edit one block of text by adding 'edited' to it" without naming which block. **Automation guidance (important, confirmed live)**: append to a **node-label line** (e.g. `A[Start] --> B{...}` → `A[Start edited] --> B{...}`), **NOT the diagram-type declaration line** (`flowchart TD`/`graph TD`, always line 1). Appending to line 1 breaks Mermaid syntax and the canvas/conversation both fall into a syntax-error state instead of rendering an updated diagram — confirmed live (see step 9/11 below). Editing a node label instead keeps the diagram valid and lets steps 9–11 assert against a real re-rendered diagram rather than an error banner.

## Test Steps

1. Navigate to Chats and open a conversation.
   - **Verify**: `ChatPage.navigate_to_chat(conversation_id=...)`; conversation view displayed.
2. Send the message "generate a mermaid diagram".
   - **Verify**: `ChatPage.send_message()`, then `wait_for_ai_response()` + `wait_for_message_content_stable()`. **Do NOT** wait on a bare `page.wait_for_selector("svg")` — confirmed live to false-positive-match an unrelated icon SVG elsewhere on the page (sidebar/nav icons) well before the diagram itself renders, producing a premature "no edit icon found" false negative on the very first live attempt in this session. Use the message-content-stability wait instead.
3. Verify the diagram displays nodes and connecting lines/arrows.
   - **Verify**: confirmed live — a rendered Mermaid SVG (via `MermaidDiagramOutput/DiagramOutput.jsx`) with boxes/diamonds and connecting arrows; this generation produced a flowchart (`flowchart TD`) with 13 nodes and decision branches. **Diagram type/content is AI-generated and not fixed** — assert structural presence (an SVG with >0 node/edge elements), not exact node text/count.
4. Locate the pencil/edit icon on the diagram.
   - **Verify**: confirmed live — same `CanvasContent` toolbar shape as the table case (`MermaidCodeBlock.jsx` reuses the identical `Canvas.jsx`/toolbar pattern), `Tooltip` title exactly `"Edit diagram"` (computed in `Canvas.jsx` as `type === 'diagram' || language === 'mermaid' ? 'Edit diagram' : ...`). **NO testid** — see § Concrete Handles.
5. Click the pencil icon.
   - **Verify**: confirmed live — canvas panel opens with heading text exactly `"Edit diagram"` (same `CanvasEditHeader.jsx` component/testid gap as ELITEA-2086's "Edit table" heading — `chat-canvas-title`, shared).
6. Verify the canvas displays the Mermaid code/syntax in a text editor.
   - **Verify**: confirmed live — a CodeMirror editor (`.cm-editor`/`.cm-content`, 2 matched elements) shows the raw Mermaid source, one `.cm-line` per source line (19 lines this generation, matching `flowchart TD` + 18 node/edge definition lines). **Bonus, not in case text**: a LIVE-RENDERED diagram preview also appears in a split panel BELOW the code editor within the same canvas (confirmed live, screenshot evidence) — not asserted by this case's own steps, but useful context for the implementer (this is what step 9's real-time validation renders into).
7. Verify the interaction window shows "Diagram editing..." indicator with blue border.
   - **Verify**: confirmed live — same `EditingPlaceholder` component as the table case, text exactly `"Diagram editing..."`. **NO testid** — `chat-canvas-editing-indicator`, shared (see ELITEA-2086's AFS).
8. Edit one block of text by adding "edited" to it.
   - **Verify**: confirmed live — clicking into a `.cm-line` (CodeMirror), pressing `End`, then typing `" edited"` successfully modifies that line's text (confirmed via screenshot; a same-session `all_inner_texts()` poll of `.cm-line` read stale/unchanged text once despite the visible DOM having updated — treat CodeMirror's virtualized line rendering as needing a fresh locator query or a short settle wait after typing, not a raw immediate re-read).
9. Verify the canvas validates Mermaid syntax in real-time.
   - **Verify**: **confirmed live and directly observed** — editing the diagram-TYPE line (`flowchart TD` → `flowchart TD edited`, this session's exploratory edit) triggered an immediate, real-time red error panel: `"Syntax error: Missing semicolon, new line, or unexpected characters (Line 1)"` + `"Problematic code: flowchart TD edited    A[Start]"` + a "Quick Fix" affordance + a red bomb icon replacing the diagram preview (`mermaid version 11.16.0` shown). This is the case's step 9 requirement, confirmed working. **Automation guidance**: edit a node-LABEL line instead (see § Test Data) to assert the HAPPY path (valid diagram re-renders) rather than deliberately exercising the error path — unless a separate case wants to test the error/Quick-Fix path explicitly (not this case's scope).
10. Close the canvas window.
    - **Verify**: confirmed live — same close `IconButton` mechanism as ELITEA-2087 (`chat-canvas-close-button`, shared, no testid).
11. Verify changes are applied to the edited block in the mermaid diagram.
    - **Verify**: confirmed live (this session's exploratory run, which edited the invalid line) — after close, the conversation pane's own diagram render **also** shows the identical syntax-error state (same error text, same "Quick Fix" affordance) that the canvas showed — i.e., the edited (invalid) source synced back faithfully. **With the recommended node-label edit instead** (§ Test Data), the expected observation is a normally re-rendered diagram in the conversation reflecting the edited label text — not independently re-verified with a valid edit in this session (time budget went to isolating the real-time-validation finding above, which is the more informative live discovery); flagging this specific sub-path (valid-edit sync) as the implementer's first-pass confirmation item, not a case-level blocker (the sync MECHANISM itself — canvas state persists to conversation on close — is fully confirmed by the error-path run).

## Expected Results
- All 11 steps pass; the diagram-editing flow, real-time syntax validation, and canvas→conversation sync are all confirmed working. No product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation | — | step 1 | `conversation_id` fixture | asserted |
| 1 Navigate/open conversation → displayed | conversation displayed | step 1 | message input visible | asserted |
| 2 Send message → diagram rendered | diagram rendered | step 2 | SVG present after content-stable wait | asserted |
| 3 Verify nodes/connections | diagram structure | step 3 | SVG node/edge element count > 0 | asserted |
| 4 Locate pencil icon → visible | edit icon visible | step 4 | icon visible, tooltip "Edit diagram" | asserted — testid needed |
| 5 Click pencil → canvas opens, heading "Edit diagram" | canvas opens | step 5 | heading text == "Edit diagram" | asserted — testid needed (shared) |
| 6 Verify Mermaid syntax in text editor | syntax visible/editable | step 6 | `.cm-line` count == source line count | asserted |
| 7 Verify "Diagram editing..." indicator | indicator visible | step 7 | exact text match | asserted — testid needed (shared) |
| 8 Edit block, add "edited" | text modified | step 8 | edited `.cm-line` text contains "edited" | asserted |
| 9 Verify real-time syntax validation | validation occurs | step 9 | error panel appears immediately on invalid edit | asserted (confirmed via the error-path edit) |
| 10 Close canvas | canvas closes | step 10 | canvas testids absent post-close | asserted — testid needed (shared) |
| 11 Verify changes applied in conversation diagram | change reflected | step 11 | conversation view mirrors canvas's edited (error or valid) state | asserted for error-path; valid-path re-render **not independently re-verified this session** — flagged for implementer's first pass |
| Expected Final State: canvas opens, editing works, changes reflected | — | steps 5–11 | — | asserted |
| Pass/Fail: "canvas fails to open/edit/reflect" is FAIL condition | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2's wait-strategy correction (content-stable wait, not a bare `svg` selector wait) is called out explicitly — *added: this exact mistake produced a false "edit icon not found" result on the FIRST live attempt this session, wasting a full run; the fix and the reason are recorded so the implementer doesn't repeat it.*
- Step 9's real-time-validation finding is documented with the FULL live error text and the "Quick Fix" affordance discovered alongside it — *added: this is a genuine, valuable UI discovery (a live Mermaid linter with an AI-assisted quick-fix) beyond the case's literal ask; noted for context, not asserted as an additional requirement since it's out of this case's scope.*
- Step 6's split-panel live diagram PREVIEW inside the canvas (below the code editor) is documented as a bonus observation — *added: useful implementer context (this is what re-renders when a valid edit lands), not part of this case's own assertions.*
- Step 11's "valid edit → diagram re-renders" sub-path is explicitly flagged as not independently re-verified (only the error-path sync was directly observed) — *added transparently rather than silently assuming it works, per the skill's "don't invent handles/observations you didn't exercise" rule. The MECHANISM (canvas state → conversation on close) IS confirmed via the error-path run; only the specific "valid content" rendering branch of that same mechanism is unconfirmed.*

## Cleanup
1. Delete the created conversation via the `conversation_id` fixture's own teardown.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Shared canvas-chrome testids (`chat-canvas-title`, `chat-canvas-close-button`, `chat-canvas-editing-indicator`) are documented once in ELITEA-2086's AFS § Concrete Handles — this case is a third consumer, do not re-request them. Mermaid-specific handles below.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Diagram's own "Edit diagram" pencil icon | **NO TESTID** | needs-adding | `testid needed: chat-diagram-edit-button` on `MermaidCodeBlock.jsx`'s `IconButton` (parallel to ELITEA-2086's `chat-table-edit-button` on the same `CanvasContent`-toolbar shape, different source component). Confirmed 0 hits via `git grep` on `origin/main`/`origin/automation/testids`. Current interim (pre-testid) handle observed live: `[aria-label="Edit diagram"] button`. |
| Canvas heading, dynamic text "Edit diagram" | `chat-canvas-title` (shared) | needs-adding | See ELITEA-2086 § Concrete Handles. |
| Editing indicator, "Diagram editing..." text | `chat-canvas-editing-indicator` (shared) | needs-adding | See ELITEA-2086 § Concrete Handles. |
| Canvas close (X) button | `chat-canvas-close-button` (shared) | needs-adding | See ELITEA-2086 § Concrete Handles; this case also clicks it (step 10). |
| CodeMirror mermaid-source editor — container | **NO TESTID** | needs-adding | `testid needed: chat-canvas-mermaid-editor-content` on `CanvasEditor.jsx`'s CodeMirror wrapper `Box` (`mermaidCodeEditorContainer` style key — currently a styling hook only, not a testid). |
| CodeMirror per-line elements (`.cm-line`) | raw `.cm-line`, scoped inside `chat-canvas-mermaid-editor-content` | n/a | **Sanctioned #579 exception** (third-party editor library internal render nodes) — same category and discipline as `mcp_form_page.py:121`'s existing precedent: parent testid required (above), raw handle scoped as a child of it, declare the exception in the implementing method's docstring. No declared-improvisation flag needed here (unlike ELITEA-2086's DataGrid case) — this is a direct, already-precedented match to the #579 category. |
| Real-time syntax-error panel ("Syntax error: ...", "Quick Fix") | **NO TESTID** | needs-adding | `testid needed: chat-canvas-mermaid-syntax-error` — only if a future case wants to assert the error path explicitly (this case's own recommended happy-path edit does not need it); not required for THIS case's own executed path if the node-label-edit guidance is followed. |
| Rendered Mermaid SVG (both conversation view and canvas live-preview) | **NO TESTID** | needs-adding | `testid needed: chat-mermaid-diagram-svg-container` — the SVG itself is Mermaid-library-rendered (sanctioned #579, category 1: third-party widget subtree), so scope any node/edge-count assertion inside a real testid on the wrapping container, not on the SVG internals. |

## Network Behavior
- No dedicated network call opens the canvas (client-side, confirmed live).
- The real-time syntax validator (step 9) runs client-side (Mermaid's own parser, `mermaid version 11.16.0` shown in the error UI) — no network round-trip per keystroke observed.
- The "Quick Fix" affordance (bonus discovery, step 9) is backed by `useGenerateContentBlockingMutation`/`MERMAID_QUICK_FIX` service-prompt machinery (source-confirmed in `MermaidCodeBlock.jsx`/`CanvasEditor.jsx`) — not exercised live this session (out of this case's scope), flagging only as a pointer for whoever next automates the Quick-Fix flow specifically.
- No 4xx/5xx observed at any point in this session's execution of this case's own 11 steps.

## Known Defects Found During Exploration
None. The apparent "edit didn't take effect" signal from a `.cm-line` `all_inner_texts()` re-read (step 8) was a **transient locator-timing artifact, not a product defect** — the same edit is unambiguously confirmed present via screenshot evidence (canvas + synced conversation view both show `"flowchart TD edited"`) taken moments later in the same run. Gated per the pristine-repro discipline before considering it defect-worthy; it did not survive a second look (visual evidence directly contradicts it), so not filed.

## Blocked Steps
None. All 11 case steps were executed and observed end-to-end live. One sub-path (step 11's valid-edit re-render, as opposed to the error-path re-render actually observed) is flagged for the implementer's first-pass confirmation rather than independently re-verified this session (see § Coverage Map / Axis 2) — this does not block `ready-for-automation` classification since it is one isolable assertion at the tail of an otherwise-fully-confirmed flow, not a wall preventing further exploration.

## Implementer Exploration Notes (Phase 2 amendment — this closes the AFS's
own "valid-edit sync not independently re-verified" gap, § Blocked Steps)

- **Mermaid's individual edge `<path>` elements carry class
  `flowchart-link`, not `edgePath`** (`edgePaths`, plural, is only the
  group WRAPPER `<g>`). `ChatPage.MERMAID_EDGE` uses `.flowchart-link`.
- **A bare end-of-line append does NOT reliably land inside a node's
  rendered label**, and this is the actual reason the AFS's own
  valid-edit sync sub-path was unconfirmed. Confirmed live: clicking a
  `.cm-line`, pressing `End`, and typing `" edited"` (the AFS's own
  step-8 mechanism, confirmed to modify the SOURCE text) lands the new
  text AFTER the line's LAST token. On a compound connection line like
  `A[Start] --> B{Decision}`, that is past the closing `}` — syntactically
  valid (Mermaid still re-renders without error, `node_count > 0` holds)
  but the appended text is outside any node's bracketed label, so it
  never appears in the rendered SVG text. Fixed by switching to
  `ChatDiagramCanvasPage.replace_line()` (select-whole-line-then-type,
  mirroring `McpFormPage.fill_raw_json_line`/`PipelineDetailPage.
  edit_yaml_line`), with the caller inserting `" edited"` immediately
  before the target line's first closing bracket
  (`]`/`}`/`)`) — matching the AFS's own literal example
  (`A[Start] --> B{...}` → `A[Start edited] --> B{...}`) exactly.
- Same caveat as `edit_yaml_line`: CodeMirror's `Home` goes to the first
  NON-whitespace character, so the replacement text passed to
  `replace_line()` must exclude the line's leading indentation (it is
  preserved automatically) — typing it back in doubles the indent.
- **Step 11's assertion target inherits ELITEA-2087's rendering-path
  finding**: after one edit-and-close cycle a block may render via
  `Canvas.jsx`'s `canvas_message` path rather than the plain `text_message`
  path. This case's own step 11 check reads the diagram's SVG text content
  (`chat.diagram_svg_container.text_content()`), not the pencil button, so
  it is unaffected either way.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Edit a node-label line, not the diagram-type declaration line (line 1)** — critical for a happy-path assertion (valid re-rendered diagram) rather than accidentally exercising the syntax-error path. See § Test Data.
- **Wait strategy**: `wait_for_ai_response()` + `wait_for_message_content_stable()` after sending the message — do NOT use a bare `page.wait_for_selector("svg")`, confirmed live to false-positive against unrelated page icons before the actual diagram renders.
- CodeMirror `.cm-line` reads: re-query the locator fresh after typing (don't reuse a `.all_inner_texts()` result captured before the edit) — a stale-read artifact was observed live this session (see § Known Defects Found).
- Reuses the SAME shared canvas chrome as ELITEA-2086/2087 (`chat-canvas-title`/`chat-canvas-close-button`/`chat-canvas-editing-indicator`) — add these testids once across whichever of the three cases implements first; do not triplicate the `add-data-testid` work.
- The CodeMirror `.cm-line` raw-handle scoping is a DIRECT match to the existing #579 sanctioned exception (no reviewer escalation needed, unlike ELITEA-2086's DataGrid case) — cite `mcp_form_page.py:121` as precedent in the implementing method's docstring.
