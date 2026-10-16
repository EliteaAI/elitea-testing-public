# Test Case: Project Context 2500-Character Limit Enforced Across Create/Edit/Chat Surfaces (Family)

## Metadata
- **TMS ID (family)**: ELITEA-3252, ELITEA-3253, ELITEA-3254, ELITEA-3255 —
  `family_afs: true`, this file is the single AFS for all four cases (parameter
  table below has one row per case).
- **Linked Story**: `EliteaAI/elitea_issues#6344` (all four cases' `requirements`
  frontmatter)
- **Priority**: l1 (critical — all four cases declare `priority: critical` in
  frontmatter; maps to `l1` per this project's established TMS→AFS priority
  mapping, confirmed against sibling `l1_*` AFS files e.g. ELITEA-1962,
  ELITEA-1870/1869; pytest marker `@pytest.mark.p0`)
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app`,
  project "Private" — API project id `575`). Playwright MCP server has no
  Chrome binary in this container (known gap, see qa-engineer memory
  `elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`) — a
  direct `sync_playwright` scratch script was used instead
  (`p.chromium.launch(headless=True)`, context `storage_state` loaded from
  `.playwright-mcp/dev-storage-state.json`). All four flows driven live, no
  synthesized input.
- **User set**: `${TEST_USER}` (DEV, `auth_state` logs in via the API —
  storage state refreshed via `scripts/dev_storage_state.py` this session)
- **Analyst**: qa-engineer (Sage), analyst slot (cluster dispatch, one live
  session for all four cases)
- **Status**: **ready-for-automation** — all four cases executed end-to-end
  live against DEV, all handles captured, no blockers, no defects. One
  behavior **not described by any of the four cases' step text** was
  discovered and is recorded in § Known Defects Found During Exploration as a
  CLARIFICATION (not a product bug) — see that section.

## Family classification rationale

Per `test-case-analysis` § 3 "differ only in DATA vs. differ in STEPS": the
four cases are **not** a single parameterized flow in the strict sense (each
touches a materially different entry point — Settings "Build with AI" from
empty state, Settings "Build with AI" with a verbose prompt, Chat's
`project_context_builder` module tool, Settings "Edit with AI" on existing
content) and are written here as a family **by dispatch grouping**, not
because they collapse into one parameterized test. Each case keeps its own
numbered steps below (Axis 1 Coverage Map is per-case) because the actions
differ: ELITEA-3252 and ELITEA-3253 share the same entry point (Settings →
"Build with AI") but diverge immediately — one asserts a short-prompt success
path, the other asserts a long-prompt 422-error path, with different final UI
states (saved content vs. untouched empty state + preserved prompt). ELITEA-
3254 is a different surface entirely (Chat, not Settings). ELITEA-3255 starts
from a *populated* Project Context (not empty) and uses "Edit with AI", a
third distinct entry point. All four share one object under test (the project
context's 2500-char server-side limit, enforced identically wherever content
is submitted) and one page object/API surface, which is why they are analysed
together and will land as one implementation unit (one new page object +
helper methods on `ChatPage` for the module toggle), but the AFS below gives
each its own Test Steps / Coverage Map so the implementer writes 4 independent
test methods (parameterizing only the parts that are genuinely identical, if
any, at implementation time) rather than one artificially unified flow.

## Preconditions (shared)
- User is logged in with Editor or Admin role (`${TEST_USER}` on DEV, API-based
  `auth_state`).
- Project Context toggle is enabled — **confirmed live: there is no longer a
  separate "toggle" UI element to enable.** The feature's "enabled" state is
  implicit in whether a Project Context row exists; `enabled: true` is always
  sent in the PUT body by the editor and is NOT a separately exposed switch on
  Settings → Project Context. (All four cases' Preconditions text says
  "Project Context toggle is enabled" — this is case-text drift against the
  current build; see § Known Defects Found During Exploration below, filed as
  a CLARIFICATION, not re-automated as a toggle step.)
- Feature is gated off for the "Public" project (confirmed inherited from
  `l2_project-context-character-limit-2500_ELITEA-2272.md`'s precondition —
  not independently re-verified this session, carried forward); run against a
  non-Public project (`${ELITEA_PROJECT_ID}` on DEV, API project id `575`).
- `MAX_CHARS` = 2500, confirmed live via the error payload
  (`"String should have at most 2500 characters"`, `ctx.max_length: 2500`) and
  the character counters observed throughout — same constant
  `l2_project-context-character-limit-2500_ELITEA-2272.md` already documents.

## Test Data

### Parameter table (one row per source TMS case)

| # | Case | Entry point | Input | Expected outcome |
|---|---|---|---|---|
| 1 | ELITEA-3252 | Settings → empty state → "Build with AI" | Short project description (~90 chars) | Draft generated ≤2500 chars, Apply succeeds, Save succeeds |
| 2 | ELITEA-3253 | Settings → empty state → "Build with AI" | Long/verbose project description (healthcare platform prompt, 834 chars, confirmed live to produce a ~4300-char draft) | HTTP 422, specific error message, prompt preserved, no content saved |
| 3 | ELITEA-3254 | Chat, `project_context_builder` module tool | Chat message asking the AI to generate+save a project context, with a project description in the same message (confirmed live: the tool needs a description in-message, not just "generate a project context for this project" alone — see Known Defects/Clarifications) | Tool invokes `put_project_context`, content ≤2500 chars saved, visible in both Chat and Settings |
| 4 | ELITEA-3255 | Settings → populated Project Context → "Edit with AI" | Existing ~1380-char content + edit instruction "Add one short sentence about security." | Edited draft ≤2500 chars, Apply & Save succeeds |

### reuse-existing
- `${ELITEA_PROJECT_ID}` = DEV API project id `575` ("Private" project,
  confirmed via `GET .../project_context/prompt_lib/575/project-context`
  returning 200 both when empty and when populated)

### generate-per-test (in test setup, cleaned up in its own teardown)
- Project Context content strings (short filler text for #1/#4's starting
  content, the long healthcare-platform prompt for #2, the chat message for
  #3) — entered through the UI/chat under test, not server-seeded.
- API endpoints used for setup/teardown (same base path as ELITEA-2272, this
  session confirmed the response shape has grown two new fields):
  - `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
    → `{"id", "content", "enabled", "activation_description", "updated_at"}`.
    **New since ELITEA-2272's AFS**: `activation_description` field (was not
    present then). Empty state: `{"id": null, "content": "", "enabled": true,
    "activation_description": null, "updated_at": null}` — confirmed live,
    always 200.
  - `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
    → 204 when a context exists (ELITEA-2272's AFS says 200 with a 404-on-empty
    variant; this session observed **204** on successful delete, not 200 —
    re-verify at implementation time, both are "success" status codes so this
    doesn't change the teardown's tolerate-404 contract, just note the exact
    code if asserting on it).
  - `POST /elitea_core/generate_project_context_draft/prompt_lib/{project_id}`
    — fires on "Generate Draft" (Settings Build-with-AI) and "Generate" (Settings
    Edit-with-AI). Body: `{"prompt": "..."}` (Build-with-AI, create flow) or
    equivalent edit-instruction body (Edit-with-AI flow — not independently
    captured, confirmed to fire via network log only). 200 + draft payload on
    success; **422** on limit violation with the body shape captured in
    § Network Behavior below.
  - `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
    — fires on Save (Settings) and is invoked directly by the chat tool
    (`put_project_context`) for case #3. Body includes at minimum `content`
    and `enabled`; the editor's Save additionally requires a non-empty
    `activation_description` (see Concrete Handles — this is a NEW
    Save-enablement condition not present in ELITEA-2272's AFS/page object).

## Test Steps

### ELITEA-3252 — Settings: Generate Project Context produces content ≤2500 characters

1. Precondition: `DELETE` the project's Project Context via API (tolerate
   404/204 — "already clean" is a pass).
