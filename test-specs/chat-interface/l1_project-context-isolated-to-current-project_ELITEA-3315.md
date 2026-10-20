# Test Case: Project Context Builder receives runtime_context and creates context in current project only

## Metadata
- **TMS ID**: ELITEA-3315
- **Source case**: `.agents/automation/chat-project-context-builder/cases/ELITEA-3315.md` (snapshot)
- **Linked Story**: `EliteaAI/elitea_issues#6306`
- **Priority**: l1 (case priority: `critical` → AFS `l1_` prefix → pytest `@pytest.mark.p0`,
  same convention the sibling ELITEA-3368/ELITEA-3369 family tests already use).
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app`),
  acting project `Private` (`${ELITEA_PROJECT_ID}` = `575`), second project
  `Elitea Automation` (id `470`) — discovered live via `ProjectAPI.list_projects()`
  (the same acting-user-memberships endpoint `test_pipeline_fork_to_different_project.py`
  already uses to resolve a second project at runtime, rather than a hardcoded id).
  `scripts/dev_storage_state.py` storage state; `mcp__playwright__browser_*` tools
  unavailable in this container (no Chrome binary at `/opt/google/chrome/chrome` —
  see `.agents/memory/qa-engineer/elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`),
  so exploration used a standalone `sync_playwright` script
  (`p.chromium.launch(headless=True)`, loading the same storage-state file) —
  not committed, scratch-only, same approach the ELITEA-3368 analyst used.
- **User set**: `${TEST_USER}` (dev-token/API-login session; renders as
  `autotest_user_admin`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 6
  numbered steps + preconditions observed against the real DEV app, 2
  independent live create runs). No product defect found — the feature works
  exactly as the case's Expected Final State describes. No existing merged
  spec covers this case's own observable (cross-project isolation); see
  Coverage decision below.

## Coverage decision — why `ready-for-automation`, not `extend-existing`/`already-covered`

Searched `test-specs/` and `automation/tests/` by behaviour (project context,
chat chip, cross-project, isolation) before executing:

- `test-specs/chat-interface/l1_chat-project-context-create-update-chip-canvas_ELITEA-3368.md`
  (merged test: `automation/tests/ui/chat/test_chat_project_context_builder.py`,
  commit `c9eb89f5` — **on THIS batch's own trunk `tests/batch-chat-project-context-builder`,
  confirmed via `git merge-base --is-ancestor c9eb89f5 HEAD`, but NOT an
  ancestor of `origin/main`** (`git merge-base --is-ancestor c9eb89f5 origin/main`
  → not an ancestor)). Drives the SAME chat `project_context_builder` module
  tool and the SAME create message shape this case uses, and its own AFS
  already asserts the created context persists for the active project
  (confirmed via its own API GET). However, it **never switches projects or
  reads a second project's context** — its own Concrete Handles table
  explicitly scopes `switch_project()`/cross-project reads as untouched. The
  observable THIS case needs — that a SECOND project's context is unaffected
  by the first project's creation — is not exercised anywhere in that test.
  Because `extend-existing` may target a spec on this batch's own trunk (the
  merged-target rule, `test-case-analysis` § Classify findings), this is the
  live decision point: is the gap small enough to extend ELITEA-3368's test,
  or does it need its own test?
  - **Decided: fresh `ready-for-automation`, not `extend-existing`.** The gap
    is not "a few more assertions on the same state machine" — it is a
    structurally different flow: ELITEA-3368's test never leaves the active
    project, uses `conversation_id` (single-project) fixture wiring, and its
    own `clean_project_context`/`project_context_api` fixtures are scoped to
    exactly one project (`ELITEA_PROJECT_ID`). This case's defining action is
    switching the ACTIVE project via the sidebar selector and reading a
    SECOND project's state via a second `ProjectContextAPI` instance scoped
    to that other project id — a different precondition shape (two
    projects, not one) that ELITEA-3368's existing test body has no state
    for and would need substantially new setup/fixtures to reach, closer to
    `test_pipeline_fork_to_different_project.py`'s precondition-discovery
    pattern (a different corner of the suite entirely) than to anything in
    `test_chat_project_context_builder.py`. Per the "near-rewrite" boundary
    in `test-case-analysis` § Classify findings ("if the gap is large enough
    that the extension would be a near-rewrite… treat as ready-for-automation
    instead"), this is `ready-for-automation`.
  - This case's own Pass criteria (steps 3/4's "no clarifying question" +
    "chip present") duplicate assertions ELITEA-3368 already proves — those
    are reused as **transit** (confirmed working live, not re-derived) inside
    this case's own test, not separately asserted as new coverage.
- `test-specs/chat-interface/l1_project-context-ambiguous-request-ask-user-clarification_ELITEA-3369.md` —
  different observable entirely (an AMBIGUOUS request's clarifying-question
  flow); this case's own request is unambiguous and must NOT trigger that
  flow. Not a target.
- No spec anywhere drives a cross-project Project Context isolation check.

Conclusion: `ready-for-automation`, fresh test. Reused `ChatPage`'s existing
Modules-toggle/chip/Canvas infra (confirmed working live by ELITEA-3368) to
reach the create step fast, plus `BasePage.switch_project()` (pre-existing,
used by `ArtifactsPage`/`ChatPage` elsewhere) and `ProjectAPI.list_projects()`
(pre-existing, `test_pipeline_fork_to_different_project.py`) to discover and
switch to a genuine second project — none of which previously had this
specific isolation flow driving them, but this is new coverage, not a
duplicate.

## Preconditions
- User is logged in to `https://dev.elitea.ai` (satisfied by the dev storage
  state / API-login session).
