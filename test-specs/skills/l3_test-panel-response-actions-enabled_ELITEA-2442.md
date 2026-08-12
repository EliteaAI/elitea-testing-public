# Test Case: Read aloud and Copy to clipboard are enabled on test panel responses

## Metadata
- **TMS ID**: ELITEA-2442
- **Linked Story**: none
- **Priority**: l3 (case frontmatter/body: `medium`) — matches sibling
  `l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md` /
  `l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`,
  same "medium" TMS priority label.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value, not an exclusion. Proceeded
  to full execution.
- **Dedup / reuse check**: grepped `test-specs/skills/` and
  `automation/tests/ui/skills/*.py` for "read aloud" / "copy to clipboard" /
  "test panel" — no existing merged spec asserts the enabled/clickable state
  of the SkillTestPanel's response action buttons. The closest neighbours,
  `l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md` and
  `l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`,
  drive the same test panel (`SkillDetailPage.send_test_message()` /
  `wait_for_test_response()`) but neither asserts anything about the
  response's action-button row (Read out / Copy / Regenerate / Delete). Not
  a duplicate — proceeded as new coverage, reusing the same page-object
  methods for message send/wait.
- **Source-traced root cause (why this case is meaningful):** the Read-out
  and Copy-to-clipboard buttons on `ApplicationAnswer.jsx` (shared by the
  Chat `ChatBox.jsx` and the Skill `SkillTestPanel.jsx` — same
  `ChatMessageList`/`ApplicationAnswer` component tree, per the ELITEA-2436
  precedent already documented in `_surface.md`) gate on
  `disabled={VOICE_FEATURES_TEMPORARILY_DISABLED || isProcessing ||
  !realAnswer || !!speakingMessageId}` (Read out) and `disabled={isProcessing
  || !realAnswer}` (Copy) — i.e. both flip to enabled the instant
  `isProcessing` clears and `realAnswer` is non-empty, exactly the state a
  fully-arrived test-panel response reaches. This case's pass criterion is
  therefore a genuine regression guard on that gating logic, not a trivial
  "element exists" check.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all`) and at least one Skill
  exists (or is created fresh — see Test Data).
- Voice features are enabled for this environment: confirmed live via
  `common/constants.js`'s `VOICE_FEATURES_ENABLED` (defaults `true` when
  `VITE_VOICE_FEATURES_ENABLED` is unset — confirmed unset in
  `EliteaUI/.env`) and `VOICE_FEATURES_TEMPORARILY_DISABLED` (defaults
  `false` when `VITE_VOICE_FEATURES_TEMPORARILY_DISABLED` is unset — also
  confirmed unset). Both confirmed live in the running session: the "enter
  speaking mode" / "start voice input" controls render in the test-panel
  input bar, which only happens when `VOICE_FEATURES_ENABLED` is true.

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- Skill: created via the UI create-skill form (`SkillsListPage.navigate_to_create()`
  → `SkillFormPage.fill_form(name, instructions, description)` →
  `save_and_wait_for_navigation()`) — mirrors the ELITEA-2440/2441 sibling
  tests' Step 1 exactly. A dedicated skill is created (rather than reusing
  an existing one) so the test panel's message history starts empty and the
  run is self-contained.
- Skill name convention: `autotest-2442-<slug>` (must satisfy the Name
  field's `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, ≤32-char constraint documented
  in `test-specs/skills/_surface.md`).
- Instructions used this run (live exploration, not necessarily the
  implementation's literal string): `"Reply with the single word: PONG"` —
  any deterministic short instruction works; content is irrelevant to this
  case, only that a response is produced.
- `SkillAPI.delete_skill(skill_id)` reused for teardown (pattern confirmed
  live by the ELITEA-2440/2441 siblings; this run itself explored against
  a pre-existing skill — see Exploration note below — so no fresh skill was
  created or needed cleanup this run, but the AFS/implementation should
  still create+clean up its own skill for isolation, matching every other
  test-panel case in this feature).
- **Exploration note:** this run's live verification reused an existing
  skill (`autotest-skill-markdown-toggle`, id `1463`, from a prior
  ELITEA-2432 run) purely to observe the action-button behavior — sending a
  test-panel message mutates no skill-entity state (confirmed: the only
  `POST` fired was `predict_llm`, no `PUT`/`PATCH` to the skill; matches the
  "any existing skill is safe to reuse" finding already recorded for
  ELITEA-2436 in `_surface.md`). No cleanup was needed for this exploration
  run. The implementation should still use its own disposable skill per
  the project's test-isolation convention (`.agents/testing.md` § Test data
  strategy) — reuse-for-exploration is not licence to skip isolation in the
  shipped test.

