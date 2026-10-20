# Test Case: Project Context creation with missing information triggers Ask User clarification

## Metadata
- **TMS ID**: ELITEA-3369
- **Source case**: `.agents/automation/chat-project-context-builder/cases/ELITEA-3369.md` (snapshot)
- **Linked Story**: `EliteaAI/elitea_issues#6239`
- **Priority**: l1 (case priority: `critical` → AFS `l1_` prefix → pytest
  `@pytest.mark.p0`, same convention as the sibling ELITEA-3368 AFS in this
  same feature family).
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app`),
  project `Private` (`${ELITEA_PROJECT_ID}` = `575` in `automation/.env.test`).
  `scripts/dev_storage_state.py` storage state; `mcp__playwright__browser_*`
  tools unavailable in this container (no Chrome binary at
  `/opt/google/chrome/chrome` — same known constraint as ELITEA-3368's AFS,
  see `.agents/memory/qa-engineer/elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`),
  so exploration used a standalone `sync_playwright` script
  (`p.chromium.launch(headless=True)`, loading the same storage-state file) —
  not committed, scratch-only.
- **User set**: `${TEST_USER}` (dev-token/API-login session; renders as
  `autotest_user_admin`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live
  (preconditions + all 6 numbered steps observed against the real DEV app, 3
  independent live runs of the full ambiguous-request → clarify → answer →
  created flow). No product defect found; one case-text precondition
  clarified (same pattern as ELITEA-3368's "module toggle is per-conversation,
  not ambient" finding — see Known Defects). No existing merged spec covers
  this case's own observable (see Coverage decision).

## Coverage decision — why `ready-for-automation`

Searched `test-specs/chat-interface/` and `automation/tests/ui/chat/` by
behaviour (`ask_user`, `clarifying`, `ClarifyingQuestion`, `project_context`)
before executing. Found:

- `test-specs/chat-interface/_surface.md` (digest, not a spec) and
  `test-specs/chat-interface/l1_chat-project-context-create-update-chip-canvas_ELITEA-3368.md`
  (merged to `origin/main`, confirmed via `git log -1 -- test-specs/chat-interface/_surface.md`
  showing commit `c9eb89f5` already on this branch's history, and this
  session's own `git log --oneline -10` showing it as an ancestor commit) —
  covers Project Context creation **assuming the create message is
  unambiguous** ("Create project context: This project is a Python REST API
  for order management."), explicitly asserting NO clarifying question is
  asked for that message. It never drives an ambiguous request, never
  exercises `ClarifyingQuestionControl`, and never touches the `ask_user`
  module at all — the `ask_user` toggle isn't even enabled in that test's
  setup. Different observable (the ask_user HITL pause, never reached by
  ELITEA-3368's flow), not a target for `extend-existing`/`already-covered`.
- `test-specs/chat-interface/lextend_modules-panel-full-menu-and-all-toggles_ELITEA-2464.md`
  and its underlying implementation exercise the `ask_user` **toggle switch
  itself** (on/off state in the Modules panel), never the clarifying-question
  CARD/flow the toggle gates. Different observable (module panel UI vs.
  in-conversation clarification UI) — orthogonal, not a target.
- `automation/tests/` has zero hits for `ask_user`/`clarifying`/`Clarifying`
  outside the two files above (`grep -rln`).
- No spec anywhere drives the ambiguous-request → `ClarifyingQuestionControl`
  card → answer-submission → entity-creation flow this case specifies.

Conclusion: `ready-for-automation`, fresh test. Reusing ELITEA-3368's own
module-toggle/conversation-creation infra (`ChatPage.ensure_module_toggle_checked()`,
`close_modules_panel()`, `generated_entity_chip`/`open_generated_entity_chip()`,
`ProjectContextChatCanvasPage`, `ProjectContextAPI`/`clean_project_context`
fixtures — all already exist on this branch from ELITEA-3368's implementation)
made exploration and will make implementation fast, but does not change the
classification — nothing existing drives the clarifying-question path.

## Preconditions
- User is logged in to `https://dev.elitea.ai` (satisfied by the dev storage
  state / API-login session).