- The acting user belongs to at least two non-public projects — confirmed
  live via `ProjectAPI.list_projects()`: `575` ("project_user_940", UI label
  "Private") and `470` ("Elitea Automation"), both with full
  `configuration`/`models` plugins. Resolved at runtime (never hardcoded —
  same precondition-discovery pattern `test_pipeline_fork_to_different_project.py`
  already establishes for a different case), since project memberships are
  not guaranteed identical across every CI matrix cell / environment.
- Project A (the active project at test start — `${ELITEA_PROJECT_ID}`, `575`)
  has no existing Project Context — enforced via API teardown (`DELETE
  /elitea_core/project_context/prompt_lib/{project_id}/project-context`,
  tolerate 404), confirmed live: `GET` returns `{"id": null, "content": "",
  "enabled": true, ...}` before the test.
- Project B (the second, non-active project — `470`) likewise starts with no
  Project Context — confirmed live via the same GET endpoint scoped to `470`
  (`{"id": null, ...}`); not independently torn down by this test (nothing in
  this case's own flow ever writes to Project B, so there is nothing to clean
  up there — see Cleanup).
- Project Context Builder is enabled in Chat Modules — **NOT ambient**, same
  per-conversation toggle finding ELITEA-3368's AFS already documents and
  `_surface.md` already caches: `default_project_context_builder_enabled:
  false` for this project, confirmed live again this session via `GET
  /api/v2/social/module_settings/{project_id}`. The test enables it
  explicitly via the Modules submenu before sending the creation message
  (AFS step 1), reusing `ChatPage.ensure_module_toggle_checked()` (already
  built for ELITEA-3368, confirmed live unchanged this session). This is a
  clarification of an under-specified precondition, not a defect — see Known
  Defects.

## Test Data

### reuse-existing
- `${TEST_USER}` — dev-token/API-login session.
- `${ELITEA_PROJECT_ID}` (`575`, "Private") — Project A, the active project
  at test start.
- Project B — discovered at runtime via `ProjectAPI.list_projects()`, same
  resolution pattern as `test_pipeline_fork_to_different_project.py`'s
  `_resolve_source_project_id()` (excludes the active project id and the
  public project id from the candidate list; this environment resolved to
  `470`, "Elitea Automation", confirmed live). **Never hardcode `470`** — a
  different CI matrix cell's acting user may have a different second
  membership; resolve by the SAME exclusion logic, not a literal id.