## Test Steps

1. Open a Skill and run a test prompt in the test panel.
   - Create the Skill (see Test Data), which navigates to its detail page
     with the SkillTestPanel visible.
   - Send a test prompt via `SkillDetailPage.send_test_message()`.
   - **Verify — confirmed live**: message sends without error; the skill
     detail page (`/skills/all/{id}`) loads successfully with the
     SkillTestPanel rendered, matching the case's "Target page/section
     loads successfully" expectation.

2. Wait for a response to appear.
   - Wait via `SkillDetailPage.wait_for_test_response()`.
   - **Verify — confirmed live**: response text stabilizes (this run:
     `"PONG"`, `get_last_test_response()`); the AI response arrives over
     WebSocket per `.agents/testing.md`, `wait_for_test_response()`'s
     content-stabilization polling is the correct wait, not a plain
     network-response wait.

3. Verify the "Read aloud" and "Copy to clipboard" action buttons are
   active and clickable (not grayed out or disabled).
   - **Verify — confirmed live, TWO layers of proof, not just the `disabled`
     attribute:**
     - **Layer 1 (state):** `page.get_by_test_id("chat-read-out-button")`
       and `page.get_by_test_id("chat-copy-button")` both resolve to exactly
       one element on the last (AI) response, and both have
       `.disabled === false` / no `aria-disabled` attribute (confirmed via
       live DOM query — see Network/Console evidence below). The
       accessibility snapshot corroborates this independently: neither
       button carries the `[disabled]` marker the snapshot shows on other,
       genuinely-disabled controls in the same view (`"clear the chat"`,
       `"Save"`, `"Discard"` all show `[disabled]`; `"Read out"` and
       `"Copy to clipboard"` do not).
     - **Layer 2 (behavioral — actually clicking each, stronger than a bare
       `disabled` check since a button can be non-disabled yet still
       non-functional):** clicking `chat-copy-button` produced the toast
       **"The message has been copied to the clipboard."**; clicking
       `chat-read-out-button` opened the `chat-voice-mini-player` (the
       `VoiceMiniPlayer`, with a live `chat-voice-play-stop-button`). Both
       confirm the buttons are not just visually enabled but genuinely
       functional — the case's "clickable" wording is satisfied by an
       actual successful click outcome, not merely an attribute read.

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: after a
test-panel response completes, the "Read aloud" (`chat-read-out-button`) and
"Copy to clipboard" (`chat-copy-button`) action buttons on that response are
both enabled (`disabled === false`, no `[disabled]` in the a11y tree) AND
functionally clickable (Read aloud opens the voice mini-player; Copy
produces the "copied to the clipboard" toast). No functional product defect
found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| 1 Open a Skill and run a test prompt in the test panel | target page/section loads successfully | step 1 | step 1: skill detail page loads, test prompt sent without error | asserted |
| 2 Wait for a response to appear | wait completes; subsequent state is ready | step 2 | step 2: response text stabilizes (`"PONG"`) | asserted |
| 3 Verify Read aloud and Copy to clipboard are active/clickable, not grayed out/disabled | condition holds as described | step 3 | step 3: `.disabled === false` on both testids (state) + successful click outcome on both (toast / voice player) | asserted |
| Expected Final State: both buttons active and clickable | — | step 3 | step 3, same assertions | asserted |

**Note on the case's own step ordering:** the case's 3 steps map 1:1 to the
AFS's 3 steps — no decomposition or reordering was needed. Step 3's single
case line ("active and clickable") was split into the two independently
meaningful proofs above (state + behavior) because "clickable" is stronger
than "not disabled" — see Axis 2.

### Axis 2 — Analyst additions

- **Click-through assertion (added) is stronger than a bare `disabled`
  check** — *why: the case's own wording is "active and clickable", not
  merely "not disabled". A button can have `disabled=false` yet still be
  non-functional (e.g. a stale `onClick` handler, an unmounted portal
  target for the voice player). Actually clicking each button and observing
  its real effect (toast text; voice-player mount) is the only proof that
  satisfies "clickable" as written, and it's genuinely cheap here since both
  actions are synchronous/client-visible (no destructive side effect,
  nothing to clean up).*
