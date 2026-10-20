# Test Case: Project Context creation and update from chat with chip opening in Canvas

## Metadata
- **TMS ID**: ELITEA-3368
- **Source case**: `.agents/automation/chat-project-context-builder/cases/ELITEA-3368.md` (snapshot)
- **Linked Story**: `EliteaAI/elitea_issues#6239`
- **Priority**: l1 (case priority: `critical` → AFS `l1_` prefix → pytest
  `@pytest.mark.p0`, matching the family convention already established by
  the sibling (unmerged) `ELITEA-3252/3253/3254/3255` family test's own
  docstring — `critical` priority throughout → `p0`).
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app`),
  project `Private` (`${ELITEA_PROJECT_ID}` = `575` in `automation/.env.test`).
  `scripts/dev_storage_state.py` storage state; `mcp__playwright__browser_*`
  tools unavailable in this container (no Chrome binary at
  `/opt/google/chrome/chrome` — see `.agents/memory/qa-engineer/elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`),
  so exploration used a standalone `sync_playwright` script
  (`p.chromium.launch(headless=True)`, loading the same storage-state file) —
  not committed, scratch-only.
- **User set**: `${TEST_USER}` (dev-token/API-login session; renders as
  `autotest_user_admin`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all
  9 numbered steps + preconditions observed against the real DEV app, 6
  independent live runs across both create and create+update flows). No
  product defect found; one case-text precondition clarified (see Known
  Defects). No existing merged spec covers this case's own observable (see
  Coverage decision) — the only overlapping spec (ELITEA-3254, the
  2500-char-limit family) lives on an **unmerged** sibling branch
  (`tests/batch-project-context-char-limit`, commit `4d3f0c72`), so per the
  merged-target rule it cannot be an `extend-existing`/`already-covered`
  target for THIS case.

## Coverage decision — why `ready-for-automation`, not `extend-existing`/`already-covered`

Searched `test-specs/` and `automation/tests/` by behaviour (project context,
chat chip, canvas, `project_context_builder`) before executing. Found:

- `test-specs/settings-project-params/l2_project-context-character-limit-2500_ELITEA-2272.md`
  (merged, `automation/tests/ui/settings/` — file since removed by commit
  `3fcc1478`, per the sibling family test's own docstring) — covers the
  **Settings UI editor's** 2500-char boundary, not the chat creation flow at
  all. Different surface, different observable. Not a target.
- A sibling family test, `automation/tests/ui/settings/test_project_context_ai_generation_char_limit.py`
  (`TestProjectContextAIGenerationCharLimit::test_chat_project_context_builder_under_limit`,
  TMS ELITEA-3254) — **does** drive the exact same chat `project_context_builder`
  module tool this case touches, confirmed via `git show 4d3f0c72`. However:
  - It lives on `tests/3252-3253-3254-3255-project-context-char-limit` /
    `tests/batch-project-context-char-limit`, **neither merged to
    `origin/main` nor an ancestor of this batch's own trunk**
    (`git merge-base --is-ancestor 4d3f0c72 origin/main` → not an ancestor;
    same against `tests/batch-chat-project-context-builder` → not an
    ancestor). Per the merged-target rule, an unmerged sibling branch can
    never be an `extend-existing`/`already-covered` target — only a spec
    merged to base, or (for `extend-existing` only) already on THIS batch's
    own trunk.
  - Even disregarding the merge state, its own observable is narrower and
    orthogonal: it asserts the **2500-char limit holds** for one
    generate+save message (tool-chip text + content length), never the
    **chip's own click-opens-Canvas affordance** (case step 3), never the
    **not-added-as-a-participant** behaviour (case step 5), and never the
    **update-in-place / no-duplicate** behaviour (case steps 6–9) — all of
    which are THIS case's actual Pass criteria. The two cases are siblings
    on the same module tool, not duplicates of each other.
- No spec anywhere drives the chip → Canvas-open → update → no-duplicate
  flow this case specifies.

Conclusion: `ready-for-automation`, fresh test. The reused suite (`ChatPage`'s
existing modules-toggle, participants-panel, and `generated-entity-chip`-era
infra, none of which previously had this flow driving them) made exploration
fast but does not change the classification — this is new coverage, not a
duplicate.

## Preconditions
- User is logged in to `https://dev.elitea.ai` (satisfied by the dev storage
  state / API-login session).