- Project Context Builder is enabled in Chat Modules — **NOT ambient**, same
  finding ELITEA-3368's AFS already documented: every new conversation starts
  with the `project_context_builder` toggle OFF; enable via the `+` menu →
  Modules submenu before sending the ambiguous message.
- **Ask User is enabled in Chat Modules — ALSO NOT ambient, same per-conversation
  mechanism, confirmed live this session.** `GET /api/v2/social/module_settings/{project_id}`
  → `default_ask_user_enabled: false` for this project (same shape as
  `default_project_context_builder_enabled`); every new conversation's Modules
  submenu `modules-toggle-ask_user` switch renders unchecked. **Both toggles
  must be explicitly enabled per-conversation** before sending the ambiguous
  message, or the assistant silently guesses instead of asking (confirmed
  live: with ONLY `project_context_builder` enabled and `ask_user` left OFF,
  the identical ambiguous message "Set up project context for this." produces
  a direct `"There is no project context configured yet. Please provide the
  project background..."` text response — no clarifying card, no tool chip
  for `ask_user` — i.e. the assistant degrades to a plain follow-up question
  in chat rather than the structured Ask User card the case's Pass criteria
  require). This is a clarification of an under-specified precondition, same
  pattern as ELITEA-3368's finding — not a defect; see Known Defects.
- The current project has no existing Project Context configured — enforced
  via the EXISTING `clean_project_context` fixture
  (`automation/fixtures/data_fixtures.py`, built for ELITEA-3368; reuse
  directly — no new fixture needed).

## Test Data

### reuse-existing
- `${TEST_USER}` — dev-token/API-login session.
- `${ELITEA_PROJECT_ID}` (`575`, "Private") — ambient default project for
  this session.

### generate-per-test (created via the UI action under test, cleaned up in its own teardown)
- **New conversation** — created via `ChatPage.click_create_conversation()`
  (existing method); same "no dependency on a prior case" pattern as
  ELITEA-3368.
- Ambiguous request, **case's literal Test Data**: `"Set up project context
  for this."`
- Clarification answers (own choice, confirmed live to work; case text itself
  only specifies the EXPECTED RESULT — "a question about intended scope" —
  not a literal answer script):
  - Q1 (free-text, "Your option" input): a short project description, e.g.
    `"This project is a Python REST API for order management."`
  - Q2 (single-select radio, 2 options): `"When relevant"` (confirmed live
    stable wording across all 3 runs this session, alongside sibling option
    `"Always"`).

### API endpoints used for setup/teardown/verification
Identical to ELITEA-3368's AFS — reuse `ProjectContextAPI` as-is:
- `GET /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
- `DELETE /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`
- `GET /api/v2/social/module_settings/{project_id}` — diagnostic only, confirms
  the per-project DEFAULT (not the per-conversation toggle the test drives).
- `DELETE /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  — cleanup, via `ConversationAPI.delete_conversation()`.
- OpenAPI contract confirmed live this session (`GET /shared/openapi/?all=true`):
  `/api/v2/elitea_core/project_context/{mode}/{project_id}/project-context`
  (`get`/`put`/`delete`) and `/api/v2/elitea_core/generate_project_context_draft/{mode}/{project_id}`
  (`post`) are both documented — same contract ELITEA-3368 already used, no
  new endpoint needed by this case.

## Test Steps

1. Open a fresh conversation (`ChatPage.click_create_conversation()`). Open
   the `+` menu (`plus-menu-button`), hover **Modules**, enable BOTH
   `project_context_builder` AND `ask_user` toggles
   (`ensure_module_toggle_checked("project_context_builder")` +
   `ensure_module_toggle_checked("ask_user")` — the EXISTING ELITEA-3368
   method works unchanged for `ask_user` too, confirmed live: neither toggle
   shows a confirmation toast, so the toast-less variant is required for
   both, not just `project_context_builder`), then
   `close_modules_panel()` before interacting with the composer (same
   submenu-interception gotcha ELITEA-3368 documented).
   - **Verify**: both toggle switches report checked
     (`is_module_toggle_checked()` for each key) before proceeding.