### generate-per-test (created via the UI action under test, cleaned up in its own teardown)
- **New conversation** — created via the `conversation_id` fixture (same
  pattern ELITEA-3368 uses), in Project A.
- Context content (create), **case's own literal Test Data message**: `"Create
  project context: This is a QA automation project using Python and
  Playwright"` (confirmed live this exact message reaches a direct creation
  response — no clarifying question — across 2 independent runs).

### API endpoints used for setup/teardown/verification (not UI, so no testid needed)
- `GET /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → `{"id": ..., "content": "...", "enabled": true, "activation_description":
  ..., "updated_at": ...}` when set, or `{"id": null, "content": "", "enabled":
  true, "activation_description": null, "updated_at": null}` when unset.
  Confirmed live for BOTH `575` and `470`: HTTP 200 either way (never 404 on
  GET — same contract ELITEA-2272's/ELITEA-3368's AFS already documented).
- `DELETE /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → HTTP 204 when a context exists; tolerate 404. Confirmed live for `575`
  this session (204 after the create flow had populated it).
- `GET /api/v2/projects/project/default/1?check_public_role=true` —
  `ProjectAPI.list_projects()`'s underlying call; confirmed live returns the
  acting user's project memberships (`id`, `name`, `owner_id`, `plugins`,
  …). This is how Project B is discovered.
- `GET /api/v2/social/module_settings/{project_id}` — confirms the
  per-project module DEFAULT; diagnostic only, not required by the test's own
  steps (same note as ELITEA-3368's AFS).

## Test Steps

1. Confirm the active project is Project A via the sidebar project selector
   (`BasePage.project_selector_trigger`, pre-existing, confirmed live reads
   `"Project: Private"` for `575`).
   - **Verify**: the trigger's text contains the Project A label (confirmed
     live: `"PProject:Private"` — the visible string concatenates a leading
     avatar-letter glyph with the label; assert via substring/contains, not
     an exact match).
2. Open a fresh conversation in Project A (`conversation_id` fixture). Open
   the `+` menu (`plus-menu-button`), hover **Modules**
   (`internal-tools-menuitem`), click the `project_context_builder` toggle
   switch (`modules-toggle-project_context_builder`,
   `ChatPage.ensure_module_toggle_checked()`) to enable it for this
   conversation, then close the submenu
   (`ChatPage.close_modules_panel()` — same submenu-interception gotcha
   ELITEA-3368's AFS/`_surface.md` already document: the panel intercepts
   pointer events on the composer underneath until explicitly dismissed).
   - **Verify**: toggle switch state element reports checked
     (`is_module_toggle_checked("project_context_builder") == True`) before
     proceeding.
3. Send the case's own literal message: `"Create project context: This is a
   QA automation project using Python and Playwright"` via the composer +
   send button.
   - **Verify**: the assistant proceeds with Project Context creation
     without asking for the project or the user explicitly — no clarifying
     question in the response text. Confirmed live 2/2 runs with this exact
     message: both produced a direct "Project context created..." response
     with the tool chips below, never an intermediate question. (This
     directly satisfies the case's own named mechanism — the backend tool
     call carries `runtime_context` with `user_id`/`project_id` already
     resolved server-side from the authenticated session, so the assistant
     never needs to ask; the ONLY externally observable proof available to
     a UI-level test is the absence of a clarifying question plus the
     content landing in the correct project in steps 4–6 below — there is
     no UI-visible representation of `runtime_context` itself to assert
     against directly, see Known Defects/Automation Hints.)
4. Wait for the AI response, then verify the Project Context chip/link
   appears in the chat response — reusing `ChatPage.generated_entity_chip`
   (pre-existing, built for ELITEA-3368, confirmed unchanged live this
   session: `[data-testid="generated-entity-chip"]`, label text
   `"Project Context"`).
   - **Verify**: `generated_entity_chip` becomes visible and its label
     contains `"Project Context"`.