- Project Context Builder is enabled in Chat Modules — **NOT ambient**:
  confirmed live via `GET /api/v2/social/module_settings/{project_id}` that
  `default_project_context_builder_enabled: false` for this project, and the
  in-chat Modules submenu's `modules-toggle-project_context_builder` switch
  renders unchecked (`is_checked() == False`) on a fresh conversation. The
  case's precondition text implies the module is simply "enabled" as a given;
  live behaviour is that **every new conversation starts with it OFF** and
  the test must explicitly enable it per-conversation via the `+` menu →
  Modules submenu before sending the creation message (same per-conversation
  toggle mechanism `test_chat_modules_panel_full_menu_and_all_toggles` already
  exercises for the other 9 module keys). This is a clarification of an
  under-specified precondition, not a defect — see Known Defects.
- The current project has no existing Project Context configured — enforced
  via API teardown (`DELETE
  /elitea_core/project_context/prompt_lib/{project_id}/project-context`,
  tolerate 404) before the test, mirroring ELITEA-2272's established
  precondition-enforcement pattern (`clean_project_context`-style fixture).
- Canvas mode is available — confirmed live, no gating observed (same
  `ChatEditorPanel`/`BaseEditor` chrome every other in-chat canvas uses).

## Test Data

### reuse-existing
- `${TEST_USER}` — dev-token/API-login session.
- `${ELITEA_PROJECT_ID}` (`575`, "Private") — ambient default project for
  this session.

### generate-per-test (created via the UI action under test, cleaned up in its own teardown)
- **New conversation** — created via `ChatPage.click_create_conversation()`
  (existing method); this case's own first action is sending the creation
  message into a conversation, so any fresh conversation satisfies the
  precondition (same "no dependency on a prior case" pattern as ELITEA-2085's
  AFS).
- Context content (create), **case's literal Test Data**: `"Create project
  context: This project is a Python REST API for order management."`
- Update request, **case's literal Test Data**: `"Update the project context
  to mention we now support GraphQL in addition to REST."`