2. Navigate to `${BASE_URL}/settings/project-context`.
   - **Verify**: empty-state "Build with AI" button is visible (confirmed
     live, no testid yet — see Concrete Handles) alongside "Create".
3. Click "Build with AI".
   - **Verify**: a dialog opens with a textarea (placeholder "Describe your
     project: architecture, design decisions, workflows, terminology,
     constraints, coding standards, deployment process, or other important
     information.") and a "Generate Draft" button, initially disabled.
4. Fill the textarea with a short project description (confirmed live with:
   `"A simple test automation project for a web app with login, dashboard,
   and settings pages."`, 90 chars) and click "Generate Draft".
   - **Verify**: `POST generate_project_context_draft` fires and returns 200.
5. Wait for generation to complete (confirmed live: ~5-8s).
   - **Verify**: the dialog transitions to a review step showing an editable
     "Project Background" textarea pre-filled with the generated draft, and
     an "Apply" button.
6. Read the draft textarea's content length.
   - **Verify**: length ≤ 2500 (confirmed live: 1685 chars for the short
     prompt above — well under the limit; this case's pass bar is the
     inequality, not a specific number, since generation is non-deterministic).
   - **Verify**: content is coherent markdown (headed sections), not
     truncated mid-sentence (confirmed live by reading the full text).
7. Click "Apply".
   - **Verify**: dialog closes, draft content now populates the main editor
     (`project-context-editor-content`), character counter reflects the
     applied length.
8. Fill the (new) "Activation description" input (testid
   `project-context-activation-description`) — required for Save to enable
   (see Concrete Handles; not in the case's own steps, added because without
   it Save never becomes clickable on this build — see § Analyst additions).
9. Click Save.
   - **Verify**: success toast, URL reverts to the non-`?view=` saved path.
10. (Teardown) `DELETE` the Project Context via API.

### ELITEA-3253 — Settings: Generate Project Context shows error when output would exceed 2500 characters

1. Precondition: `DELETE` the project's Project Context via API.
2. Navigate to `${BASE_URL}/settings/project-context`.
3. Click "Build with AI".
4. Fill the textarea with the Test Data's complex healthcare-platform prompt
   (834 chars, see Parameter table) and click "Generate Draft".
   - **Verify**: `POST generate_project_context_draft` fires and returns
     **422** (confirmed live, reproducible: 2 separate runs returned 422 with
     the generated draft at 4303 and 4423 chars respectively — generation is
     non-deterministic in length but reliably exceeds 2500 for this prompt).
5. Observe the result.
   - **Verify**: an inline error alert (MUI `Alert` role, `color="error"`) is
     displayed inside the dialog with the exact text pattern confirmed live:
     `"Project background is {N} characters, the maximum is 2500. Try
     generating again, or ask for a narrower scope."` where `{N}` is the
     actual generated length (4303/4423/5253/2638 observed across runs — the
     case's own expected text uses the literal number as an *example*
     ("e.g. 5893"), not a fixed value; assert the pattern, not a specific N).
6. Verify the original prompt remains in the textarea.
   - **Verify**: textarea's `input_value()` still equals the originally-typed
     prompt verbatim (confirmed live, exact match, length 834).
7. Verify no partial/truncated content was saved.
   - **Verify**: `GET` the project's Project Context via API — `content` is
     still `""` / `id` still `null` (unchanged from precondition — confirmed
     live, no PUT fires on a 422).
8. (Teardown) `DELETE` the Project Context via API (best-effort — expected to
   already be clean per step 7).

### ELITEA-3254 — Chat: Project Context Builder tool generates content ≤2500 characters

1. Precondition: `DELETE` the project's Project Context via API.
2. Navigate to `${BASE_URL}/chat`, click "+Chat"/create-conversation (testid
   `sidebar-create-button`) for a fresh conversation.
3. Open the plus-menu (`plus-menu-button`) → hover "Modules" → ensure the
   `project_context_builder` module toggle (testid template
   `modules-toggle-project_context_builder`, see `ChatPage.MODULE_TOGGLE_ORDER`)
   is checked; toggle it on if not.
   - **Verify**: switch `is_checked()` is true after the click (confirmed
     live, no confirmation toast observed for this specific toggle unlike
     `click_module_toggle()`'s documented pattern for other modules — do not
     assume the toast; poll the checked state instead, or extend
     `click_module_toggle()`/add a dedicated wait if this diverges — flag at
     implementation time if the toast IS present but wasn't surfaced in this
     session's capture).
   - Close the Modules panel via the documented outside-click pattern
     (`ChatPage.close_modules_panel()` — center-click is unreliable, use the
     scroll container's top-left corner per that method's own docstring).
4. Send a chat message asking the AI to generate+save a project context
   **with a project description included in the same message** (confirmed
   live: `"Generate a project context for this project"` alone, with no
   description, makes the AI ask a clarifying follow-up instead of invoking
   the tool — this is a case-text gap, not a defect; see § Known Defects).
   Message used live: `"Generate and save a project context for this
   project. It is a Playwright/pytest test automation suite for the Elitea
   AI platform, covering chat, agents, pipelines, skills, toolkits, and
   settings UI flows against a deployed DEV environment."`
   - **Verify**: AI response shows a tool-invocation chip/label — confirmed
     live text pattern `"Elitea Project Context: put_project_context_project-context"`
     (via `wait_for_ai_response()`).
5. Wait for generation to complete.
   - **Verify**: `GET /elitea_core/project_context/prompt_lib/575/project-context`
     (fired by the chat tool's own flow or by a follow-up poll) returns
     `content` with length ≤2500 (confirmed live: 2218 chars for the message
     above).
6. Navigate to `${BASE_URL}/settings/project-context` to verify.
   - **Verify**: the saved view renders the same content (confirmed live:
     "Still no Project Context" empty-state text is NOT present; the
     generated markdown headings — e.g. "Project Overview" — ARE present).
7. (Teardown) `DELETE` the Project Context via API.

### ELITEA-3255 — Settings: Edit with AI respects 2500-character limit

1. Precondition: ensure Project Context exists with ~1500 characters of
   content (confirmed live with repeated filler text, 1380 chars via
   `keyboard.type()`, plus a required `activation_description` value — see
   Concrete Handles) — create it via the UI create flow + Save (not server
   seeded, matching the case's own "existing content" precondition, which is
   itself produced through the UI action under test per the project's test
   data strategy).
2. Navigate to `${BASE_URL}/settings/project-context`.
   - **Verify**: saved view renders with existing content, and an "Edit with
     AI" button (testid `ai-edit-project-context-open-button`) is directly
     visible on the saved view **without** first clicking a separate "Edit"
     button (confirmed live — "Edit" and "Edit with AI" are two independent,
     adjacent buttons on the saved view toolbar; the case's step 2 "Click
     'Edit' to enter edit mode" then step 3 "Click 'Edit with AI'" describes
     an older/alternate path — "Edit with AI" opens its own modal directly
     from the saved view and does not require entering plain "Edit" mode
     first. See § Known Defects — case-text drift, not a defect).
3. Click "Edit with AI" (`ai-edit-project-context-open-button`).
   - **Verify**: a modal opens (testid `ai-edit-project-context-modal`) with
     a prompt input (testid `ai-edit-project-context-prompt-input`) and a
     "Generate Draft" button (testid `ai-edit-project-context-generate-button`).
4. Enter the edit instruction (`"Expand this context with more details about
   integrations and security"` per the case's own Test Data) and click
   Generate Draft (confirmed `is_disabled()` false once the prompt has text).
5. Wait for the AI-edited content to appear.
   - **Verify**: `POST generate_project_context_draft` returns 200 (not 422 —
     this specific instruction, applied to the ~1380-char base, stayed under
     the limit: confirmed live, result editor showed "1033 characters left"
     i.e. new length ≈1467).
6. Verify the edited content length.
   - **Verify**: length ≤2500 (confirmed live, well under at ≈1467 — the
     case's own Test Data assumes a base of ~1500 chars, consistent with this
     session's 1380-char base).
   - Click "Apply & Save" (confirmed live label — not a separate Apply-then-
     Save-click as in the create flow; this surface's modal applies and
     saves together).
   - **Verify**: success toast, modal closes, saved view shows updated content.
7. (Teardown) `DELETE` the Project Context via API.

## Expected Results (shared)
- Across all four surfaces (Settings create, Settings create-with-overflow,
  Chat tool, Settings edit), generated/edited content delivered to the user
  never exceeds 2500 characters.
- When generation WOULD exceed the limit (ELITEA-3253), the server rejects it
  (HTTP 422) with a specific, actionable error message, the original prompt is
  preserved for editing, and no content is saved.
- No console errors at any step (confirmed live for all four flows — only the
  expected 422 network-level error for ELITEA-3253, no uncaught JS exception).

## Coverage Map

### Axis 1 — Case coverage (one block per case, same table shape as spec-format.md)

**ELITEA-3252**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Project Context | page loads | step 2 | empty-state visible | asserted |
| 2 Enable the Project Context toggle if not already enabled | toggle ON, Edit/Edit-with-AI active | — | — | out-of-scope *(no such toggle exists on this build — see Known Defects; feature's "enabled" is implicit, not a separate switch)* |
| 3 Click "Edit with AI" or "Build with AI" | generation dialog opens | step 3 | dialog + textarea visible | asserted *(case names either button; this AFS exercises "Build with AI", the empty-state entry point; "Edit with AI" from a populated state is ELITEA-3255's own path)* |
| 4 Provide description, trigger generation | AI begins generating | steps 4–5 | 200 response + review step shown | asserted |
| 5 Wait for generation | content appears | step 5 | review step with pre-filled draft | asserted |
| 6 Check character count | ≤2500, displayed | step 6 | draft textarea length read | asserted |
| desc/Pass: content complete, not truncated mid-sentence | coherent content | step 6 | manual read of full draft text | asserted |

**ELITEA-3253**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Project Context | page loads | step 2 | empty-state visible | asserted |
| 2 Enable toggle | toggle ON | — | — | out-of-scope *(same as ELITEA-3252 — no such toggle)* |
| 3 Click "Edit with AI" | dialog opens | step 3 | dialog visible | asserted *(exercises "Build with AI" — same empty-state-only button as 3252; case says "Edit with AI" but that button isn't present in the empty state, only "Build with AI" is — see Known Defects)* |
| 4 Enter complex prompt | prompt entered | step 4 | textarea filled, verified via a later `input_value()` read | asserted |
| 5 Click Generate Draft | system attempts generation | step 4 | POST fires | asserted |
| 6 Observe result | exact error string shown | step 5 | inline Alert text matched against the pattern | asserted |
| 7 Verify prompt preserved | prompt unchanged, editable | step 6 | `input_value()` equality | asserted |
| 8 Verify no partial content saved | Project Context field unchanged | step 7 | API GET still empty | asserted |

**ELITEA-3254**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open Chat in a project with multiple components | chat loads | step 2 | new conversation created | asserted *(did not independently verify "multiple components" exist — see Axis 2)* |
| 2 Ensure Project Context Builder enabled in settings | module active | step 3 | toggle `is_checked()` true | asserted |
| 3 Ask AI to generate/create project context via chat | AI invokes `generate_project_context_draft` tool | step 4 | tool-invocation chip text matched | asserted *(case names the tool `generate_project_context_draft`; live tool-chip name observed is `put_project_context` — see Known Defects, case-text naming drift, not a behavior defect: content IS generated and saved)* |
| 4 Wait for generation | AI produces project context | step 4–5 | chat response + API GET | asserted |
| 5 Verify generated content length | ≤2500 | step 5 | API GET content length | asserted |
| 6 Navigate to Settings to verify | content appears, respects limit | step 6 | Settings saved view shows content | asserted |

**ELITEA-3255**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Project Context | page loads with existing content | step 2 | saved view with content visible | asserted |
| 2 Click "Edit" to enter edit mode | edit mode activated | — | — | out-of-scope *("Edit with AI" is reached directly from the saved view without a separate "Edit" step on this build — see Known Defects, case-text drift)* |
| 3 Click "Edit with AI" | AI editing interface opens | step 3 | modal with prompt input visible | asserted |
| 4 Provide expand/modify instructions | AI processes edit request | step 4 | Generate Draft click | asserted |
| 5 Wait for edited content | content displayed | step 5 | 200 response, review step | asserted |
| 6 Verify edited content length | ≤2500 | step 6 | "N characters left" counter / length read | asserted |

### Axis 2 — Analyst additions

- All four: asserted **no console error** throughout each flow — *added:
  silent truncation/rejection paths are exactly the kind of interaction that
  can throw uncaught exceptions without visibly breaking the UI (same
  rationale as ELITEA-2272's AFS); confirmed none on any of the four live
  runs.*
- ELITEA-3252 step 8 (fill Activation description before Save): *added — not
  in the case's own steps. Confirmed live this build's Save button requires
  BOTH non-empty editor content AND a non-empty activation-description value
  to enable (`isDirty` is no longer sufficient alone, diverging from
  ELITEA-2272's documented "Save gated purely on isDirty" finding — that
  finding is now STALE for the create flow; re-verify at implementation time
  whether ELITEA-2272's own test still passes, since this is a shared editor
  component). Without this step the case cannot reach a clickable Save at
  all.*
- ELITEA-3253 step 7 (API-level "no partial content saved" check): the
  case's own step 8 says this in UI terms ("Project Context field is
  unchanged"); this AFS asserts it via the API GET directly, which is a
  strictly stronger check that also back-stops a future UI-only read that
  might mask a stale cache — *added for determinism.*
- ELITEA-3254: did not independently verify the precondition "Project exists
  with various assets (agents, pipelines, skills)" — the test project (DEV
  id 575, "Private") was used as-is without confirming it has multiple
  component types. *Flagged, not blocking*: the tool's own output in this
  session only referenced generic test-automation concepts from the chat
  message content, not any specific agent/pipeline/skill name, so the
  precondition's role (giving the AI real assets to describe) wasn't
  exercised either way live. If the implementer's run shows the same
  generic-content behavior, this precondition can be dropped from the
  automated test without losing coverage of the actual pass bar (≤2500 chars).

## Cleanup
1. `DELETE /elitea_core/project_context/prompt_lib/{ELITEA_PROJECT_ID}/project-context`
   (best-effort — tolerate 404/204 either way) before AND after each of the
   four tests, so each run is idempotent (same pattern as ELITEA-2272).

## Concrete Handles (discovered during exploration)

All testids below were newly observed live on DEV during this session — the
feature has grown substantially since ELITEA-2272's analysis (2026-08-05):
several NEW testids now exist that did not before, and the Save-enablement
condition has changed (see Axis 2 above). `ProjectContextPage` (existing,
`automation/pages/project_context_page.py`) needs extending, not rewriting.

| Element | Testid (rung 1 — confirmed on DEV) | Notes |
|---|---|---|
| Empty-state "Create" button | `project-context-create-button` | unchanged from ELITEA-2272 |
| CodeMirror editor content | `project-context-editor-content` | unchanged |
| Save button (editor) | `project-context-save-button` | **behavior changed**: now also requires `activation_description` non-empty (see Axis 2) |
| Character counter | `project-context-char-counter` | unchanged |
| **Activation description input** | `project-context-activation-description` | **NEW since ELITEA-2272.** An `<input>` (not CodeMirror), max 300 chars (confirmed live: "166/300" style counter), labeled "When should this context be used?" — required for Save |
| "Edit with AI" open button (saved view) | `ai-edit-project-context-open-button` | **NEW**. Visible directly on the saved view, no separate "Edit" click needed |
| "Edit with AI" modal container | `ai-edit-project-context-modal` | **NEW** |
| "Edit with AI" modal close (X) | `ai-edit-project-context-close-button` | **NEW** |
| "Edit with AI" prompt input | `ai-edit-project-context-prompt-input` | **NEW** |
| "Edit with AI" Cancel button | `ai-edit-project-context-cancel-button` | **NEW** |
| "Edit with AI" Generate button | `ai-edit-project-context-generate-button` | **NEW** |
| Actions menu button (saved view) | `project-context-actions-menu-button` | **NEW**, not exercised by any of these 4 cases (not touched — no testid request beyond noting it exists) |
| Generic success toast | `toast-message` (+ `toast-alert`, `toast-dismiss-button`) | `toast-alert`/`toast-dismiss-button` NEW observed testids on the same toast component — `ProjectContextPage.toast_message` already covers the one these cases need |
| Chat modules panel toggle (Project Context Builder) | `modules-toggle-project_context_builder` (template, existing `ChatPage.MODULES_TOGGLE_SWITCH` constant) | `ChatPage.MODULE_TOGGLE_ORDER` already lists `("project_context_builder", "Project Context Builder")` — no new page-object work needed here, just a test using the existing method |
| Chat send / message input / create-conversation | `chat-send-button`, `chat-message-input`, `sidebar-create-button` | existing `ChatPage` fields, reused as-is |

**No non-testid handles were needed for any of the four cases** — DEV serves
testid rung 1 for every interactive element these cases touch. The empty-
state "Build with AI" button has **no testid yet** (confirmed live via
`[data-testid]` enumeration — absent from the list both in the empty state
and in the Build-with-AI dialog's own controls, e.g. the dialog's "Generate
Draft"/"Cancel"/textarea are also testid-less): use `get_by_text("Build with
AI", exact=True)` (role=button accessible-name rung, confirmed unique) for
the open-button and `get_by_placeholder("Describe your project", exact=False)`
+ `get_by_role("button", name="Generate Draft")` for the dialog, each with
`suggested_testid=`:
- `project-context-build-with-ai-button` (empty-state open button)
- `project-context-build-with-ai-prompt-input` (dialog textarea)
- `project-context-build-with-ai-generate-button` (dialog "Generate Draft")
- The dialog's post-generation review step's "Apply" button:
  `project-context-build-with-ai-apply-button` (role+name "Apply", confirmed
  unique within the dialog scope)
- The inline error Alert (ELITEA-3253): no testid; use `page.locator('[role="alert"]')`
  scoped to the dialog, `suggested_testid="project-context-build-with-ai-error-alert"`

## Network Behavior
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — unchanged shape plus the new `activation_description` field (see Test
  Data). Always 200.
- `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires on Save (create/edit flows) and directly from the chat tool
  (`put_project_context`, case #3). 200 on success.
- `POST /elitea_core/generate_project_context_draft/prompt_lib/{project_id}`
  — fires on both "Generate Draft" (create, from empty state) and the
  "Edit with AI" modal's generate action. 200 with the draft payload on
  success; **422** with this confirmed live body shape on overflow:
  ```json
  {
    "error": "Project background is {N} characters, the maximum is 2500. Try generating again, or ask for a narrower scope.",
    "details": [{"type": "string_too_long", "loc": ["project_background"],
                 "msg": "String should have at most 2500 characters",
                 "ctx": {"max_length": 2500}}],
    "raw": {"activation_description": "...", "project_background": "..."}
  }
  ```
  (confirmed live, two separate overflow runs — `N` was 4303, 4423, 5253, and
  2638 across different prompt/run combinations; `error` is a plain string,
  not nested, so the UI's inline Alert can render it directly).
- `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — **confirmed live: 204** on success (not 200 as ELITEA-2272's AFS states;
  not independently re-tested on an already-empty context this session — carry
  forward ELITEA-2272's documented 404-on-empty behavior as unconfirmed-this-
  session, verify at implementation time).

## Known Defects Found During Exploration

**None found — no product bug.** Three CLARIFICATION-worthy case-text
divergences from the live product were observed (reverse-masking guard
applies: the product is internally consistent and functioning; the TMS case
text is stale against the current build). Not filed as tracker issues per
`.agents/profile.md` § Bug filing (these are case-authoring notes, not
product defects) — recorded here for the TMS case owner to reconcile, per
`.agents/test-automation.yaml`'s `contradictory_metadata: report in the run
summary — never guess, never file, never skip silently` and the skill's own
reverse-masking guard (classify as CLARIFICATION, not `defect-found`):

1. **No "Project Context toggle" exists.** All four cases' Preconditions say
   "Project Context toggle is enabled" / "Enable the Project Context toggle
   if not already enabled." Confirmed live: there is no such switch anywhere
   on `/settings/project-context` in either the empty or populated state. The
   feature's `enabled` flag is sent as a fixed `true` in the PUT body — it is
   not surfaced as a user-facing toggle on this build. This looks like
   leftover case text from an earlier design (possibly superseded by the new
   `activation_description` field, which IS a user-facing per-context
   activation control, just not a boolean toggle). Does not block automation
   — simply drop the toggle step.
2. **ELITEA-3254's tool name**: the case says the AI "invokes
   `generate_project_context_draft` tool"; the live tool-invocation chip
   shows `put_project_context` for a message that both generates AND asks to
   save in one request (the message used includes "and save"). A message
   that asks ONLY to "generate" (not save) might invoke a `read`/`generate`-
   only tool first — not independently tested this session (see Axis 2 note
   re: the precondition gap). Either way, content ends up correctly saved
   ≤2500 chars, so the case's own pass bar is met; only the tool-name
   assertion in automation should match the live chip text, not the case's
   named tool.
3. **ELITEA-3255's "Edit" then "Edit with AI" two-step** does not match the
   live two-independent-buttons layout (see Coverage Map row for case step 2).
   Automate against the live layout: "Edit with AI" is a single click from
   the saved view.

No step blocked exploration; all four cases reached their pass bar on this
build.

Evidence (screenshots, not yet uploaded to the evidence release store — see
Automation Hints):
- `test-results/screenshots/project-context-3252-step01.png` (empty state)
- `test-results/screenshots/project-context-build-with-ai.png` (Build with AI
  dialog, empty prompt)
- `test-results/screenshots/project-context-3252-after-generate.png` (post-
  generation review step, short prompt)
- `test-results/screenshots/project-context-3253-exceeds-limit.png` (422
  error state, long prompt)

## Blocked Steps
None.

## Automation Hints

- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend the existing `automation/pages/project_context_page.py`
  (`ProjectContextPage`) rather than creating a new one — add:
  - `activation_description` field (`LocatorDescriptor(testid="project-context-activation-description")`)
  - `build_with_ai_button`, `build_with_ai_prompt_input`,
    `build_with_ai_generate_button`, `build_with_ai_apply_button`,
    `build_with_ai_error_alert` on the ladder with the `suggested_testid=`
    hints listed in Concrete Handles above
  - `ai_edit_open_button`, `ai_edit_modal`, `ai_edit_prompt_input`,
    `ai_edit_generate_button` (testid rung — all confirmed on DEV)
  - a method like `fill_and_save(content: str, activation_description: str)`
    that wraps the now-two-field Save-enablement (update
    `set_editor_content_via_paste` callers rather than duplicating it, since
    the existing method is otherwise unchanged and still correct for filling
    the editor itself).
  - **Re-verify ELITEA-2272's existing test still passes** before merging —
    its Save-enabled assertions may now be false if the activation-description
    field is required and that test's fixture doesn't fill it. This is a
    shared-component regression risk, not something to silently patch inside
    this family's own test file.
- For ELITEA-3254, no new page object is needed — `ChatPage`'s existing
  `MODULE_TOGGLE_ORDER`/`click_module_toggle`/`is_module_toggle_checked`/
  `close_modules_panel`/`send_message`/`wait_for_ai_response` cover the whole
  flow; only a new test file/method is needed.
- Clipboard-paste technique (ELITEA-2272 precedent) is unnecessary for the
  short strings these four cases use (90–1500 chars) — plain
  `locator.type(text, delay=...)` is fine and was used throughout this
  session's live exploration; reserve clipboard-paste for ELITEA-2272's own
  2500-char boundary case.
- Wait strategy: wait for the specific network response
  (`page.expect_response(lambda r: "generate_project_context_draft" in r.url)`)
  around each "Generate"/"Generate Draft" click rather than a fixed
  `wait_for_timeout` — confirmed live this is the dominant source of
  flakiness risk (generation took 5-11s across different runs/prompts).
- Screenshots captured this session are local scratch-script output, not
  tracker evidence — no tracker issue was filed (no defect found), so the
  `.agents/role-overrides.md` "screenshot evidence attaches" rule does not
  apply here (that rule governs issue/comment bodies). They remain on disk
  under `test-results/screenshots/` for the implementer's reference only.