- **Both testids resolve to exactly ONE element scoped to the (single) AI
  response in this flow** — *added: confirmed live via
  `document.querySelectorAll('[data-testid="chat-copy-button"]').length ===
  1` — the user's own message row also renders a "Copy to clipboard"
  button, but it carries a DIFFERENT mechanism (`UserMessage.jsx`'s inline
  `title={'Copy to clipboard'}`, no `chat-copy-button` testid), so the
  testid-scoped selector is unambiguous even with multiple "Copy to
  clipboard"-labelled buttons on screen. Do not use a text-based selector
  here — it would collide with the user message's copy button.*
- **Read-aloud gating condition, source-confirmed** — *added:
  `ApplicationAnswer.jsx`'s Read-out button also depends on
  `VOICE_FEATURES_ENABLED` (module-level constant, gates whether the button
  renders AT ALL) and `hasSpeakableText` (whether the response has
  TTS-convertible content) — both true for this run's plain-text "PONG"
  response. If a future response type produces no speakable text (e.g. an
  empty/tool-only answer), the Read-out button would legitimately not
  render — out of scope for this case (case only covers a normal text
  response), but a trap for whoever picks a different test message.*
- **"zero console errors across the case's own 3 steps"** — *added:
  side-channel check per this skill's standard discipline; confirmed live —
  0 console errors after opening the skill, sending the message, and
  clicking both action buttons.*
- **Network confirmation the response completed before the assertion
  fires** — *added: `POST /api/v2/elitea_core/predict_llm/prompt_lib/399`
  → `200 OK` observed; `wait_for_test_response()`'s content-stabilization
  wait (not a network wait) is still the correct implementation pattern per
  `.agents/testing.md` (WebSocket delivery), but the REST `predict_llm` call
  is a useful secondary corroboration that the request cycle completed.*

## Cleanup
1. Delete the skill created in Test Data via `SkillAPI.delete_skill(skill_id)`
   in test teardown (`try`/`finally`), regardless of pass/fail — matches the
   ELITEA-2440/2441 sibling tests' cleanup pattern exactly.
2. No other cleanup needed: clicking Read aloud / Copy to clipboard mutates
   no server-side state (confirmed live: no `PUT`/`PATCH` fired by either
   click; the copy goes to the OS clipboard, the read-aloud player is
   client-only UI state that unmounts when stopped/navigated away).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill create form — Name field | `page.get_by_test_id("skill-name-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.name_input` | n/a — testid already present |
| Skill create form — Description field | `page.get_by_test_id("skill-description-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.description_input` | n/a — testid already present |
| Skill create form — Instructions CodeMirror editor content | `page.get_by_test_id("skill-instructions-editor-content")` — **confirmed live, existing testid**, already `SkillFormPage.instructions_editor_content` / `fill_instructions()` | n/a — testid already present |
| Skill create form — Save button | `page.get_by_test_id("skill-save-button")` — **confirmed live, existing testid** | n/a — testid already present |
| Test panel chat input | `page.get_by_test_id("chat-message-input")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel send button | `page.get_by_test_id("chat-send-button")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel last AI response text | `page.get_by_test_id("skill-test-last-response")` — **confirmed live, existing testid**, already `SkillDetailPage.get_last_test_response()` | n/a — testid already present |
| Read aloud (speaker) button on the AI response | `page.get_by_test_id("chat-read-out-button")` — **confirmed live, existing testid** (`ApplicationAnswer.jsx`), aria-label `"Read out"`. **Not yet on `SkillDetailPage`** — `ChatPage` already exposes it as `read_out_button` (`automation/pages/chat_page.py:526`), but `SkillDetailPage` (a separate class, extends `SkillFormPage`, no shared inheritance with `ChatPage`) has no equivalent field yet — implementer adds a `LocatorDescriptor(testid="chat-read-out-button")` field on `SkillDetailPage`, mirroring `ChatPage`'s | n/a — testid already present, page-object field is the only gap |
| Copy to clipboard button on the AI response | `page.get_by_test_id("chat-copy-button")` — **confirmed live, existing testid** (`ApplicationAnswer.jsx`). **Not yet on `SkillDetailPage`** — `ChatPage` already exposes it as `copy_action_button` (`automation/pages/chat_page.py:481`); `SkillDetailPage` has no equivalent field yet — implementer adds a `LocatorDescriptor(testid="chat-copy-button")` field on `SkillDetailPage` | n/a — testid already present, page-object field is the only gap. **Do NOT match by role/text "Copy to clipboard"** — the user's own message row renders a same-labelled but differently-mechanised button (no `chat-copy-button` testid); the testid-scoped selector is required to avoid ambiguity. |
| Voice mini-player (opens on Read-out click) | `page.get_by_test_id("chat-voice-mini-player")` — **confirmed live, existing testid**, already `ChatPage.voice_mini_player` (an `OptionalLocatorDescriptor`) | n/a — testid already present; optional handle for the click-through (Layer 2) assertion only, not required to satisfy the case's literal 3 steps |