2. Send the ambiguous message `"Set up project context for this."` via the
   composer (`chat-message-input`) + send button (`chat-send-button`).
   - **Verify**: the response does NOT proceed directly to creation — no
     `generated-entity-chip` appears, and the assistant instead pauses on a
     clarifying-question card (confirmed live 3/3 runs with this exact
     message, both toggles enabled).
3. Wait for the clarifying-question card to render (poll for the card's
   custom-text input — see Concrete Handles; `wait_for_ai_response()`-style
   condition wait, not a fixed sleep — observed live at 15–25s for the first
   `ask_user` pause to appear).
   - **Verify**: a tool-invocation chip containing `"Ask User: ask_user"`
     appears (confirmed live, same colon-separated `"{service}: {endpoint}"`/
     `"{toolkit}: {tool}"` shape already documented for this toolkit's other
     calls, e.g. ELITEA-3368's `"Elitea Project Context: ..."` chips).
   - **Verify**: the card presents a scope/background QUESTION — confirmed
     live, the exact live wording varies slightly run to run (`"What project
     background should I use for the project context?"` /
     `"What should the project context describe?"`) but is topically
     consistent: it always asks for the project's purpose/background needed
     to populate the context, satisfying the case's "question about intended
     scope" Pass criterion via a background/purpose question (this
     environment's actual card does NOT offer scope radio options like
     "current project only / all conversations / specific Agent or Pipeline"
     — see Known Defects for the case-text clarification this produces).
   - **Verify**: a stepper reading `"1/2"` is visible (confirmed live 3/3 —
     this flow asks exactly 2 questions: a free-text project-background
     question first, then a single-select "when should the model load the
     full context" question with 2 radio options, `"Always"` / `"When
     relevant"`).
4. Answer Q1: type the project-background text into the custom-text input
   (`placeholder="Your option"`) and click the submit button (its visible
   label toggles `"Skip"`→`"Continue"` once the input is non-empty — confirmed
   live, same `answered` logic as the component source).
   - **Verify**: the card advances to Q2 (stepper now reads `"2/2"`, the
     `"When relevant"`/`"Always"` option rows render) — confirmed live 3/3;
     the card does NOT close after Q1 alone (this is a 2-question flow, not
     1-and-done).
5. Answer Q2: click the `"When relevant"` option row (a hoverable row with a
   nested MUI radio, no accessible name of its own — see Concrete Handles),
   then click the now-"Continue"-labeled submit button (selecting a radio
   option on the LAST step does not auto-advance like it would on a
   non-last step — confirmed live, the component's own `handleSelectSingle`
   only auto-advances `if (!isLastStep)`; the final Continue click is still
   required to actually submit).
   - **Verify**: the clarifying-question card disappears immediately
     (confirmed live 3/3 — no re-render with a 3rd question, no lingering
     "1/2"/"2/2" stepper).
6. Wait for the AI response (`wait_for_ai_response()`-style condition wait;
   full generate-and-save round trip observed live at 15–20s after the final
   Continue click).
   - **Verify**: the clarifying card does NOT reappear (confirmed live 3/3 —
     this case's own Fail criterion "Clarification card reappears after
     submission").
   - **Verify**: a `generated-entity-chip` labeled `"Project Context"`
     renders in the assistant's answer (confirmed live 3/3 — same component
     ELITEA-3368 already uses/declares; reuse `ChatPage.generated_entity_chip`/
     `open_generated_entity_chip()` unchanged).
   - **Verify**: via a direct API GET
     (`GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`),
     the Project Context now exists (`id` is non-null, `content` is non-empty)
     and the content is topically consistent with the Q1 answer submitted
     (e.g. contains "REST"/"API"/"order" when that was the Q1 text — confirmed
     live, AI phrasing varies but is topically faithful, same non-determinism
     caveat ELITEA-3368's AFS already documented for this same tool).
   - Click the chip (hover → "Open entity", reuse
     `open_generated_entity_chip()` unchanged) and verify the Canvas's
     `project-context-editor-content` shows non-empty content consistent with
     the submitted answer — closes the loop with a UI-level read, not
     API-only (same pattern ELITEA-3368's AFS step 9 already established).

## Expected Results
- Sending the ambiguous request with `project_context_builder` AND `ask_user`
  both enabled triggers exactly ONE clarifying-question flow (2 sequential
  questions presented one at a time via a stepper, never both at once, never
  re-shown after the final answer) — steps 2–3, 5.
- The clarifying card closes immediately after the final answer is submitted
  (step 5).
- A Project Context is created whose content reflects the submitted
  background answer (steps 6).
- The clarification is never re-shown for this same request (step 6).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Project Context Builder enabled in Chat Modules | — | AFS step 1 | `modules-toggle-project_context_builder` checked | asserted *(clarified: per-conversation, same as ELITEA-3368)* |
| Precondition: Ask User enabled in Chat Modules | — | AFS step 1 | `modules-toggle-ask_user` checked | asserted *(clarified: per-conversation, NOT ambient — new finding this case, see Known Defects)* |
| 1 Send ambiguous "Set up project context for this." → clarifying-question card appears | clarifying-question card appears, includes a question about intended scope | AFS steps 2–3 | custom-text input (`placeholder="Your option"`) visible, tool chip `"Ask User: ask_user"` present | asserted *(clarified: the live card asks a project-background question, not a literal "scope" multiple-choice — see Known Defects)* |
| 2 Verify question card includes scope options | question asks about scope (e.g. current project only / all conversations / specific Agent or Pipeline) | AFS step 3 | — | **clarification, not asserted as literally specced** — see Known Defects: the live Q1 is open-ended background text, Q2 is "when to load" (Always/When relevant), neither matches the case's named scope-option set |
| 3 Select an answer for scope and submit → card closes | the clarification card closes | AFS steps 4–5 | custom-text input + option-row submission across both questions; card absence confirmed via `custom_input.count() == 0` | asserted |
| 4 Verify clarification card does not reappear | the same clarification card is not shown again for this request | AFS step 6 | no re-render of the custom-text input / stepper after the final Continue | asserted |
| 5 Verify Project Context is created | a Project Context chip/link appears in the chat response | AFS step 6 | `generated-entity-chip` present, label "Project Context" | asserted |
| 6 Click the chip and inspect the created Project Context | scope and content reflect the submitted answer | AFS step 6 (final clause) | API GET non-empty content + Canvas `project-context-editor-content` re-check | asserted *(content reflects the Q1 BACKGROUND answer; "scope" per the case's own framing maps to the Q2 "when to load" answer, not a separate scope field — see Known Defects)* |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- AFS step 1 explicitly enables `ask_user`, not just `project_context_builder`
  — *added: the case precondition text only names the latter; live behaviour
  needs BOTH, confirmed by the degraded-no-clarification repro documented in
  Preconditions. Omitting this guard produces a confusing "no clarifying card
  appeared" failure far downstream instead of a clear precondition miss.*
- AFS step 3 asserts the stepper reads `"1/2"` and step 4 asserts it advances
  to `"2/2"` — *added: the case text implies a single clarifying question;
  live behaviour is a 2-question sequence. Asserting the stepper transition
  gives the implementer a precise, falsifiable multi-step signal instead of
  only "a card appeared" / "a card is gone".*
- AFS step 5 asserts that selecting the LAST question's radio option does
  NOT auto-submit — the final Continue click is still required — *added:
  directly observable in the component source
  (`ClarifyingQuestionControl.jsx`'s `handleSelectSingle` only calls
  `goNext()` `if (!isLastStep)`) and confirmed live; a test that assumes
  selecting the last option auto-submits would silently never click Continue
  and then time out waiting for the chip.*
- AFS step 6 re-verifies via a UI-level Canvas reopen on top of the API GET —
  *added: closes the loop so the test doesn't only prove the API was updated
  while never checking what the user actually sees, same established pattern
  as ELITEA-3368's AFS step 9.*
- Side-channel console-error check folded into every step (not in the case's
  own text) — *added: standard practice on this surface, confirmed clean
  across all 3 runs this session.*

## Cleanup
1. `DELETE /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
   — the conversation created in step 1 (via `ConversationAPI.delete_conversation()`).
2. `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
   (best-effort, tolerate 404) — restores the empty-state precondition.
   Reuse the EXISTING `clean_project_context` fixture (ELITEA-3368) for both
   setup and teardown — no new fixture needed.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration — DEV, ladder provenance)

| Element | Rung | Handle | Provenance | Notes |
|---|---|---|---|---|
| `+` menu button | 1 (testid) | `plus-menu-button` | pre-existing, confirmed live | `ChatPage.plus_menu_button` |
| Modules submenu toggle (Project Context Builder) | 1 (testid) | `modules-toggle-project_context_builder` | pre-existing on DEV | `ChatPage.ensure_module_toggle_checked("project_context_builder")` (existing, ELITEA-3368) |
| Modules submenu toggle (Ask User) | 1 (testid) | `modules-toggle-ask_user` | pre-existing on DEV, confirmed live (first added for ELITEA-2464) | `ChatPage.ensure_module_toggle_checked("ask_user")` — SAME existing method, confirmed live it also works for this key (no confirmation toast, same as `project_context_builder`) |
| Message composer | 1 (testid) | `chat-message-input` | pre-existing, confirmed live | `ChatPage.message_input` (existing) |
| Send button | 1 (testid) | `chat-send-button` | pre-existing | existing `ChatPage.send_button` |
| `ask_user` tool-invocation chip | 1 (testid) | `chat-answer-tool-chip` | pre-existing, confirmed live for text `"Ask User: ask_user"` | existing `ChatPage.answer_tool_chip`; filter by `.filter(has_text="Ask User")` |
| Clarifying-question card container | — (no testid, no stable role/label on the container itself) | — | **NO testid anywhere** — confirmed live + via full source read of `ClarifyingQuestionControl.jsx`/`ChatHitlActions.jsx`: the card is a plain `<Box>`, no `data-testid`, no `role`, no `aria-label`. The container itself is never a locator target in this AFS — every assertion below targets a child element instead. | `suggested_testid="chat-clarifying-question-card"` — **needs-adding**, the whole-card presence/absence check in this AFS uses the custom-text input as the detection proxy instead (see next row) |
| Clarifying question's custom-text input | 3 (label — via `placeholder`, confirmed stable; NOT a true `<label>`/`aria-label`, see note) | `placeholder="Your option"` | **NO testid, NO aria-label, NO `<label>`** — confirmed live via `get_by_label("Your option")` returning 0 matches, and via source read: `TextField`'s `placeholder` prop only, no `aria-label`/`InputLabel`. Declare as a `css=` rung (`input[placeholder="Your option"]`), NOT `label=` (Playwright's `get_by_label` does not match a bare placeholder) — confirmed live. | `suggested_testid="chat-clarifying-question-custom-input"`. Doubles as the card's presence/absence signal (`count() > 0`/`== 0`) since the container itself has no testid. |
| Stepper label (`"1/2"`, `"2/2"`) | 4 (css, text-anchored) | Typography containing text matching `/^\d+\/\d+$/`, only rendered when the question set has >1 entry | **NO testid** — confirmed live + source (`stepperLabel` Typography, `total > 1` conditional). Only present on a MULTI-question flow (this case's live flow always has 2) — a 1-question flow (confirmed reachable live when the Q1 answer alone fully satisfies the tool, see step 3's Known-Defects note on run-to-run question-count variance) renders no stepper at all. | `suggested_testid="chat-clarifying-question-stepper"`. Assert its text, not its mere presence, since a 1-question run legitimately has none. |
| Submit button (label toggles Skip ⇄ Continue) | 2 (role+name, STATE-DEPENDENT NAME — see note) | `role="button" name="Skip"` (unanswered) / `role="button" name="Continue"` (answered) | **NO testid** — confirmed live + source (`BaseBtn` with no `data-testid`, variant/children change with the `answered` boolean, same-element conditional-text pair). Per `.agents/testing.md`'s state-handle rule ("state is specced as an attribute/ARIA-state filter, never a state-dependent handle") this is borderline: the ACCESSIBLE NAME itself is the only differentiator (no `aria-pressed`/`data-*` state attribute exists), so there is no non-text rung available — flagging as a `question` for the lead/testid-migrator rather than inventing a positional pick. For THIS AFS, implementation locates by whichever name is current (`get_by_role("button", name="Continue")` once text is entered, falling back to `"Skip"`), never a positional index among the two header-stepper buttons. | `suggested_testid="chat-clarifying-question-submit-button"` — adding a real testid retires the state-dependent-name problem entirely; flagged, not blocking. |
| Previous/Next question stepper nav buttons | 2 (role+name) | `role="button" name="Previous question"` / `role="button" name="Next question"` | **NO testid**, confirmed live via `aria-label` on the icon buttons — stable, not exercised by this case's own steps (the case answers in forward order only; back-navigation is out of scope) | `suggested_testid="chat-clarifying-question-prev-button"` / `"...-next-button"` — not touched by this case |
| Option row (e.g. "When relevant") | 5 (xpath, text-anchored, scoped) | row Box containing a Typography with the option's exact label text, clickable (the whole row, not just the nested radio — nested `BaseCheckbox` has `pointerEvents: 'none'` on its own control per source) | **NO testid, NO accessible name on the row itself** (the nested MUI radio input has no `aria-label`; only the sibling Typography carries the visible text) — confirmed live via `get_by_text(option_label).click()` reliably hitting the row (`cursor: pointer`, `onClick={() => handleRowClick(option)}` on the row `Box`, not the radio) | `suggested_testid="chat-clarifying-question-option-{}"` (dynamic, by sanitized option label) — **needs-adding**. Scope non-positionally: this AFS's own flow has at most 2 rows and selects by exact label text, never by index. |
| Generated-entity chip (Project Context) | 1 (testid) | `generated-entity-chip` | pre-existing, DECLARED on this branch already (ELITEA-3368: `ChatPage.generated_entity_chip`) | reuse `open_generated_entity_chip(entity_label="Project Context")` unchanged |
| Canvas editor content | 1 (testid) | `project-context-editor-content` | pre-existing (ELITEA-2272), reuse `ProjectContextPage` composed on the same page (ELITEA-3368 pattern) | existing `ProjectContextPage.editor_content` |
| Canvas chrome (title/close) | 5 (xpath, scoped) | — | pre-existing `ProjectContextChatCanvasPage` (added for ELITEA-3368) | reuse unchanged — this case never needs to close the canvas before the Canvas-level re-verification, since the chip-click happens only once at the very end |

Not touched by this case (no testid requested — scope discipline):
- The "Delete entity" hover button on the generated-entity chip (no delete
  step in this case).
- Canvas Save/Discard buttons (this flow's AI tool call does its own PUT; no
  manual Save click in this case's own steps, same as ELITEA-3368).
- Previous/Next question stepper nav (forward-only flow, see table above).

## Network Behavior
- `POST /api/v2/elitea_core/generate_project_context_draft/prompt_lib/{project_id}`
  — fires once the clarifying-question flow completes (confirmed live via the
  WebSocket trace's tool-name string, same inference-only caveat ELITEA-3368's
  AFS already recorded — not independently confirmed via a raw network-tab
  capture of the exact REST verb/path this session; the OpenAPI contract
  itself WAS confirmed this session, see Test Data).
- `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires as part of the same completion round trip (confirmed live via the
  API GET showing non-empty content immediately after the final Continue
  click, same single-call generate-and-save shape ELITEA-3368 documented).
- The `ask_user` HITL resume itself is a `POST`/predict-style request carrying
  `{action: "answer", value: {...}, toolCallId, interruptId}` per
  `ChatHitlActions.jsx`'s `handleClarifyingSubmit` (confirmed via source read,
  not independently captured on the wire this session — flagged for the
  implementer's first pass if a network-level assertion on this specific
  request becomes useful; not needed for this AFS's own UI-level assertions).

## Known Defects Found During Exploration
None — no product defect found. Three CLARIFICATIONS (case-text drift, not
bugs — reverse-masking guard applies):

1. **Precondition "Ask User is enabled in Chat Modules" is per-conversation,
   not an ambient project setting — same mechanism ELITEA-3368 already
   documented for `project_context_builder`.** Confirmed live:
   `GET /api/v2/social/module_settings/{project_id}` returns
   `default_ask_user_enabled: false`, and a brand-new conversation's Modules
   submenu toggle for this key renders OFF. Confirmed live that omitting this
   toggle causes the assistant to SILENTLY DEGRADE to a plain text follow-up
   question in chat (no `ask_user` tool chip, no clarifying-question card,
   no stepper) rather than failing visibly — a test that only enables
   `project_context_builder` (as the case's literal precondition text
   implies is sufficient) would produce a confusing false negative on step 2.
   Not filed as a tracker issue (test-authoring note only, not a product gap
   — the toggle mechanism itself works identically to every other module key,
   same as ELITEA-3368's equivalent finding).
2. **The clarifying card's actual question set does not match the case's
   named scope-option list.** The case's Pass criteria specify "a question
   about intended scope (e.g., current project only / all conversations /
   specific Agent or Pipeline)". The LIVE card instead asks (confirmed
   identical shape across 3 runs): Q1 — an open-ended free-text question
   about the project's purpose/background/architecture/terminology; Q2 — a
   single-select "when should the model load the full context" question with
   exactly 2 options, `"Always"` / `"When relevant"`. Neither question offers
   the case's named scope choices (no "current project only" / "all
   conversations" / "specific Agent or Pipeline" option anywhere). The case's
   underlying INTENT — "ask when information is missing, use the answer to
   complete creation correctly" — IS satisfied by the live flow; only the
   SPECIFIC named question/option text is stale relative to the live product.
   This AFS asserts the live question/option set (Known Defects + Coverage
   Map), not the case's literal wording — reverse-masking guard. Not filed
   as a tracker issue — purely a case-text wording gap, not a behavior gap
   (the feature's actual intent, "ask for missing info and act on the
   answer", is fully met); worth a case-text update if/when the TMS case
   itself is revised, but doesn't block automation per the reverse-masking
   guard's own guidance ("file the case-text drift as a clarification...
   assert the live contract").
3. **Question count is 2 for this exact ambiguous prompt, but is NOT
   guaranteed to be a fixed constant across all possible prompts** — a
   closely related probe this session (same ambiguous message, Q1 answered
   with a FULLER description including both purpose AND an explicit "scope:
   current project only" clause in the free-text answer) produced only ONE
   question total before completing (confirmed live, see Automation Hints) —
   i.e. the model's own `ask_user` tool call count appears to depend on how
   much the Q1 answer itself already resolves. This AFS specs the stable,
   reproducible 2-question path (Q1 generic background, Q2 generic "when to
   load") that resulted from the case's OWN literal Test Data message
   answered with a SHORT, single-sentence background — confirmed deterministic
   3/3 with that exact combination. The implementer should NOT hardcode an
   assumption that "the flow always asks exactly 2 questions" as a general
   product fact; this AFS's own test is written against the specific,
   reproducible path, with the stepper-count assertion scoped to THIS test's
   own run (step 3's `"1/2"` assertion), not asserted as an invariant of the
   `ask_user` tool in general.

## Blocked Steps
None. All 6 case steps + both preconditions were executed and observed live,
across 3 independent full ambiguous-request → clarify (2 questions) →
answer → verify runs, plus 1 additional probe run (both-toggles-off control,
confirmed the silent-degradation finding above) and 1 additional probe run
(fuller Q1 answer → single-question path, confirmed the finding above).

## Automation Hints
- Framework: Playwright + pytest, ladder locators (`.agents/testing.md`).
- **Compose, don't rewrite**: this case reuses, UNCHANGED, every piece of
  infrastructure ELITEA-3368 already built on this branch —
  `ChatPage.ensure_module_toggle_checked()`, `close_modules_panel()`,
  `generated_entity_chip`/`GENERATED_ENTITY_CHIP_OPEN_BUTTON`/
  `open_generated_entity_chip()`, `ProjectContextChatCanvasPage`,
  `ProjectContextAPI`, and the `project_context_api`/`clean_project_context`
  fixtures. The ONLY new page-object surface this case needs is the
  clarifying-question card's own elements (new `ChatPage` fields — see
  Concrete Handles: custom-text input, stepper label, submit button,
  dynamic option-row template).
- **New `ChatPage` fields needed**: a `CLARIFYING_QUESTION_CUSTOM_INPUT`
  (`css='input[placeholder="Your option"]'`, `suggested_testid=
  "chat-clarifying-question-custom-input"`), a `CLARIFYING_QUESTION_STEPPER`
  (text-anchored, `suggested_testid="chat-clarifying-question-stepper"`), a
  `CLARIFYING_QUESTION_SUBMIT_BUTTON` helper that resolves by CURRENT
  accessible name (`"Continue"` if present else `"Skip"` — flagged as a
  `question` per the state-dependent-name note in Concrete Handles, not
  blocking), and a dynamic `CLARIFYING_QUESTION_OPTION` template
  (`ScopedLocator`-style text match by exact option label,
  `suggested_testid="chat-clarifying-question-option-{}"`). A small
  `answer_clarifying_question(custom_text: str | None, option_label: str |
  None)` helper on `ChatPage` that: fills the custom input when `custom_text`
  is given, OR clicks the option row when `option_label` is given (mutually
  exclusive per the component's own `handleCustomChange`/`handleRowClick`
  semantics — typing text clears any radio selection and vice versa), then
  clicks the submit button — covers both Q1 (free-text) and Q2 (option
  select) with one method, called twice.
- **Wait strategy**: no fixed sleeps. Poll for the custom-text input's
  visibility as the clarifying card's own appearance signal (observed live
  15–25s after Send for the FIRST `ask_user` pause — slower than
  ELITEA-3368's plain creation path since this flow does an extra HITL
  round-trip); poll for its ABSENCE as the "card closed" signal after the
  final submit; use `wait_for_ai_response()`-style condition waits for the
  final AI response/chip, same as every other surface on this page object.
- **Non-determinism caveat (same family as ELITEA-3368's)**: the exact
  WORDING of each clarifying question varies run to run (confirmed live:
  3 runs produced 3 differently-worded Q1 prompts, all topically asking for
  project background/purpose) — assert topical content (e.g. the stepper
  count, the tool-chip presence, the input's placeholder) never the exact
  question text. The Q2 OPTION LABELS (`"Always"` / `"When relevant"`) WERE
  stable verbatim across all 3 runs — safe to assert exactly.
- No sanctioned-RED / known-defect handling needed — this case's happy path
  is fully clean across every run this session.