### API endpoints used for setup/teardown/verification (not UI, so no testid needed)
- `GET /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → `{"id": ..., "content": "...", "enabled": true, "activation_description":
  ..., "updated_at": ...}` when set, or `{"id": null, "content": "", "enabled":
  true, "activation_description": null, "updated_at": null}` when unset.
  Confirmed live: HTTP 200 either way (never 404 on GET — same contract
  ELITEA-2272's AFS already documented).
- `DELETE /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → HTTP 204 when a context exists; tolerate 404 (not independently re-probed
  this session, but ELITEA-2272's AFS already confirmed it — same endpoint).
- `GET /api/v2/social/module_settings/{project_id}` — confirms the
  per-project module DEFAULT (not the per-conversation toggle state the test
  actually drives); useful for diagnosing an unexpectedly-pre-enabled module,
  not required by the test's own steps.
- `DELETE /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  — cleanup (singular path, matches `ConversationAPI.delete_conversation()`'s
  existing docstring note).

## Test Steps

1. Open a fresh conversation (`ChatPage.click_create_conversation()`). Open
   the `+` menu (`plus-menu-button`), hover **Modules**, click the
   `project_context_builder` toggle switch
   (`[data-testid="modules-toggle-project_context_builder"]`, reuses
   `ChatPage.MODULES_TOGGLE_SWITCH.format("project_context_builder")`) to
   enable it for this conversation, then click elsewhere to close the
   submenu (clicking inside the still-open submenu/tooltip region
   intercepts pointer events on the composer — confirmed live, see
   Automation Hints).
   - **Verify**: toggle switch state element reports checked (`element.checked
     === true`, same DOM-property read `ChatPage.is_module_toggle_checked()`
     already uses) before proceeding.
2. Send the message `"Create project context: This project is a Python REST
   API for order management."` via the composer (`chat-message-input`) +
   send button (`chat-send-button`, falls back to
   `role=button name="send your question"` — confirmed live this is the
   send button's accessible name on this build).
   - **Verify**: no clarifying question is asked — the assistant proceeds
     directly to creation. Confirmed live 4 separate times with this exact
     message (and close variants): every run produced a direct "Project
     context created"/"...established"/"...updated" response with the tool
     chips below, never an intermediate question.
3. Wait for the AI response (`wait_for_ai_response()`-style condition wait,
   not a fixed sleep — tool invocation + generation observed live at
   9–20s).
   - **Verify**: a tool-invocation chip containing `"Elitea Project Context:
     post_elitea_core_generate_project_context_draft"` appears during
     "Thought for N secs" (confirmed live — the live tool-chip text is a
     colon-separated `"{service}: {endpoint_name}"` shape, same convention
     ELITEA-2215's AFS already documented for a different toolkit).
   - **Verify**: a `[data-testid="generated-entity-chip"]` renders in the
     assistant's answer, below the response text (confirmed live — this is
     the SAME `GeneratedEntityChip` component the Agent/Pipeline/Toolkit/
     Skill "Build with AI"/create-via-chat flows already use; its chip label
     reads the literal text `"Project Context"` for this entity type,
     confirmed via `entity_name` being the fixed string).
4. Click the chip (hover first to reveal the "Open entity" icon button —
   `role=button name="Open entity"`, scoped inside the chip — then click
   it; a bare click on the chip's own container does nothing, confirmed
   live, see Automation Hints).
   - **Verify**: a Canvas panel opens on the right with heading text
     `"Project Context"` (no dedicated `titleTestId`/testid on this heading
     — confirmed live via DOM text-match, see Concrete Handles) and the
     SAME `ProjectContextEditor` component the Settings → Project Context
     "Create" flow already renders (`project-context-editor-content`,
     `project-context-save-button`, `project-context-char-counter` — all
     pre-existing testids, confirmed identical live in both hosts).
5. Verify Canvas content.
   - **Verify**: `project-context-editor-content`'s text matches the content
     the AI generated from the prompt (confirmed live — content is a
     markdown-structured elaboration of "Python REST API for order
     management", not a verbatim echo of the user's one-line prompt; assert
     non-empty + topically consistent, not an exact string match, since the
     AI's exact phrasing varies run to run — same non-determinism caveat
     `test-specs/chat-interface/_surface.md`'s AI-generated-table section
     already documents for a different surface).
6. Open the PARTICIPANTS panel (`ChatPage.expand_participants_panel_via_toggle()`,
   existing testid-backed method).
   - **Verify**: the panel renders with NO participant rows at all — the
     created Project Context is NOT present as a participant. Confirmed
     live: `PARTICIPANT_ROW_PREFIX` (`[data-testid^="chat-participant-row-"]`)
     resolves to zero elements, and no `PARTICIPANTS_BADGE` of any kind
     renders either, immediately after the chip/Canvas-open sequence above.
7. Close the Canvas (click the header's X icon-button — same
   `EditorHeader.jsx` close `IconButton` every other in-chat canvas uses;
   NO testid on this build, see Concrete Handles) and send the update
   message: `"Update the project context to mention we now support GraphQL
   in addition to REST."`
   - **Verify**: the assistant updates the EXISTING Project Context (no
     clarifying question; direct "Project context updated..." response).
8. Wait for the AI response.
   - **Verify**: a tool-invocation chip containing
     `"Elitea Project Context: get_project_context_project-context"` AND one
     containing `"Elitea Project Context: put_project_context_project-context"`
     both appear (confirmed live — the update path reads-then-writes,
     distinct from the create path's single `generate_project_context_draft`
     chip in step 3).
   - **Verify**: a `generated-entity-chip` referencing "Project Context"
     appears again in this new answer.
9. Verify via a direct API GET (`GET
   /elitea_core/project_context/prompt_lib/{project_id}/project-context`)
   that:
   - the returned `id` is IDENTICAL to the `id` captured right after step 3
     (no duplicate entity created) — confirmed live across 2 independent
     create+update runs: `id` was `64` before and after the update in one
     run, unchanged in the other.
   - the returned `content` includes the word `"GraphQL"` (case-insensitive)
     — confirmed live both runs.
   Then click the chip again (hover → "Open entity") and verify the Canvas's
   `project-context-editor-content` reflects the updated content (contains
   "GraphQL") — closes the loop with a UI-level read, not API-only.

## Expected Results
- Project Context is created with content matching the AI's elaboration of
  the Test Data prompt (step 2–5).
- A `generated-entity-chip` labeled "Project Context" appears in the chat
  response and clicking it (via its hover-revealed "Open entity" button)
  opens the Canvas showing that content (steps 3–5).
- The created Project Context is NOT added to the Participants panel (step
  6).
- The update message modifies the SAME entity in place — identical `id`
  before/after, content now includes "GraphQL" — rather than creating a
  second Project Context (steps 7–9).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Project Context Builder enabled in Chat Modules | — | AFS step 1 | `modules-toggle-project_context_builder` checked, confirmed via DOM property read | asserted *(clarified: per-conversation toggle, not an ambient project setting — see Known Defects)* |
| Precondition: no existing Project Context | — | Setup (API DELETE, tolerate 404) | precondition enforced, not case-observed | asserted |
| 1 Send "Create project context: ..." → Assistant proceeds without clarifying questions | no clarifying question | AFS step 2 | direct creation response text, confirmed live 4× | asserted |
| 2 Verify chat response contains a Project Context chip | chip/link displayed | AFS step 3 | `generated-entity-chip` present, label "Project Context" | asserted |
| 3 Click the Project Context chip/link | Canvas mode opens | AFS step 4 | hover → "Open entity" button → `project-context-editor-content` visible | asserted *(decomposed: hover-then-click is required, a bare chip click is a no-op — see Automation Hints)* |
| 4 Verify Project Context content in Canvas | content matches what was provided | AFS step 5 | editor content non-empty + topically consistent with the prompt | asserted *(exact-string match correctly avoided — AI phrasing is non-deterministic, same caveat as the AI-generated-table precedent)* |
| 5 Open the conversation's participant list | newly created Project Context NOT auto-added | AFS step 6 | `PARTICIPANT_ROW_PREFIX` count == 0, no badge rendered | asserted |
| 6 Send update request | Assistant updates the existing Project Context | AFS step 7 | direct update response text | asserted |
| 7 Verify chat response contains a Project Context chip (updated) | chip/link displayed, referencing updated entity | AFS step 8 | `generated-entity-chip` present again in the new answer | asserted |
| 8 Click the chip and verify content | existing entity now includes GraphQL detail | AFS step 9 (second half) | Canvas editor content contains "GraphQL" after reopening | asserted |
| 9 Navigate to Project Context list; no duplicate | only one updated entity | AFS step 9 (first half) | API GET `id` identical before/after update | asserted *(implemented via a direct API GET rather than the Settings UI list, since Project Context is a SINGLETON per project — there is no "list" to navigate to; see Known Defects)* |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1 asserts the module toggle's checked state via a DOM-property read
  BEFORE sending the creation message — *added: without this guard, a flaky
  toggle-click (overlay interception, confirmed as a real live hazard — see
  Automation Hints) would silently leave the module off and the whole case
  would fail downstream with a confusing "no chip appeared" symptom instead
  of a clear "toggle didn't engage" one.*
- Step 3 asserts the specific `post_elitea_core_generate_project_context_draft`
  tool-chip text, and step 8 asserts the specific
  `get_project_context_project-context` / `put_project_context_project-context`
  pair — *added: distinguishes the create path's single-call shape from the
  update path's read-then-write shape, which the case text itself doesn't
  call out but is directly observable and gives the implementer a precise
  wait/assert target instead of only the generic "a tool chip appears".*
- Step 9 adds a UI-level re-verification (reopen the Canvas, read the editor
  content) on top of the API GET — *added: closes the loop so the test
  doesn't only prove the API was updated while silently never checking the
  UI the user actually looks at, matching this suite's established
  API-response ⇄ UI cross-check pattern (e.g. ELITEA-2085's step 7).*
- Side-channel console-error check folded into every step (not in the
  case's own text) — *added: standard practice on this surface, confirmed
  clean across all runs this session.*

## Cleanup
1. `DELETE /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
   — the conversation created in step 1 (via `ConversationAPI.delete_conversation()`).
2. `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
   (best-effort, tolerate 404) — restores the empty-state precondition for
   the next run. Confirmed live: returns 204 when content exists.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration — DEV, ladder provenance)

| Element | Rung | Handle | Provenance | Notes |
|---|---|---|---|---|
| `+` menu button | 1 (testid) | `plus-menu-button` | pre-existing, confirmed live | `ChatPage.plus_menu_button` |
| Modules submenu toggle (Project Context Builder) | 1 (testid) | `modules-toggle-project_context_builder` | pre-existing on DEV, confirmed live | `ChatPage.MODULES_TOGGLE_SWITCH.format("project_context_builder")`; already in `MODULE_TOGGLE_ORDER` |
| Message composer | 1 (testid) | `chat-message-input` | pre-existing, confirmed live | `ChatPage.message_input` (existing) |
| Send button | 1 (testid) | `chat-send-button` | pre-existing (`LocatorDescriptor` with `fallback=` to `role=button name="send your question"` already in `chat_page.py:49`) | existing `ChatPage.send_button` |
| Tool-invocation chip | 1 (testid) | `chat-answer-tool-chip` | pre-existing, confirmed live for both `post_elitea_core_generate_project_context_draft` and `get_/put_project_context_project-context` text | existing `ChatPage.answer_tool_chip`; filter by `.filter(has_text=...)` |
| Generated-entity chip (create/update response) | 1 (testid) | `generated-entity-chip` | **NEW on DEV, confirmed live — not yet declared in `chat_page.py`** | `GeneratedEntityChip.jsx:data-testid="generated-entity-chip"`, label text = entity's name (literal `"Project Context"` for this entity type). Needs a new `ChatPage` field: `LocatorDescriptor(testid="generated-entity-chip")` (plus a `GENERATED_ENTITY_CHIP_PREFIX`-style scoped lookup is NOT needed — unlike attachment chips, there is normally exactly one per answer for this case's flow). |
| Chip's hover-revealed "Open entity" button | 2 (role+name) | `role="button" name="Open entity"` | **NO testid** — confirmed live via full `GeneratedEntityChip.jsx` source read: `aria-label="Open entity"` on the `Button.BaseBtn`, no `data-testid` anywhere on it | `suggested_testid="generated-entity-chip-open-button"`. Only visible after hovering the chip's container (`isHovering` state) — the bare chip has no `onClick` of its own. |
| Chip's hover-revealed "Delete entity" button | 2 (role+name) | `role="button" name="Delete entity"` | **NO testid**, same component, confirmed via source | `suggested_testid="generated-entity-chip-delete-button"`. Not exercised by this case's own steps (no delete-via-chip assertion in the case text) — not touched. |
| Canvas (Project Context) heading | — (text match) | DOM text == `"Project Context"` | **NO testid** — confirmed live + via source: `ProjectContextEditor.jsx`'s `<BaseEditor title="Project Context">` call passes no `titleTestId`, though `BaseEditor`/`EditorHeader` already support the prop (same gap pattern ELITEA-2085's AFS documented for the MCP canvas title) | `suggested_testid="project-context-canvas-title"` |
| Canvas close (X) button | 5 (xpath, scoped) OR coordinate-free alternative | header's first icon-button, no `aria-label`, no testid | **NO testid** — confirmed live + via source: `EditorHeader.jsx`'s close `IconButton` receives `data-testid={closeButtonTestId}`, and `ProjectContextEditor.jsx`'s `<BaseEditor>` call never passes `closeButtonTestId` (same omitted-optional-prop gap as `mcp-canvas-close-button`/`agent-canvas-close-button` before THEIR fixes) | `suggested_testid="project-context-canvas-close-button"`. **Scope non-positionally**: scope to the Canvas container (e.g. a parent testid'd element, or `ScopedLocator` keyed off `project-context-editor-content`'s ancestor) and pick the ONLY icon-button with no visible text inside that scope — do not pick by raw page-wide coordinate or `.first` across the whole page (this exploration used a raw pixel coordinate click as a scratch-script expedient only; that is NOT how the implementer should build the production locator). |
| Canvas editor content | 1 (testid) | `project-context-editor-content` | pre-existing (ELITEA-2272), confirmed identical live inside the chat-hosted Canvas | existing `ProjectContextPage.editor_content` — reuse `ProjectContextPage(page)` composed on the same `page`, same pattern as `AgentCanvasPage`+`AgentFormPage` |
| Canvas Save button | 1 (testid) | `project-context-save-button` | pre-existing (ELITEA-2272) | existing `ProjectContextPage.save_button` |
| Canvas char counter | 1 (testid) | `project-context-char-counter` | pre-existing (ELITEA-2272) | existing `ProjectContextPage.char_counter` |
| Activation-description input (new since ELITEA-2272, per the sibling family test's docstring) | — | not exercised by this case | not applicable | this case's flow never reaches Save manually — the AI tool call does its own PUT with whatever `activation_description` the tool sets; not asserted here, out of this case's scope |
| Participants panel toggle | 1 (testid) | `chat-participants-panel-toggle-button` | pre-existing (ELITEA-2168), confirmed live | existing `ChatPage.participants_panel_toggle_button` / `expand_participants_panel_via_toggle()` |
| Participant row (any entity type) | 1 (testid, dynamic prefix) | `[data-testid^="chat-participant-row-"]` | pre-existing, confirmed live resolves to ZERO matches post-creation | existing `ChatPage.PARTICIPANT_ROW_PREFIX` |

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- Chip's "Delete entity" hover button (no delete-via-chip step in the case).
- The Settings → Project Context page's own UI (`ProjectContextPage.navigate()`
  / `create_button` / empty-state) — step 9's "no duplicate" verification uses
  a direct API GET instead (Project Context is a per-project singleton, not a
  list — see Known Defects), so the Settings page is never navigated to by
  this test.
- Activation-description field (see table above).

## Network Behavior
- `POST /api/v2/elitea_core/generate_project_context_draft/prompt_lib/{project_id}`
  — fires on the create message; 200 on success (confirmed live via the
  WebSocket trace's `post_elitea_core_generate_project_context_draft` tool
  name — the actual HTTP verb/path is inferred from the tool-name string,
  not independently confirmed via a raw network-tab capture this session;
  if the implementer wants a hard status-code assertion, confirm the exact
  REST shape via `/shared/openapi/?all=true` first, per
  `.agents/role-overrides.md`'s 4xx/5xx-classification ladder — not needed
  for THIS case's happy-path, which never hits an error status).
- **Declared improvisation (gate run 2/3 fix):** the LLM nondeterministically
  (~1 in 4 runs) saves the create-path directly via
  `Elitea Project Context: put_project_context_project-context` instead of
  `generate_project_context_draft`. The case (step 2) only requires "a Project
  Context chip/link" and names no tool, so the Step 3 tool-chip pin was relaxed
  to accept EITHER tool name (still requires an "Elitea Project Context" tool
  chip). Downstream assertions (entity chip, Canvas, API entity, participant,
  update) are unchanged.
- **Declared improvisation (gate run, update path):** same nondeterminism on
  Step 8 — the LLM sometimes only calls `put_project_context` with no preceding
  `get_project_context`. The read-then-write chip pair pin was relaxed to
  require a Project Context tool chip (`get_` OR `put_project_context`); the
  same-id/no-duplicate, GraphQL content and Canvas-reopen assertions are unchanged.
- `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires on both the create and update paths (the create path's single
  `generate_project_context_draft` tool call appears to generate-and-save in
  one request, matching the sibling ELITEA-3254 test's own documented
  drift note: "put_project_context, not the case's named
  generate_project_context_draft"). Confirmed live via the direct API GET
  showing non-empty content immediately after the create message, with no
  separate manual Save click in this flow.
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires as part of the update path's tool-chip pair (`get_project_context_project-context`
  before `put_project_context_project-context`), and is also how this AFS's
  own steps 3-after/9 verify server state directly.

## Known Defects Found During Exploration
None — no product defect found. One CLARIFICATION (case-text drift, not a
bug — reverse-masking guard applies):

1. **Precondition "Project Context Builder is enabled in Chat Modules" is
   per-conversation, not an ambient project setting.** Confirmed live:
   `GET /api/v2/social/module_settings/{project_id}` returns
   `default_project_context_builder_enabled: false`, and a brand-new
   conversation's Modules submenu toggle for this key renders OFF. The case
   text's precondition phrasing reads as if the module is simply "on" as a
   given project state; the live mechanism requires the test to explicitly
   toggle it per-conversation (step 1) — the SAME per-conversation toggle
   mechanism `test_chat_modules_panel_full_menu_and_all_toggles` (ELITEA-2464)
   already exercises for every other module key. This does not change the
   case's Pass/Fail criteria — it only clarifies HOW the precondition is
   satisfied in automation. Not filed as a tracker issue (purely a
   test-authoring note, not a product-behavior gap — the module toggle UI
   itself works exactly as every other module key's does); recorded here per
   the reverse-masking guard's spirit so the implementer doesn't waste time
   rediscovering it.
2. **Case step 9 ("Navigate to Project Context list") does not literally
   apply** — Project Context is a per-project SINGLETON resource
   (`GET .../project-context` always returns one object, never a collection;
   there is no "Project Context list" page anywhere in the app — confirmed
   live via the Settings sidebar, which has a single "Project Context" item,
   not a list/table view). The case's intent ("confirm no duplicate was
   created") is fully satisfiable via the same singleton GET endpoint
   (compare `id` before/after) — implemented that way in AFS step 9. Not a
   defect; the case text's "list" wording is generic Pass/Fail phrasing that
   doesn't map to a literal UI element for this particular entity type.

## Blocked Steps
None. All 9 case steps + preconditions were executed and observed live, both
in isolation and across 2 independent full create→update→verify runs plus 4
additional create-only runs used for chip/Canvas/participants-panel
exploration.

## Automation Hints
- Framework: Playwright + pytest, ladder locators (`.agents/testing.md`).
- **Compose, don't rewrite**: reuse `ChatPage` (conversation creation, Modules
  toggle, send/receive, participants panel) + `ProjectContextPage` (Canvas
  editor content/Save/char-counter — same component, same testids, confirmed
  identical live inside the chat-hosted Canvas) on the SAME `page` object —
  mirrors the `AgentCanvasPage`+`AgentFormPage` / `McpCanvasPage`+`McpFormPage`
  composition pattern already established for every other in-chat
  create/edit canvas.
- **New `ChatPage` surface needed**: a `generated_entity_chip` field
  (`LocatorDescriptor(testid="generated-entity-chip")`) plus two
  `ScopedLocator`s for its hover-revealed buttons (`role="button"
  name="Open entity"` / `name="Delete entity"`, each with a
  `suggested_testid=` per the table above) and a small
  `open_generated_entity_chip(entity_label: str)` helper that: locates the
  chip (optionally `.filter(has_text=entity_label)` if more than one chip
  could render — not needed for THIS case, which has exactly one), hovers
  it, then clicks the scoped "Open entity" button. **A bare `.click()` on
  the chip's own container does nothing** — confirmed live (the chip `Box`
  has no `onClick`; only its hover-revealed child buttons do) — don't ship
  a click-the-chip-directly implementation, it will silently no-op.
- **New `ChatCanvasProjectContext`-scoped close-button locator**: no shared
  `ChatCanvasPage`/`GeneratedEntityEditorPanel` page object exists yet for
  this specific canvas's chrome (unlike Agent/Pipeline/MCP, which each got
  their own `*CanvasPage`); either add a minimal
  `ProjectContextCanvasPage` (mirroring `McpCanvasPage`'s shape: just
  `close_button` + maybe a `title` text-match helper) OR add the close
  button directly as a new field on `ProjectContextPage` scoped to a Canvas
  container ancestor — implementer's call, declare the choice in the Run
  Report per `.agents/role-overrides.md`'s declared-improvisation protocol
  (no existing precedent names which page object should own a NEW entity's
  in-chat canvas chrome when that entity's "form" page object already
  exists for a non-chat host).
- **Modules submenu interception gotcha, confirmed live**: after clicking
  the `project_context_builder` toggle, the submenu/tooltip stays open and
  its DOM intercepts pointer events on the composer underneath — a
  subsequent `composer.click()` can time out with a Playwright
  actionability error ("subtree intercepts pointer events") unless the
  submenu is explicitly dismissed first (click elsewhere on the page body,
  or `Escape`, confirmed both work live). Close the Modules submenu
  (`ChatPage.close_modules_panel()`, already exists per the sibling family
  test's own step 2) before interacting with the composer.
- **Wait strategy**: no fixed sleeps. Use `wait_for_ai_response()`-style
  condition waits for both the create and update messages (observed live:
  9–20s per response, tool-call-plus-generation); wait for the
  `generated-entity-chip` to become visible before attempting to hover/click
  it (it is NOT present during streaming — confirmed live it only renders
  once `!isStreaming && !isLoading`, same `ApplicationAnswer.jsx` gating
  every other entity-chip type uses).
- **Non-determinism**: the AI's exact generated content varies run to run
  (confirmed live: six different runs of near-identical create prompts
  produced six differently-worded "Project context created/established/
  updated:" responses, all topically faithful to the input). Never assert
  exact generated text — assert non-empty, topical keyword presence
  ("Python", "REST", "order management" or similar for create;
  case-insensitive "graphql" for the update), and the API-level `id`
  stability for the no-duplicate check.
- No sanctioned-RED / known-defect handling needed — this case's happy path
  is fully clean across every run this session.

**Resolved/added during ELITEA-3368 implementation (2026-10-17):** built
exactly per the plan above, no scope drift —
- `ChatPage.generated_entity_chip` (`testid="generated-entity-chip"`) +
  `GENERATED_ENTITY_CHIP_OPEN_BUTTON`/`GENERATED_ENTITY_CHIP_DELETE_BUTTON`
  (`ScopedLocator(role="button", name=...)`) +
  `open_generated_entity_chip(entity_label=None)` added to `chat_page.py`,
  exactly the shape this section specced.
- **Declared improvisation resolved**: added a NEW page object,
  `pages/project_context_chat_canvas_page.py` (`ProjectContextChatCanvasPage`),
  rather than a bare field on `ProjectContextPage` — mirrors `McpCanvasPage`'s
  shape (`title` + `close_button` + `wait_for_open()`/`close()`) since the
  in-chat canvas chrome is a distinct component (`EditorHeader.jsx`) from
  `ProjectContextPage`'s own Settings-page chrome; composed with
  `ProjectContextPage(page)` on the same `page` for the editor
  content/Save/char-counter per this section's own plan. Both `title` and
  `close_button` landed as declared `xpath=` rungs (rung 5) scoped off
  `project-context-editor-content`'s `<form>` ancestor and the title's own
  exact-text Typography — confirmed via full source read
  (`EditorHeader.jsx`/`BaseEditor.jsx`) that neither carries a testid or an
  aria-label on this build, matching this section's prediction; `suggested_testid=`
  `project-context-canvas-title` / `project-context-canvas-close-button`.
- Two NEW `ChatPage` methods needed beyond this section's own list, both
  ports of the sibling (unmerged) ELITEA-3254 family's own additions since
  this case independently needs the identical mechanisms:
  `ensure_module_toggle_checked(tool_key)` (the `project_context_builder`
  toggle shows no confirmation toast, so `click_module_toggle()`'s
  toast-wait would hang — confirmed live) and a `close_modules_panel()`
  fallback for a brand-new conversation with zero messages (its
  scroll-container anchor doesn't exist yet).
- New `api.client.ProjectContextAPI` + `project_context_api`/
  `clean_project_context` fixtures (cookie-auth only — the bearer-token
  fallback 302s to `/access_denied` on this endpoint, confirmed live) — this
  case's own `test-data` section already named these endpoints; the client
  class didn't exist yet on this branch (it lives only on the unmerged
  `tests/batch-project-context-char-limit` sibling), so it was added here
  independently rather than depending on an unmerged branch.
- Locator-debt delta (`locator_inventory.py scan`, `automation/` CWD):
  declared 1234 → 1239 (+5: 1 testid + 2 role `ScopedLocator` + 2 xpath, all
  5 new declarations hinted), non-testid-hinted 13 → 17, no-hint unchanged at
  21, unmanaged handles unchanged at 351.
- Green on DEV (project 575), 0 reruns, ~35-38s, 2 independent local runs.

## Evidence
Scratch-session screenshots (not committed — ephemeral exploration artifacts
per this skill's Evidence paths convention; cite paths, not pixels):
- Chip rendered post-create: confirmed via live DOM dump
  (`[data-testid="generated-entity-chip"]` present).
- Canvas opened via chip, showing generated content: confirmed via
  screenshot (right-panel "Project Context" heading, CodeMirror content,
  Save/Discard buttons).
- Participants panel empty post-create: confirmed via screenshot (PARTICIPANTS
  header, zero rows, Context Budget widget visible instead).
- Update flow: confirmed via screenshot (new user message, update response,
  second chip, GraphQL-mentioning editor content).
- API-level before/after `id` match: confirmed via direct `GET`
  request/response pairs (same `id`, content delta includes "GraphQL").
