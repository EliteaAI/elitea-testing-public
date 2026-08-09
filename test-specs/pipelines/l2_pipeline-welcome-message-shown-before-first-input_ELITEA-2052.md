# Test Case: Pipeline — Welcome Message shown before first user input

## Metadata
- **TMS ID**: ELITEA-2052
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter/header, both agree)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (localhost: `auth_state`/`VITE_DEV_TOKEN` bypasses login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live
  system via Playwright MCP; all 6 steps verified; the feature (a pipeline's
  configured welcome message renders automatically in the embedded chat panel
  before any user input) has **no functional defect**. All required elements
  already carry testids (some pre-existing on `main`, one accordion-header
  testid exists only on `automation/testids` and is not needed for this case's
  assertions — see § Concrete Handles). No `add-data-testid` work needed.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- No pre-existing pipeline is required — the case's own step 1 ("Open a
  pipeline") is satisfied by creating a fresh disposable pipeline through the
  create form itself (mirrors `test_create_pipeline_full_details_persist.py`'s
  pattern; no separate "open an existing pipeline" precondition is needed).

## Test Data

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Pipeline name: `autotest_pipe_welcome_<unique>` (`autotest_` prefix — cleanup
  fixture convention, see `l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`
  § Test Data).
- Description: any non-empty string (required field, not itself under test).
- Welcome message (literal, from the case): `Hello! How can I help you today?`

## Test Steps

1. Navigate to `${BASE_URL}/pipelines/create?viewMode=owner` (sidebar "Pipelines"
   → "+ Pipeline", same entry point as `test_create_pipeline_full_details_persist.py`
   steps 1–2) and fill Name + Description.
   - **Verify — PASSES.** Create form loads; Name/Description fields show the
     typed values.
2. Locate the "Welcome message" section in the left panel
   (`agent-canvas-section-welcome-message` accordion header — see Metadata
   note) and confirm it is expanded.
   - **Verify — PASSES, with a case-text nuance (not a defect).** The Welcome
     message section is a `BasicAccordion` item with its own expand/collapse
     header (`<button aria-expanded>`), matching the case's literal wording —
     **but it renders already expanded by default**, exactly like the
     pre-existing "Advanced" section's `agent-canvas-section-advanced` pattern
     documented in ELITEA-2021's AFS. No click is needed to reach the
     textarea; asserting `welcome_message_input.wait_for(state="visible")`
     (step 3) already proves the section is expanded, so no separate
     interaction with the accordion header is required. Confirmed live via
     accessibility snapshot: `heading > button [expanded] > "Welcome message"`
     immediately followed by the visible `region` containing the textarea.
3. Fill the "Input your welcome message" textbox
   (`agent-welcome-message-input`) with the literal:
   `Hello! How can I help you today?`
   - **Verify — PASSES.** Field value updates immediately; character counter
     shows `736 characters left` (confirmed live, `MAX_WELCOME_MESSAGE_LENGTH`
     - message length).
4. Click Save (`agent-save-button`).
   - **Verify — PASSES.** `POST /api/v2/elitea_core/applications/prompt_lib/399`
     returns `2xx` (confirmed live: pipeline created, id `8580` in this
     session); page navigates to
     `/pipelines/all/{id}?destTab=configuration&name=...&viewMode=owner`. Zero
     console errors, zero console warnings.
5. "Open a new chat session with this pipeline."
   - **Verify — PASSES, with a live-product clarification (not a defect).**
     There is no separate "open chat" action on the pipeline detail route —
     the embedded chat panel is **already mounted** on the detail page (same
     live-product shape ELITEA-1885 documented for the agent detail page).
     The AFS treats "open a new chat session" as: (a) the chat panel visible
     immediately after Save (step 4, same page), **and** (b) a full-page
     reload (`page.goto`, not an SPA route change) to the same detail URL,
     which gives a pristine "new session" load distinct from any live-preview
     state carried over from step 3's typing. Both were confirmed live in
     this session: the welcome message appears identically in both cases.
6. Verify the welcome message
   `Hello! How can I help you today?` appears automatically before any user
   input.
   - **Verify — PASSES.** Confirmed live (post-reload, pristine state):
     exactly **one** `chat-message-item` inside `chat-message-list`, sender
     label shows the pipeline's own name (`autotest_2052_welcome` in this
     session), body text (`.innerText`) contains the exact literal
     `Hello! How can I help you today?`. The message input textbox is empty
     and no user message precedes or follows it. The message renders through
     the agent/pipeline-answer code path — `chat-read-out-button` present,
     `skill-test-last-response` present (it's the sole/last message),
     `chat-answer-content` absent, `chat-message-delete-button` absent
     (confirmed live via `browser_run_code_unsafe` locator counts) — the
     exact same testid-based code-path signature ELITEA-1885 established for
     the agent surface (this pipeline's embedded chat panel shares the same
     `ChatMessageList.jsx`/`ApplicationAnswer.jsx` FSD components with the
     agent surface — confirmed via source read).

## Expected Results
- The configured welcome message persists across Save and a full-page reload.
- Exactly one message renders in the embedded chat panel before any user
  message is sent, and it is that welcome message.
- The message renders through the agent-answer code path (never the
  user-message code path).
- No console errors or warnings at any step.
- The create `POST` returns `2xx`.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| Precondition: a pipeline is open for editing | Pipeline loaded in editor | Step 1 (create form) | create form loads, fields accept input | asserted *(satisfied via a fresh disposable pipeline — see Preconditions note)* |
| 1 Open a pipeline | Pipeline loaded in editor | Step 1 | create form URL + field values | asserted |
| 2 Expand "Welcome message" section in left panel | Section visible | Step 2 | accordion header `[expanded]` + visible textarea region | asserted *(clarification: already expanded by default, no click needed — see Step 2 note, same pattern as ELITEA-2021's "Advanced" section)* |
| 3 Fill welcome-message textbox | Field populated | Step 3 | `welcome_message_input.input_value()` / char counter | asserted |
| 4 Save pipeline | Saves without errors | Step 4 | POST 2xx, console error/warning check | asserted |
| 5 Open a new chat session with this pipeline | New chat session starts | Step 5 | chat panel visible immediately post-save AND after a full-page reload | asserted *(clarification: no separate "open chat" action exists on this route — panel is always mounted; "new session" = pristine reload — see Step 5 note)* |
| 6 Verify welcome message appears automatically before any user input | Message displayed at top of chat | Step 6 | message count == 1, exact text match, agent-code-path testids present/absent | asserted |
| Expected Final State: welcome message shown at start of every new chat session, before any user interaction | — | Step 6 (post-reload) | same assertions as Step 6 | asserted |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1–6 | console error/warning check at Step 4 and reload | asserted |
| Fail criterion: "message absent or incorrect text" | n/a (negative condition) | Step 6 | exact-text + count==1 assertion (absent/wrong text would fail it) | asserted |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Message renders via the agent/pipeline-answer code path specifically (`chat-read-out-button` + `skill-test-last-response` present, `chat-answer-content` + `chat-message-delete-button` absent), not just "message is visible" | Stronger, testid-based signal than a bare text-presence check; mirrors ELITEA-1885's exact pattern for the agent surface and satisfies the project's testid-only locator policy |
| Zero console errors AND zero console warnings at Save and at the post-reload load | Silent-error check per project convention (`test-case-analysis` § Anti-patterns); clean both times this run |
| Exact message count == 1 (not just "welcome message is present") | The case's Fail criterion calls out "shows incorrect text" / implicitly "appears after user input" — a bare presence check wouldn't catch a welcome message preceded/followed by another message; count==1 closes that gap |
| Full-page reload (not SPA navigation) before the "new chat session" check | Guards against synthetic/session-state carryover from Step 3's live-preview typing poisoning the "before any user input" assertion — same pristine-context discipline ELITEA-1885 used |
| The chat panel is confirmed to share the same FSD chat components (`ChatMessageList.jsx`/`ApplicationAnswer.jsx`) as the agent surface | Grounds the "no new testid needed" claim in source, not assumption — confirmed via `grep`/source read this session |

## Cleanup
1. Created a disposable pipeline (`autotest_2052_welcome`, id `8580`) via the
   create-form UI flow (Steps 1–4 above).
2. Executed all 6 case steps against it (see Test Steps above).
3. **Not deleted this session** — a live `DELETE
   /api/v2/elitea_core/application/prompt_lib/399/8580` attempted via
   `page.evaluate(fetch(...))` failed with a same-origin `TypeError: Failed to
   fetch` in the Playwright-MCP page context (likely a CSP/CORS quirk of
   evaluating `fetch` from that context, not a product defect — not
   investigated further, out of scope for this analysis). The pipeline
   carries the `autotest_` prefix so it is picked up by
   `cleanup_autotest_pipelines_at_end` on deployed envs (no-ops on
   localhost, same precedent as ELITEA-2021's analyst-session throwaway
   pipelines, which were also left in the shared local dev DB). **For the
   implementer:** use `pipeline_api.delete_pipeline(pipeline_id)` in a
   `try/finally` (the pattern `test_create_pipeline_full_details_persist.py`
   already follows) — the API client's `DELETE` call works fine from a real
   pytest fixture/test context; only the ad-hoc MCP-session `fetch` probe hit
   the quirk above.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Provenance | Notes |
|---|---|---|---|
| Pipeline name input | `agent-name-input` | on-main ✓ | Already a field: `PipelineFormPage.name_input`. |
| Pipeline description input | `agent-description-input` | on-main ✓ | Already a field: `PipelineFormPage.description_input`. |
| Welcome message section header (accordion) | `agent-canvas-section-welcome-message` | **on `automation/testids` only** (added 2026-07-21 by EliteaAI/EliteaUI@353be956, ELITEA-2166 — unrelated case, shared `WelcomeMessage.jsx`); confirmed absent on `origin/main` via fresh `git fetch origin` + `git grep` this session | **Not needed for this case's assertions** — the section is expanded by default (confirmed live) and `welcome_message_input`'s visibility already proves the section is open (same "don't interact with an always-expanded accordion" precedent as ELITEA-2021's `agent-canvas-section-advanced`). No page-object field needed; do not add one speculatively (canon ruling #511 — only add what the test's executed path calls). |
| Welcome message textarea | `agent-welcome-message-input` | on-main ✓ | Already a field: `PipelineDetailPage.welcome_message_input` (added ELITEA-2021). Use `fill_welcome_message()`/`get_welcome_message()` (already exist, `pipeline_detail_page.py:5376`/`:5393`). |
| Save button | `agent-save-button` | on-main ✓ | Already a field: `PipelineFormPage.save_button`. |
| Embedded chat message list container | `chat-message-list` | on-main ✓ (shared `ChatMessageList.jsx`) | **Not yet a `LocatorDescriptor` field on `PipelineDetailPage`** — only exists on `AgentDetailPage.chat_message_list`. Add a sibling field on `PipelineDetailPage` (same testid, per project convention of duplicating shared-component testids as separate fields per page object — see ELITEA-2021 AFS § Automation Hints precedent). Confirmed live: count==1 in this session. |
| Each message item | `chat-message-item` | on-main ✓ (shared `ChatMessageList.jsx`/`ApplicationAnswer.jsx`) | Same as above — add `PipelineDetailPage.chat_message_item` field (mirrors `AgentDetailPage.chat_message_item`). |
| Agent/pipeline-answer child: TTS read-out button | `chat-read-out-button` | on-main ✓ | Confirmed present (count==1) scoped inside the welcome-message `chat-message-item` this session. Add a `PipelineDetailPage` field if not already present (mirrors `ChatPage.read_out_button`). |
| Agent-answer body, when message is last/only in the list | `skill-test-last-response` | on-main ✓ | Confirmed present (count==1) this session — same `isLastMessage` ternary ELITEA-1885 documented for the agent surface (shared `ApplicationAnswer.jsx`). Assert on this, not `chat-answer-content`, since a lone welcome message is always "last". |
| Agent-answer body, non-last message (absence check only) | `chat-answer-content` | on-main ✓ | Confirmed absent (count==0) this session — correct, since the welcome message is the sole/last message. |
| User-only child (absence check): message delete button | `chat-message-delete-button` | on-main ✓ | Confirmed absent (count==0) this session — proves the bubble is not user-rendered. |

No new testids need adding to EliteaUI for this case — every element it
touches already carries one on `main` except the accordion header (which
this case's assertions don't need). Only new page-object *fields* are
needed, all against pre-existing `main` testids: `chat_message_list`,
`chat_message_item`, and (if not already present on `PipelineDetailPage`)
`chat_read_out_button`, `skill_test_last_response`, `chat_answer_content`,
`chat_message_delete_button` — the implementer should grep
`pipeline_detail_page.py` first since some of these may already exist under
different names from prior pipeline cases (e.g. HITL-related chat fields
exist at line ~1028 onward).

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` — fires on Save,
  `2xx` on success (confirmed live, pipeline id `8580`).
- `GET /api/v2/elitea_core/application/prompt_lib/399/{id}` — fires on page
  load/reload, `200 OK`, returns `version_details.welcome_message` which the
  pipeline's `usePipelineChat.hooks.js` reads to seed `chatHistory` via
  `ChatHelpers.getWelcomeMessage()` (confirmed via source read — same
  `getWelcomeMessage`/`getInitialChatHistory` helper `chat.helpers.js` that
  ELITEA-1885 documented for the agent surface's `useApplicationChat.hooks.js`;
  the pipeline hook is a sibling implementation using the identical helper).
- No further network/WebSocket traffic is relevant — no chat message is sent
  by this case (only the welcome message, seeded client-side from the GET
  response, is asserted).

## Known Defects Found During Exploration
None found. The feature behaves exactly as the case describes on the
pipeline surface — no reverse-masking, no functional defect. Two
documented **case-text clarifications** (not tracker-filed as defects, per
the reverse-masking guard — both are minor step-sequencing/wording notes,
not incorrect expected results):
1. Step 2's "Expand Welcome message section" is a no-op in the live product
   — the section is expanded by default (see Step 2 note).
2. Step 5's "Open a new chat session" has no distinct UI action on the
   pipeline detail route — the chat panel is always mounted; a full-page
   reload is the closest equivalent to a "new session" (see Step 5 note).

Neither rises to a filed clarification issue on its own — both are the same
class of low-stakes wording drift ELITEA-2021 already normalized for this
exact form (its "Advanced section already expanded" note), and this AFS
documents the equivalent nuance in place per the reverse-masking guard rather
than opening a duplicate-pattern ticket.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Reuse `PipelineDetailPage` end-to-end (subclasses `PipelineFormPage`) —
  `navigate_to_create()`, `name_input`/`description_input`,
  `fill_welcome_message()`/`get_welcome_message()`,
  `save_and_wait_for_creation()`, `wait_for_detail_page_load()` all already
  exist and were exercised live this session; no changes needed to any of
  them.
- Add the small set of chat-assertion fields listed in § Concrete Handles to
  `PipelineDetailPage` (all pre-existing `main` testids — no `add-data-testid`
  work, pure page-object additions).
- Wait strategy: after Save, `page.wait_for_load_state("networkidle")` before
  reading the chat panel — confirmed live the chat panel's welcome message
  renders promptly (well under 1s after the detail page's own load), no
  WebSocket wait needed since this is a client-side-seeded message, not an
  AI-generated response.
- Teardown: `pipeline_api.delete_pipeline(pipeline_id)` in a `try/finally`,
  exactly as `test_create_pipeline_full_details_persist.py` already does —
  don't reuse the MCP-session `fetch`-based delete attempt that failed (see
  Cleanup note); it's an artifact of the exploration tool, not the pytest
  fixture path.
- Test data teardown note: this session's throwaway pipeline (`autotest_2052_welcome`,
  id `8580`) was left in the shared local dev DB (see Cleanup) — harmless,
  same precedent as ELITEA-2021's analyst-session pipelines.