5. Verify via a direct API GET (`GET
   /elitea_core/project_context/prompt_lib/{project_a_id}/project-context`,
   `ProjectContextAPI.get_project_context()`) that Project A now has
   non-empty content.
   - **Verify**: response status 200, `content` is non-empty and includes
     terms topically consistent with the prompt (case-insensitive match on
     "python" or "playwright" or "qa" — same non-determinism caveat
     ELITEA-3368's AFS documents for AI-generated content: exact wording
     varies run to run, confirmed live across both runs this session, so
     assert topical substance, never an exact string).
   - Record the returned `id` as `project_a_content_id` (used for the
     Navigate-to-Settings cross-check below).
6. Navigate to Project A's Settings → Project Context
   (`ProjectContextPage.navigate()`, pre-existing, confirmed live).
   - **Verify**: the empty-state "Create" button
     (`project-context-create-button`) is NOT shown and the editor/saved
     content (`project-context-editor-content`) IS visible and non-empty —
     confirms the created context is present and enabled in Project A's own
     Settings UI, not only via the raw API (closes the loop the same way
     ELITEA-3368's AFS step 9 does for its own update check).
7. Switch the active project to Project B via the sidebar selector
   (`BasePage.switch_project(project_b_id)`, pre-existing, confirmed live:
   the Settings → Project Context page reactively re-queries on project
   switch via `useSelectedProjectId()`/`useProjectContextQuery` — no
   explicit page reload needed, confirmed live via a before/after DOM read
   on the SAME page instance).
   - **Verify**: the sidebar trigger's text now shows Project B's label
     (confirmed live: `"EProject:Elitea Automation"`).
8. Verify Project B's Settings → Project Context.
   - **Verify**: the empty-state "Create" button
     (`project-context-create-button`) IS shown (confirmed live:
     `create_button` count 1, `editor_content` count 0) — Project B's
     context is unaffected by Project A's creation (empty, as it started —
     no prior content existed in Project B to compare against for THIS
     environment; see Known Defects item 2 for the "unchanged (empty OR
     previous content)" case-text wording).
   - **Verify** via a direct API GET scoped to Project B's id
     (`ProjectContextAPI(..., project_id=project_b_id).get_project_context()`)
     that `content == ""` and `id is None` — confirms isolation at the data
     layer too, not just the UI's empty-state rendering (closes the loop
     the same way step 6 does for Project A).

## Expected Results
- Sending the case's own literal creation message with Project Context
  Builder enabled produces a DIRECT creation response — the assistant never
  asks the user to specify a project or a user id (steps 3–4).
- The created content is present, non-empty, and enabled when viewed via
  Project A's own Settings → Project Context UI (steps 5–6).
- Project B — a DIFFERENT project the same user belongs to — remains
  completely unaffected: no content, no entity, confirmed via both its own
  Settings UI empty-state AND a direct API GET scoped to Project B's id
  (steps 7–8).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in to `{{base_url}}` | — | satisfied by storage state | n/a | asserted |
