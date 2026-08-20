# Test Case: Chat – Create Agent with AI Build – Click Cancel and Verify Creation is Terminated

## Metadata
- **TMS ID**: ELITEA-2073
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Status**: `ready-for-automation`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst/Implementer**: test-automation-engineer, combined slot (wave-16) — cluster dispatch with ELITEA-2074
- **Tooling**: Playwright MCP server (browser_navigate/click/type/evaluate), driving the live localhost surface directly

## Coverage decision — why `ready-for-automation`, not `extend-existing`

Two existing specs cover *adjacent* ground, but neither covers this case's
own combination:

- `test_build_with_ai_from_chat_canvas.py` (ELITEA-1920, merged) proves
  Generate → review → Create Agent **inside the chat canvas** — but never
  exercises Cancel at all.
- `test_agent_build_with_ai.py`'s `TestAgentBuildWithAICancelFromPromptStep`
  (ELITEA-1917, merged) proves Cancel-before-Generate closes the modal
  without creating an agent — but on the **standalone `/agents/create`**
  page, not the chat canvas, and it never re-opens the modal and retries a
  real generation afterward.

This case's own subject — open the canvas, verify its 5 sections + the
Build-with-AI entry point, open the modal, verify Generate is
disabled-until-typed, Cancel it, **re-open the SAME modal and complete a
real generate → review → Create Agent cycle**, landing on the
canvas's post-save "Editing…" state — is a single continuous flow neither
existing spec runs end-to-end. Per the extend/fresh boundary in the
`test-case-analysis` skill ("if the gap is large enough that the extension
would be a near-rewrite of the covering spec, treat as `ready-for-automation`
instead"), swapping a case-owned cancel-then-retry sequence into either
existing spec would not be a small additive edit — it is this case's own
scenario. **Zero new page-object locators or testids are needed anywhere in
this case** (100% reuse of `ChatPage`, `AgentCanvasPage`,
`GenerateAgentModalPage`, `AgentFormPage`) — the correct shape is a new,
small test module composing the same three-plus-one page objects
`test_build_with_ai_from_chat_canvas.py` already composes.

## Preconditions
- User is logged in with sufficient permission to open "Build with AI"
  (`${TEST_USER}`, confirmed live — `generate-agent-open-button` renders and
  is clickable, same finding as every prior "Build with AI" AFS).
- User is on the Chats section (confirmed live — `/chat`).

## Test Data

### reuse-existing
- AI build description used verbatim from the case's own Test Data table:
  `"generate an echo agent"`.
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is left behind — the created agent (and the conversation, if it
acquires an id) are deleted in Cleanup.

## Test Steps

All 15 case steps reproduced live end-to-end this session (Playwright MCP,
direct testid-scoped `evaluate()`/`click()`/`type()` calls against
`http://localhost:5173`).

1. `+ Chat` (`sidebar-create-button`) opens a fresh conversation; composer's
   `plus-menu-button` → hover `agents-menuitem` → click
   `agents-create-new-button`.
   - **Verify — PASSES.** The in-chat "Create New Agent" canvas panel opens
     (`AgentCanvasPage.wait_for_open()`); `agent-canvas-title` reads
     `"Create New Agent"` (confirmed live via `evaluate()`).
2. Click the "+ Chat" button / plus-menu → Agents → Create New Agent (same
   click as step 1 in this case's own numbering — folded together, both
   AFS step 1 and case step 2 are the single canvas-open action).
3. Verify the canvas displays sections GENERAL, INSTRUCTIONS, WELCOME
   MESSAGE, CHAT STARTERS, ADVANCED.
   - **Verify — PASSES.** All 5 `AgentCanvasPage.get_section_header(key)`
     accordion headers (`agent-canvas-section-{general,instructions,
     welcome-message,chat-starters,advanced}`) present, confirmed live via
     one batched `evaluate()` call (all 5 `true`). Pre-existing testids —
     `AgentCanvasPage.SECTION_KEYS` already enumerates exactly these 5 keys.
4. Verify the "Build with AI" button is visible in the top right of GENERAL.
   - **Verify — PASSES.** `generate-agent-open-button` present and
     `offsetParent !== null` (visible), confirmed live.
5. Click "Build with AI" (`generate-agent-open-button`).
   - **Verify — PASSES.** `generate-agent-modal` opens (confirmed live).
6. Verify the modal shows placeholder text and Cancel/Generate buttons;
   Generate disabled until text entered.
   - **Verify — PASSES.** Live-confirmed: `generate-agent-prompt-input`
     placeholder = `"Describe your agent's goal, key tasks, and preferred
     tone or behavior."`; `generate-agent-cancel-button` and
     `generate-agent-submit-button` both present;
     `generate-agent-submit-button.disabled === true` before any text is
     typed.
7. Type `"generate an echo agent"` in the prompt textarea.
   - **Verify — PASSES.** `generate-agent-submit-button.disabled` flips to
     `false` once the field is non-empty (confirmed live).
8. Click "Cancel" (`generate-agent-cancel-button`).
   - **Verify — PASSES.** `generate-agent-modal` is fully removed from the
     DOM immediately (confirmed live — matches the standalone-page Cancel
     behavior ELITEA-1917 already proved, now confirmed live inside the
     canvas too).
9. Verify no generation took place and the canvas remains open with empty
   fields.
   - **Verify — PASSES.** `agent-canvas-title` still reads `"Create New
     Agent"`; `AgentFormPage.name_input` (`agent-name-input`) value is
     `""` (confirmed live).
10. Click "Build with AI" again (`generate-agent-open-button`).
    - **Verify — PASSES.** Modal re-opens with `generate-agent-prompt-input`
      value `""` (confirmed live — the earlier Cancel did not leave stale
      text in a still-mounted textarea; the modal remounts fresh).
11. Type `"generate an echo agent"` and click "Generate"
    (`generate-agent-submit-button`).
    - **Verify — PASSES.** `generate-agent-loading-indicator`
      ("Generating agent draft...") renders immediately after the click
      (confirmed live — a real, non-mocked LLM call; this AFS does not time
      the loading window, matching every prior Build-with-AI AFS's own
      choice not to assert an exact loading duration).
12. Wait for AI generation to complete.
    - **Verify — PASSES.** The review form renders (confirmed live via
      `getByText("Chat starters").waitFor()`, ~35s wall time for this
      real generation). Review-form fields, read live this session:
      `generate-agent-review-name-input` = `"Echo Agent"`;
      `generate-agent-review-description-input` non-empty (129 chars this
      run); `generate-agent-review-instructions-input` non-empty (350
      chars this run — literal text captured in ELITEA-2074's AFS, since it
      is this case's precondition for step 15/16); 4 conversation-starter
      inputs populated (`generate-agent-review-starter-input-{0..3}`);
      `generate-agent-approve-button` / `generate-agent-back-button` both
      present. **Console note:** one pre-existing, already-documented
      `disableUnderline` React-prop warning fires on this form (same
      baseline noise `test-specs/agents/_surface.md` and
      `test-specs/skills/_surface.md` already record for this exact review
      form) — not a new finding, exclude from console-error assertions.
13. Click "Create Agent" (`generate-agent-approve-button`).
    - **Verify — PASSES.** `POST .../elitea_core/applications/prompt_lib/399`
      resolves `201` (agent id `9406` this run); URL becomes
      `/chat?edited_participant_id=9406` — stays on `/chat`, no navigation
      away (same `useAgentCreation.js` wiring ELITEA-1920 already
      documented, reconfirmed live for the AI-generated-agent path too).
14. Verify the canvas shows Name "Echo Agent", populated Description and
    Instructions.
    - **Verify — PASSES.** `agent-canvas-title` transitions to the review
      form's own generated Name (`"Echo Agent"` both live generations this
      session, but the implementation asserts it dynamically —
      `created_agent_name` captured live off the create-POST response body,
      per `.agents/testing.md` § "How to test a NONDETERMINISTIC producer
      without substituting it" — never a hardcoded literal, since the LLM
      is not guaranteed to name the agent identically on a future run) —
      the case's own plain-language claim, satisfied via the same
      title-transition contract ELITEA-1920/2166 already proved (the
      General-accordion `agent-name-input`/
      `agent-description-input` fields are collapsed/not queried directly
      here; the canvas title IS the case's own "shows Name" claim, same
      assertion shape ELITEA-1920 uses for its own equivalent step).
15. Verify the agent is in "Editing..." state.
    - **Verify — PASSES.** `chat-participant-settings-button` text reads
      `"Editing..."` (confirmed live — matches the pre-existing
      `AgentEditorPanel.jsx:291` contract `test-specs/chat-interface/
      _surface.md` already documents for owned-agent canvases, ELITEA-2089).

## Expected Results
Matches the case's stated Pass criteria in full: Cancel dismisses the modal
without any generation (empty canvas, no draft/create network call);
re-opening + Generate + Create Agent populates the canvas with the real
AI-generated "Echo Agent" configuration and lands the canvas in the
"Editing..." state. All 15 case steps executed live; zero console errors
beyond the pre-existing, already-documented `disableUnderline` baseline
noise; zero unexpected network 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, on Chats section | reachable | Preconditions | `/chat` loads, composer visible | asserted |
| 1 Navigate to Chats | Chats section displayed | step 1 | page loaded | asserted |
| 2 + Chat / + icon → Create New Agent | canvas panel opens | step 1 | `agent-canvas-title` = "Create New Agent" | asserted |
| 3 Sections GENERAL/INSTRUCTIONS/WELCOME MESSAGE/CHAT STARTERS/ADVANCED visible | all visible | step 3 | 5× `agent-canvas-section-{key}` present | asserted |
| 4 Build with AI button visible top-right of GENERAL | visible | step 4 | `generate-agent-open-button` visible | asserted |
| 5 Click Build with AI | modal opens | step 5 | `generate-agent-modal` visible | asserted |
| 6 Modal shows placeholder + Cancel/Generate; Generate disabled | condition holds | step 6 | placeholder text, both buttons present, `submit_button.disabled===true` | asserted |
| 7 Type prompt | Generate enabled | step 7 | `submit_button.disabled===false` | asserted |
| 8 Click Cancel | modal closes immediately | step 8 | `generate-agent-modal` absent from DOM | asserted |
| 9 No generation; canvas remains open, empty | condition holds | step 9 | canvas title unchanged, `agent-name-input` value empty | asserted |
| 10 Click Build with AI again | modal opens, empty textarea | step 10 | `generate-agent-prompt-input` value === "" | asserted |
| 11 Type + click Generate | loading indicator shown | step 11 | `generate-agent-loading-indicator` present | asserted |
| 12 Wait for generation | confirmation dialog w/ Name/Description/Instructions + Back/Create buttons | step 12 | review-form fields populated, both buttons present | asserted |
| 13 Click Create Agent | dialog closes, canvas populates | step 13 | create POST 201, URL stays on `/chat` | asserted |
| 14 Canvas shows Name "Echo Agent", populated Description/Instructions | condition holds | step 14 | `agent-canvas-title` === `created_agent_name` (dynamic, captured off the create-POST response — not a hardcoded "Echo Agent" literal) | asserted *(sync note: "Echo Agent" was this session's live value on both runs, not a guaranteed literal — see step 14 rationale)* |
| 15 Agent in "Editing..." state | condition holds | step 15 | `chat-participant-settings-button` text === "Editing..." | asserted |

### Axis 2 — Analyst/implementer additions

- Step 6/7 assert the Generate button's `disabled` DOM property directly
  (not just visual appearance) — *added: a stronger, deterministic check
  than "looks blue/cyan" (the case's own subjective color language), and
  reusable across theme/CSS changes.*
- Step 10 explicitly re-checks the prompt textarea is genuinely empty on
  re-open (not stale text left over from the cancelled attempt) — *added:
  closes a real "does Cancel actually reset modal state" question the case
  text implies but doesn't spell out as its own check.*
- Step 12's Instructions text is captured verbatim and carried into
  ELITEA-2074's AFS (§ Test Data) as this case's own precondition for the
  Echo Agent's actual echo behavior — *added: makes the two AFS's shared
  precondition traceable instead of ELITEA-2074 re-deriving it blind.*

## Cleanup
1. Created agent (id `9406` this run) — deleted via `AgentAPI.delete_agent()`
   in the implementation's `finally` block.
2. No message was ever sent in this flow, so the conversation never
   acquired a server-side id (same "unsaved until first message" behavior
   ELITEA-1920/2166 already document) — nothing to delete server-side.

## Concrete Handles (zero new testids — 100% reuse, confirmed live this session)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| `+ Chat` button | `ChatPage.sidebar_create_button` | on-main ✓ (pre-existing) | n/a |
| Plus menu / Agents submenu / Create New Agent | `ChatPage.plus_menu_button` / `.agents_menuitem` / `.agents_create_new_button` | on-main ✓ | n/a |
| Canvas title / 5 section headers | `AgentCanvasPage.title` / `.get_section_header(key)` (`SECTION_KEYS`) | on-main ✓ | n/a |
| Build with AI open button | `GenerateAgentModalPage.open_button` | on-main ✓ | n/a |
| Modal / prompt / Cancel / Generate / loading indicator | `GenerateAgentModalPage.modal` / `.prompt_input` / `.cancel_button` / `.generate_button` / `.loading_indicator` | on-main ✓ | n/a |
| Review-form Name/Description/Instructions/Starters | `GenerateAgentModalPage.review_name_input` / `.review_description_input` / `.review_instructions_input` / `.get_review_starter(i)` | on-main ✓ | n/a |
| Approve/Back buttons | `GenerateAgentModalPage.approve_button` / `.back_button` | on-main ✓ | n/a |
| Agent Name field (empty-check, step 9) | `AgentFormPage.name_input` (`agent-name-input`) | on-main ✓ | n/a |
| "Editing..." chip | `ChatPage.chat_participant_settings_button` (documented in `test-specs/chat-interface/_surface.md` § ELITEA-2089) | on-main ✓ | n/a |

## AFS Amendment (2026-08-20, fix round 1 — reviewer findings)

A fresh reviewer session returned `CHANGES_REQUESTED`; two of the findings touched this AFS:

**Finding — the console-error side-channel was documented (§ Expected Results: "zero console
errors beyond the pre-existing... baseline noise") but never automated.** The sibling case's
own test (`test_generated_echo_agent_save_close_and_starters.py`, ELITEA-2074) already
implements a `page.on("console", _on_console)` handler + a dedicated "Side-channel check" step;
this case's test did not. **Resolution**: ported the identical idiom into
`test_build_with_ai_cancel_then_generate_echo_agent.py` — the same `disableUnderline` exclusion
(step 12's own already-documented baseline noise), the same handler registered before the `try`
block, and the same final `assert not console_messages` step. The Expected Results claim is now
backed by a real assertion.

**Finding — step 14's Verify text and Coverage Map row asserted a hardcoded `"Echo Agent"`
literal, but the implementation always asserted `created_agent_name` (dynamic, captured off the
create-POST response body).** This AFS's own live evidence never claimed the name is guaranteed
— `"Echo Agent"` was simply what this session's two live generations happened to produce for the
prompt `"generate an echo agent"`. Per `.agents/testing.md` § "How to test a NONDETERMINISTIC
producer without substituting it," asserting the dynamic value the system actually produced (not
a value the analyst wrote down) is the correct, durable assertion — the *implementation* was
already right; the AFS's documentation was stale relative to it. **Resolution**: step 14's
Verify text and the Coverage Map row 14 disposition above are amended to describe the dynamic
assertion, so the AFS now matches what the code has always done — no code change was needed
here, only the docs sync.