**Summary for the implementer / `add-data-testid`:** zero testid gaps found
this run — every UI element the case touches already carries a testid, but
**two of them (`chat-read-out-button`, `chat-copy-button`) are not yet
wired as `LocatorDescriptor` fields on `SkillDetailPage`** (they exist on
`ChatPage` for the Chat surface, but `SkillDetailPage` is a separate class
with no shared base). This is page-object work, not an `add-data-testid`
round-trip — add both fields to `SkillDetailPage` (and optionally
`copy_toast_message` / `voice_mini_player` if the implementer chooses to
assert the click-through Layer 2 proof, recommended per Axis 2).

## Network Behavior
- `POST /api/v2/elitea_core/skills/prompt_lib/399` → `201 Created` (skill
  creation, step 1 setup — implementation's own fresh-skill flow; this
  exploration run itself reused an existing skill, see Test Data).
- `GET /api/v2/elitea_core/skill/prompt_lib/399/{id}` → `200 OK` (skill
  detail load).
- `POST /api/v2/elitea_core/predict_llm/prompt_lib/399` → `200 OK`
  (test-panel prompt send).
- AI test-panel response arrives over WebSocket (per `.agents/testing.md`),
  not a plain REST call — `wait_for_test_response()`'s content-stabilization
  polling is the correct wait strategy.
- **Confirmed live: clicking Read aloud / Copy to clipboard fires ZERO
  `PUT`/`PATCH`/`POST` requests** — both actions are 100% client-side (OS
  clipboard write; local TTS/voice-player UI state). No network wait is
  needed around either click in the implementation.
- `DELETE /api/v2/elitea_core/skill/prompt_lib/399/{id}` → `204 No Content`
  (implementation's own cleanup; not exercised by this exploration run).

## Known Defects / Observations Found During Exploration
No functional product defect was found. Both action buttons render enabled
and are genuinely clickable/functional the moment a test-panel response
completes — confirmed via DOM `.disabled` state, the accessibility tree's
absence of a `[disabled]` marker (contrasted live against other, genuinely
disabled controls in the same view), and an actual click-through to each
button's real effect (copy toast; voice mini-player mount).

## Blocked Steps
None. All 3 case steps were executed end-to-end live against the real DEV
backend on localhost: opening a Skill, sending a test-panel prompt and
waiting for the response, then verifying both action buttons' enabled state
and clicking each to confirm real functionality.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_test_panel_response_actions.py`
  (new file — grep of `automation/tests/ui/skills/` found no existing test
  asserting the test-panel response action-button row).
- Fixtures: `skill_api` (or the raw `SkillAPI`) for skill create/delete,
  matching the ELITEA-2440/2441 sibling tests exactly.
- `SkillFormPage.fill_form()` / `save_and_wait_for_navigation()` for step 1
  setup (mirrors `test_skill_management.py::TestCreateSkill`'s Steps 1–3 and
  the ELITEA-2440/2441 sibling tests' Step 1 almost verbatim — reuse that
  sequence).
- `SkillDetailPage.send_test_message()` / `wait_for_test_response()` /
  `get_last_test_response()` for steps 1–2 — all pre-existing, no changes
  needed.
- New `SkillDetailPage` fields (additive-only, no existing method body
  touched): `read_out_button = LocatorDescriptor(testid="chat-read-out-button")`,
  `copy_action_button = LocatorDescriptor(testid="chat-copy-button")` —
  mirror `ChatPage`'s existing fields of the same name/testid
  (`automation/pages/chat_page.py:526`, `:481`) exactly, since they're the
  same underlying `ApplicationAnswer.jsx` component.
- Step 3 assertion (recommended shape): assert
  `read_out_button.is_enabled()` and `copy_action_button.is_enabled()` (state
  layer), then click each and assert its effect — `copy_action_button.click()`
  → assert the toast text contains "copied to the clipboard"
  (`SkillDetailPage.version_toast_message`/`toast-message` testid, reused
  from the Save-As-Version flow already wired); `read_out_button.click()` →
  assert `page.get_by_test_id("chat-voice-mini-player")` becomes visible
  (behavior layer). Stop/dismiss the player afterward (`chat-voice-play-stop-button`)
  so the test doesn't leave TTS "playing" into the next assertion.
- Cleanup: `skill_api.delete_skill(skill_id)` in a `try`/`finally`.