| Precondition: Project Context Builder module enabled in Chat Modules | — | AFS step 2 | `modules-toggle-project_context_builder` checked, confirmed via DOM property read | asserted *(clarified: per-conversation toggle, not an ambient project setting — same finding as ELITEA-3368, see Known Defects)* |
| Precondition: in Project A, note project name/id | — | AFS step 1 | project selector trigger text contains Project A's label | asserted |
| Precondition: Project A has no existing Project Context | — | Setup (API DELETE, tolerate 404) | precondition enforced, not case-observed | asserted |
| Precondition: user has access to ≥1 other project (Project B) | — | AFS Preconditions / Test Data | `ProjectAPI.list_projects()` resolves a real second membership at runtime | asserted |
| 1 Confirm Project A selected via project selector | Project A is selected | AFS step 1 | project selector trigger text | asserted |
| 2 Enable Project Context Builder | module toggle enabled | AFS step 2 | `is_module_toggle_checked()` returns True | asserted |
| 3 Send "Create project context: This is a QA automation project using Python and Playwright" | assistant proceeds without asking for project specification | AFS step 3 | direct creation response, no "?" / clarifying question, confirmed live 2/2 | asserted |
| 4 Verify Project Context chip/link appears in the chat response | context chip present | AFS step 4 | `generated-entity-chip` visible, label "Project Context" | asserted |
| 5 Navigate to Project A's Settings > Project Context | created context content present and enabled | AFS steps 5–6 | step 5: API GET non-empty content; step 6: Settings UI shows editor content, not empty-state | asserted *(decomposed: step 5 is the API-level proof, step 6 the UI-level proof — mirrors ELITEA-3368's own API+UI cross-check pattern)* |
| 6 Navigate to Project B's Settings > Project Context | Project B's context unchanged (empty or previous content) | AFS steps 7–8 | step 7: project switch confirmed via selector text; step 8: empty-state Create button shown + API GET confirms `content==""`/`id is None` | asserted *(this environment's Project B started empty, so "unchanged" is observed as "still empty" — see Known Defects item 2 for the case-text's "or previous content" branch, not independently exercised this session)* |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 5 adds a direct API GET of Project A's content (not just the chat
  chip's presence) — *added: proves the context actually PERSISTED server-side
  in the correct project, not merely that a chip rendered in the chat UI,
  which is the case's own Expected Final State ("creates the context in the
  correct project") stated as a verifiable assertion rather than left
  implicit.*
- Step 6 adds a Settings-UI-level read of Project A's content (on top of the
  step-5 API read) — *added: closes the loop so the test doesn't only prove
  the API was updated while never checking the UI surface the case's own
  step 5 explicitly names ("Navigate to Project A's Settings > Project
  Context"), matching this suite's established API-response ⇄ UI cross-check
  pattern (e.g. ELITEA-3368's own step 9, ELITEA-2085's step 7).*
- Step 8 adds a direct API GET scoped to Project B's own id (on top of the
  case's own UI-navigation step) — *added: the case's Pass criterion is
  "other projects' context is unaffected", and a UI empty-state alone could
  theoretically be stale/cached; an independent API read scoped to Project
  B's id proves isolation at the data layer, which is the strongest
  available proof against a hypothetical cross-project data leak.*
- Side-channel console-error check folded into every step (not in the
  case's own text) — *added: standard practice on this surface, confirmed
  clean across both runs this session.*

## Cleanup
1. `DELETE /elitea_core/project_context/prompt_lib/{project_a_id}/project-context`
   (best-effort, tolerate 404) — restores Project A's empty-state
   precondition for the next run. Confirmed live: returns 204 when content
   exists.
2. `DELETE /elitea_core/conversation/prompt_lib/{project_a_id}/{conversation_id}`
   — the conversation created in step 2, via the `conversation_id` fixture's
   own existing teardown (no new cleanup code needed).
3. **No teardown needed for Project B** — this case's own flow never writes
   to Project B (that is the entire point of the isolation assertion); its
   state is read-only verified, never mutated. If a future case variant adds
   a Project-B-side create step, it would need its own `ProjectContextAPI`
   instance scoped to Project B's id and its own cleanup — not needed here.
4. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data
   Lifecycle; project is switched back to Project A at the end of the test
   (or left on Project B — declare the choice; either is safe since no
   OTHER test in this suite depends on the active project persisting across
   test boundaries — see Automation Hints).

## Concrete Handles (discovered during exploration — DEV, ladder provenance)

| Element | Rung | Handle | Provenance | Notes |
|---|---|---|---|---|
| Project selector trigger (sidebar) | 1 (testid) | `project-selector-trigger-combobox` | pre-existing, confirmed live | `BasePage.project_selector_trigger` (existing) |
| Project selector dropdown option (dynamic) | 1 (testid, dynamic) | `[data-testid="select-option-{project_id}"]` | pre-existing, confirmed live for both `575` and `470` | `BasePage.SELECT_OPTION` template (existing); used internally by `BasePage.switch_project()` |
| `+` menu button | 1 (testid) | `plus-menu-button` | pre-existing, confirmed live | `ChatPage.plus_menu_button` |
| Modules submenu toggle (Project Context Builder) | 1 (testid) | `modules-toggle-project_context_builder` | pre-existing on DEV, confirmed live | `ChatPage.MODULE_TOGGLE_ORDER`; `ensure_module_toggle_checked()` |
| Message composer | 1 (testid) | `chat-message-input` | pre-existing, confirmed live | `ChatPage.message_input` |
| Send button | 1 (testid) | `chat-send-button` | pre-existing | `ChatPage.send_button` |
| Tool-invocation chip | 1 (testid) | `chat-answer-tool-chip` | pre-existing, confirmed live for `post_elitea_core_generate_project_context_draft` and `put_project_context_project-context` | `ChatPage.answer_tool_chip` |
| Generated-entity chip (create response) | 1 (testid) | `generated-entity-chip` | pre-existing (added for ELITEA-3368, on THIS batch's trunk), confirmed live unchanged this session | `ChatPage.generated_entity_chip` |
| Settings → Project Context empty-state "Create" button | 1 (testid) | `project-context-create-button` | pre-existing (ELITEA-2272), confirmed live on Project B (empty) | `ProjectContextPage.create_button` |
| Settings → Project Context editor content | 1 (testid) | `project-context-editor-content` | pre-existing (ELITEA-2272), confirmed live on Project A (has content) | `ProjectContextPage.editor_content` |

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- The "enabled" toggle switch at the top of the Settings → Project Context
  saved view (`EnableToggleCard.jsx`'s `Switch.BaseSwitch`, confirmed live
  via source read it carries no `data-testid`/`aria-label`/`name` attribute
  of any kind — `role="switch"` only) — this case's "enabled" wording (case
  step 5's "content is present and enabled") is satisfied by the API's own
  `enabled: true` field (asserted in step 5), not by reading this UI
  control; no case step clicks or reads it directly. Flag for a future case
  that specifically tests the enable/disable toggle — not this one.
- The chip's hover-revealed "Open entity"/"Delete entity" buttons and the
  in-chat Canvas chrome (`ProjectContextChatCanvasPage`) — this case never
  opens the Canvas; it verifies via the Settings page and the API directly
  (case steps 5–6 name "Settings > Project Context", not the chat Canvas).
- Project B's own chat/Modules UI — this case never sends a message in
  Project B.

## Network Behavior
- `GET /api/v2/projects/project/default/1?check_public_role=true` —
  `ProjectAPI.list_projects()`'s request; 200, returns the acting user's
  project memberships (confirmed live: 3 entries this session — `1`
  "promptlib_public", `470` "Elitea Automation", `575`
  "project_user_940").
- `POST /api/v2/elitea_core/generate_project_context_draft/prompt_lib/{project_a_id}`
  — fires on the create message (same endpoint ELITEA-3368's AFS already
  documents; inferred from the tool-chip name, not independently confirmed
  via a raw network-tab capture this session either — same caveat).
- `PUT /elitea_core/project_context/prompt_lib/{project_a_id}/project-context`
  — fires as part of the create path (confirmed live via the direct API GET
  showing non-empty content immediately after the create message, same
  single-call generate-and-save shape ELITEA-3368's AFS documents).
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — scoped independently to EACH project id (`575` and `470`) by this case's
  own steps 5 and 8 — this is the mechanism that proves isolation: two
  separate requests to two separate project-scoped URLs, never a single
  shared endpoint that could leak state between them.
- No request observed that writes to Project B at any point in this flow —
  confirmed by the absence of any `PUT`/`POST` to a `.../prompt_lib/470/...`
  path across the full session (only `GET`s against `470` were ever issued,
  both by this exploration script and, implicitly, by the Settings page's
  own `useProjectContextQuery` after the project switch).

## Known Defects Found During Exploration
None — no product defect found; the feature works exactly as the case's
Expected Final State describes. Two CLARIFICATIONS (case-text drift, not
bugs — reverse-masking guard applies, same pattern already established by
ELITEA-3368's sibling AFS):

1. **Precondition "Project Context Builder module is enabled in Chat
   Modules" is per-conversation, not an ambient project setting.** Identical
   finding to ELITEA-3368's AFS (confirmed live again this session via `GET
   /api/v2/social/module_settings/{project_id}` → `default_project_context_builder_enabled:
   false`). Not filed as a new tracker issue — ELITEA-3368's own analysis
   already recorded this exact clarification for this exact module toggle;
   filing a second ticket for the identical finding would duplicate it. Noted
   here only so this case's own implementer doesn't have to rediscover it
   independently.
2. **The case's step 6 "Project B's context is unchanged (empty or previous
   content)" names TWO possible starting states, but this environment's
   Project B happened to start empty (confirmed live via API GET before this
   session's own create flow ran)** — so only the "empty" branch was
   independently exercised this session; the "previous content" branch
   (Project B already had some pre-existing Project Context before this
   test runs, and it stays exactly as it was) is logically the same
   assertion (content before == content after) and is NOT a separate code
   path in the product (no project-pairing special-case exists in
   `ProjectContextContent.jsx`/`useProjectContextQuery` — confirmed via
   source read: the hook is keyed purely by `projectId`, with zero
   cross-project awareness of any kind). Not a defect or even really a
   clarification needing a ticket — just noting for the implementer that a
   literal "seed Project B with pre-existing content first" setup variant
   would exercise the identical assertion shape (`before == after`) with
   different starting data, and is not required to prove isolation (the
   stronger case — a shared endpoint/handler that could theoretically leak
   state between projects — is already disproven by step 8's two
   independent, project-scoped API reads either way).
3. **The case's own named mechanism ("Project Context Builder automatically
   receives `runtime_context` containing `user_id` and `project_id`") has no
   UI-visible representation to assert directly** — there is no DOM element,
   response field, or console log that surfaces the literal string
   `runtime_context` or echoes back the resolved `user_id`/`project_id` to
   the client (confirmed via the WebSocket trace and the create/GET response
   bodies this session: neither carries any `runtime_context`-named key).
   This is not a gap in the product, just a statement about test design: the
   case's named INTERNAL mechanism is validated the only way a UI/API-level
   test can validate it — by its EXTERNAL, observable consequences (no
   clarifying question asked in step 3, correct-project isolation in steps
   5–8) — never by asserting on the mechanism's name directly. Not filed as
   a clarification; this is a normal black-box-testing boundary, not case-text
   drift or a product gap.

## Blocked Steps
None. All 6 case steps + preconditions were executed and observed live,
across 2 independent live create runs plus the cross-project switch/read
sequence (steps 7–8) run twice to confirm it is not a one-off cache artifact.

## Automation Hints
- Framework: Playwright + pytest, ladder locators (`.agents/testing.md`).
- **Compose, don't rewrite**: reuse `ChatPage` (conversation creation,
  Modules toggle, send/receive, generated-entity-chip — all confirmed
  working live, built for ELITEA-3368, present on this batch's own trunk)
  for steps 2–4, and `ProjectContextPage` (Settings → Project Context
  editor/create-button — ELITEA-2272) for steps 6/8, on the SAME `page`
  object across the project switch in step 7.
- **Project B discovery**: port `test_pipeline_fork_to_different_project.py`'s
  `_resolve_source_project_id()` pattern (module-level helper function,
  `ProjectAPI(browser_cookies=...).list_projects()`, excludes the active
  project id and `settings.public_project_id` from candidates, fails loudly
  via `pytest.fail()` rather than skipping if no second membership exists —
  same "never silently drop coverage" reasoning that helper's own docstring
  gives). Do NOT hardcode `470` — resolve by exclusion logic, confirmed live
  this environment resolves to `470` ("Elitea Automation") but a different
  CI matrix cell's acting user may have a different second membership.
- **Second-project API verification**: instantiate a SECOND
  `ProjectContextAPI` scoped to the discovered Project B id
  (`ProjectContextAPI(browser_cookies=_browser_cookies, project_id=str(project_b_id))`
  — the class already accepts an explicit `project_id` override, confirmed
  via its own `__init__` signature) rather than mutating the shared
  session-scoped `project_context_api` fixture's project id — the shared
  fixture stays scoped to `ELITEA_PROJECT_ID`/Project A throughout, exactly
  as every other test using it expects.
- **Project-switch verification**: `BasePage.switch_project(project_id)` is
  pre-existing and used elsewhere (`ArtifactsPage`'s Team-project tests) —
  reuse directly, don't re-derive. Confirmed live this session: the Settings
  → Project Context page re-queries reactively on switch (RTK Query hook
  keyed by `useSelectedProjectId()`) with NO explicit page reload/re-navigate
  needed — the SAME `page` instance's `editor_content`/`create_button`
  locators correctly reflect the new project's state immediately after
  `switch_project()` returns (confirmed via a before/after read on the
  identical page without an intervening `page.goto()`).
- **Wait strategy**: no fixed sleeps. Use `wait_for_ai_response()`-style
  condition waits for the create message (observed live: 8-12s per
  response, tool-call-plus-generation, consistent with ELITEA-3368's
  documented 9-20s range); wait for `generated_entity_chip` to become
  visible before reading its label (not present during streaming — same
  gating ELITEA-3368's AFS documents).
- **Non-determinism**: the AI's exact generated content varies run to run
  (confirmed live: 2 runs of the identical create prompt produced
  differently-worded "Project context created..." responses, both topically
  faithful to "QA automation project using Python and Playwright"). Never
  assert exact generated text — assert non-empty + topical keyword presence
  (case-insensitive "python"/"playwright"/"qa"), matching ELITEA-3368's own
  established pattern for this exact tool/content.
- **Test independence across the active-project switch**: this test leaves
  the active project on whichever one it ends on (declare the choice in the
  implementation — either switching back to Project A at the very end, or
  leaving it on Project B, is safe) — no OTHER test in this suite reads the
  active project as ambient state across test boundaries (every other test
  either doesn't care, or explicitly switches/asserts its own project via
  its own fixtures); confirmed by grep (`grep -rn "elitea_project_id"
  automation/tests/` — no test reads a *persisted* active-project value from
  a previous test). If this changes in the future (a shared project-scoped
  fixture gets added), this test's own `switch_project()` calls would need
  revisiting — not a concern on this build.
- No sanctioned-RED / known-defect handling needed — this case's happy path
  is fully clean across every run this session.

## Evidence
Scratch-session screenshots (not committed — ephemeral exploration artifacts
per this skill's Evidence paths convention; cite paths, not pixels):
- Project A Settings → Project Context showing created content:
  `/tmp/scratch_explore/03_settings_project_a.png` (headings "Project
  Overview"/"Testing Scope"/"Development Practices", enabled toggle visible
  — not from THIS case's own create message, from a prior scratch run using
  a different prompt; re-confirmed with THIS case's own exact message in a
  later run, chip + API GET only, no re-screenshot taken).
- Project B Settings → Project Context showing the empty-state ("Still no
  Project Context", "Create"/"Build with AI" buttons):
  `/tmp/scratch_explore/04_settings_project_b.png`.
- Project-switch-without-reload confirmation:
  `/tmp/scratch_explore/06_switch_no_reload.png` (Project B empty-state
  rendered on the SAME page instance immediately after `switch_project()`,
  no intervening navigation).
- API-level before/after `id`/`content` reads: confirmed via direct
  `GET`/`DELETE` request/response pairs captured in the scratch script's
  stdout (Project A: `id: 84`→populated after create; Project B: `id: null`
  throughout, unaffected).
