# Test Case (Family AFS): Chat – Composer Send-Button Visibility Toggle

**FAMILY AFS — covers TWO TMS cases describing the SAME flow at different
granularity.** ELITEA-2466 is a more granular superset of ELITEA-2179 (same
objective, same 5-step core, plus extra bottom-bar/focus-border/sender-
name-avatar detail). One live execution against the real system satisfies
both — see § Family Member Table below for the per-case step mapping.

## Metadata
- **TMS IDs**: ELITEA-2179 (priority `high` → `l1`), ELITEA-2466 (priority
  `critical` → `l0`) — pytest marker uses the higher of the two, `p0`.
- **Linked Story**: none (both cases' frontmatter: `requirements: []`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_streaming_response.py`
  (its own AFS:
  `test-specs/chat-interface/l2_streaming-response-progressive-display_ELITEA-2181.md`)
  — merged `origin/automation/base` (verified via `git show
  origin/automation/base:automation/tests/ui/chat/test_streaming_response.py`,
  byte-identical to the working-tree copy pre-edit).

**Not already-covered — a real gap, not a duplicate.** The covering test's
own Step 1 already proves the CORE send-button/empty-input toggle (absent
when empty -> visible on typing -> absent again on Backspace -> send clears
the input), so BOTH cases' central claim is largely proven there. But
neither case is fully subsumed:
- Neither case's own most literal claim — "waveform icon visible when the
  Send button is absent" — is asserted anywhere on the trunk. The covering
  test only proves ABSENCE of `chat-send-button` (`.count() == 0`); it never
  asserts that a DIFFERENT, specific element (the waveform/"enter speaking
  mode" button) is what actually renders in that slot. That distinction
  matters: `.count()==0` alone would pass identically whether a waveform icon
  render there or the slot goes empty — this AFS closes that gap with a
  positive assertion on the actual replacement node.
- ELITEA-2466 adds four observables the covering test never touches at all:
  the bottom-bar icon inventory (+/model/gear/mic/waveform), the composer's
  focus-border glow on click, the sent message's sender-name+avatar, and an
  explicit "neither button renders while streaming" check.

## Family Member Table

| TMS ID | Priority | Steps covered | Notes |
|---|---|---|---|
| ELITEA-2179 | high (`l1`) | 1-5 (its own 5-step table) | Subset of ELITEA-2466's flow; every one of its 5 steps has a 1:1 mapping onto this AFS's steps 1, 1, 3, 4, 5. |
| ELITEA-2466 | critical (`l0`) | 1-10 (its own 10-step table) | Superset — adds the bottom-bar icon inventory (its step 3), the focus-border check (its step 4), the sender-name/avatar check (its step 8), and an explicit streaming-absence check (implied by its step 9/10 sequencing). |

Per-step cross-reference (AFS step -> case step):

| This AFS step | ELITEA-2179 step | ELITEA-2466 step |
|---|---|---|
| 1 — Baseline: input empty, Send absent, waveform present, bottom-bar inventory | step 1 + step 2 (partial: absence only) | step 1, step 2, step 3 |
| 2 — Click into input, verify focus-border glow | — (not in 2179) | step 4 |
| 3 — Type one char, waveform -> Send | step 3 | step 5 |
| 4 — Delete char, Send -> waveform | step 4 | step 6 |
| 5 — Send full message; sender name+avatar, input cleared, Send absent | step 5 (partial: no name/avatar ask) | step 7, step 8, step 9 |
| 6 — Neither button renders while streaming | — (not explicitly asked; a corollary of 2179's own "Send absent" claim holding through the LLM-responding phase) | — (implied by step 9->10 sequencing) |
| 7 — Waveform reappears once generation completes | step 5 ("LLM begins responding") | step 10 |

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (both cases' own precondition: "User has an
  open conversation" / "User is logged in"). This AFS uses the existing
  `conversation_id` fixture (fresh, API-seeded conversation per test) — the
  SAME fixture the covering test's own `test_streaming_response_progressive_display`
  already uses, rather than the ambient/last-viewed "new chat" screen (which
  this session's own exploration found redirects unpredictably to a
  pre-existing conversation — a documented gotcha, not this case's subject).

## Test Data
- `SEND_TOGGLE_MESSAGE_TEXT = "Hello"` — short, unambiguous; this test only
  needs a real response to eventually complete (step 7), not a long one
  (contrast with the covering test's own `MESSAGE_TEXT`, a long-poem prompt
  chosen specifically to keep the stream open for its OWN progressive-growth
  assertions — a different need this AFS doesn't have).

## Test Steps

1. Open the conversation; verify the input is empty, the Send button is
   absent (`.count()==0`), the waveform/"enter speaking mode" button IS
   present, and the bottom-bar shows: `+` menu, model name, model-settings
   (gear) button, voice-input (mic) button.
   - **Verify**: `is_input_empty()` true; `send_button.count()==0`;
     `voice_mode_button` visible; `plus_menu_button`, `model_selector_name`,
     `model_settings_button`, `voice_input_button` all visible.
2. Click inside the input field.
   - **Verify**: the composer's focus-border container's `data-focused`
     attribute flips to `"true"`, and its computed `box-shadow` is non-`none`
     (live-confirmed value: `rgba(21, 255, 247, 0.2) 0px -5px 20px 0px` — a
     cyan glow, matching the case's "teal/cyan border" wording; implemented
     as a box-shadow + gradient-background effect, not a literal CSS
     `border-color`).
3. Type a single character (`"h"`).
   - **Verify**: `send_button` becomes visible; `voice_mode_button`'s count
     drops to 0 (mutually exclusive DOM nodes — SendButton.jsx renders
     exactly one, never a visibility toggle on a shared node).
4. Delete the character (Backspace).
   - **Verify**: `send_button`'s count drops to 0; `voice_mode_button`
     becomes visible again.
5. Type `SEND_TOGGLE_MESSAGE_TEXT` and click Send.
   - **Verify**: the sent message appears (`chat-message-item` at the
     pre-send count index) with a non-empty sender name
     (`chat-message-sender-name`) and a visible avatar
     (`chat-message-sender-avatar`); the input value is `""` immediately
     after send; `send_button.count()==0`.
6. While the response is streaming (immediately after step 5, before
   waiting for completion).
   - **Verify**: BOTH `send_button.count()==0` AND `voice_mode_button.count()==0`
     — UserInput.jsx renders a Stop control in that slot while
     `isStreaming` is true, not either of the two idle-state buttons.
7. Wait for the AI response to finish generating (`wait_for_ai_response`,
   the same dual completion signal — message appears + Copy button visible
   + non-transient content — the covering test's own Step 7 already uses).
   - **Verify**: `voice_mode_button` becomes visible again once generation
     completes (input is still empty).

## Expected Results
- The composer's send-button slot renders exactly one of two mutually
  exclusive controls (waveform vs. Send) based on whether the input has
  text, with zero overlap and zero gap (never both, never neither) EXCEPT
  during active streaming, when a Stop control takes that slot instead.
- The composer shows a teal/cyan focus glow while the input is focused.
- A sent message renders with the sender's name and avatar, and the input
  clears immediately.
- The waveform button's reappearance (both cases' final step) resolves once
  generation completes, not while the LLM is still streaming.

## Coverage Map

### Axis 1 — Case coverage (ELITEA-2179's 5 steps)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, open conversation | — | Setup | `conversation_id` fixture + `navigate_to_chat` | asserted |
| 1 Open conversation, verify input empty | Input field empty | AFS step 1 | step 1: `is_input_empty()` | asserted |
| 2 Verify Send button NOT visible; waveform visible far right | Send hidden; waveform visible | AFS step 1 | step 1: `send_button.count()==0` + `voice_mode_button` visible | asserted |
| 3 Click input, type 'h' | Waveform replaced by Send | AFS step 3 | step 3: `send_button` visible, `voice_mode_button.count()==0` | asserted |
| 4 Delete character | Send disappears; waveform reappears | AFS step 4 | step 4: `send_button.count()==0`, `voice_mode_button` visible | asserted |
| 5 Type 'Hello', click Send | Message appears; input cleared; waveform reappears; LLM begins responding | AFS steps 5-7 | step 5: message + input cleared + Send absent; step 6: neither button during streaming; step 7: waveform reappears at generation-complete (see Fidelity/Clarification note below) | asserted |

### Axis 1 — Case coverage (ELITEA-2466's 10 steps)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | Setup | `conversation_id` fixture | asserted |
| 1 Navigate to Chats, open conversation | Page loads | Setup | `navigate_to_chat` | asserted |
| 2 Input empty, Send NOT visible | Condition holds | AFS step 1 | step 1 | asserted |
| 3 Bottom bar: +/model+icon/gear/mic/waveform | Condition holds | AFS step 1 | step 1: all 5 handles visible | asserted |
| 4 Click input, focused with teal/cyan border | Control responds | AFS step 2 | step 2: `data-focused="true"` + non-`none` box-shadow | asserted |
| 5 Type 'h', waveform -> Send | Field accepts input | AFS step 3 | step 3 | asserted |
| 6 Delete char, Send -> waveform | Operation completes | AFS step 4 | step 4 | asserted |
| 7 Type 'Hello', click Send | Field accepts input | AFS step 5 | step 5 | asserted |
| 8 Message appears with sender name+avatar | Condition holds | AFS step 5 | step 5: `chat-message-sender-name`/`chat-message-sender-avatar` | asserted |
| 9 Input cleared, Send disappears | Condition holds | AFS step 5 | step 5: `input_value()==""`, `send_button.count()==0` | asserted |
| 10 Waveform reappears, response generating | Condition holds | AFS step 7 | step 7: `voice_mode_button` visible post-`wait_for_ai_response` | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` /
`out-of-scope`. All rows `asserted`.

### Axis 2 — Analyst additions
- Step 6 (neither button renders during streaming) — *added: neither case's
  steps table explicitly names this, but it is the direct corollary of
  ELITEA-2179's "Send disappears... waveform reappears" and ELITEA-2466's
  step 9->10 sequencing (Send disappears at step 9, waveform reappears at
  step 10, implying a genuinely button-less window in between — this AFS
  makes that window an explicit, asserted fact instead of an inferred gap).*
- Mutually-exclusive-DOM-node framing (assert via `.count()`, not just
  `.to_be_visible()`/`.not_to_be_visible()`) — *added: source-confirmed
  (`SendButton.jsx`) the two buttons are different DOM nodes, not one node
  toggling visibility; a visibility-only assertion would pass even if a
  regression left both mounted-but-hidden simultaneously, which `.count()`
  catches and a bare visibility check would not.*

## Fidelity Declaration
No substitutions. Every element (Send button, waveform button, mic button,
gear button, `+` button, model name, focus-border glow, sender name/avatar)
is read from the live DOM the real React app renders in response to a real
click/type/send. The "generation completes" wait (step 7) is a real
`wait_for_ai_response()` poll against the live streaming response — no
timing is faked, no response is fabricated.

**Clarification (both cases' step 5/10 wording, not a defect):** "waveform
reappears" + "LLM begins responding" read, at first glance, like the
waveform should reappear WHILE the LLM is actively streaming. Source- and
live-confirmed this is not how the component behaves:
`UserInput.jsx`'s footer renders `<SendButton>` (which is what hosts the
waveform state) only when `!isStreaming || isUploadingAttachments`; while
actively streaming, a Stop control renders in that slot instead — matching
this page object's own PRE-EXISTING `wait_for_generation_complete()`
docstring: *"The Speaking mode button appears when generation is complete...
During generation, a stop button is shown instead."* This AFS asserts the
live, self-consistent behavior (step 6: neither button during streaming;
step 7: waveform reappears once generation completes) rather than the
literal at-a-glance reading of the case text — per the reverse-masking
guard, asserting a stale/ambiguous reading over the live contract would be
masking in the opposite direction.

## Cleanup
`conversation_id` fixture owns creation/deletion of the seeded conversation
(same mechanism the covering test's own `test_streaming_response_progressive_display`
already relies on) — no additional cleanup needed.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` §
Locator policy). **Five new testids added this session** (all EliteaUI
`automation/testids`, not yet on `main` — human cherry-pick pending):

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Waveform / "enter speaking mode" button | `chat-voice-mode-button` | on-`automation/testids` ✓ only (new, `EliteaAI/EliteaUI@b84f4f8d`) | `SendButton.jsx`'s speaking-mode-entry branch; zero prior callers. |
| Microphone (dictation) button | `chat-voice-input-button` | on-`automation/testids` ✓ only (new, `EliteaAI/EliteaUI@b84f4f8d`) | `VoiceButton.jsx`'s mic `BaseBtn`; zero prior callers. |
| Model-settings (gear) button | `model-settings-button` | on-`automation/testids` ✓ AND `main` ✓ (pre-existing, `LLMModelSelector.jsx` default variant) | Zero prior page-object callers before this case (canon #511 first caller) — NOT the testid this session initially and mistakenly added on the unrelated `field` variant (reverted, `EliteaAI/EliteaUI@293d3aee`). |
| `+` menu button | `plus-menu-button` | on-`automation/testids` ✓ AND `main` ✓ (pre-existing, `PlusChatButton.jsx`) | Zero prior page-object callers before this case (canon #511 first caller). |
| Composer focus-border container | `chat-composer-focus-border` (+ `data-focused` state attribute) | on-`automation/testids` ✓ only (new, `EliteaAI/EliteaUI@bfdc3148`) | `UserInput.jsx`'s pre-existing gradient-border `Box`; zero new DOM node, state-via-`data-*` per this project's testid-identity policy. |
| Sent message's sender name | `chat-message-sender-name` | on-`automation/testids` ✓ only (new, `EliteaAI/EliteaUI@3762995c`) | `UserMessage.jsx`'s header `Typography`. |
| Sent message's sender avatar | `chat-message-sender-avatar` | on-`automation/testids` ✓ only (new, `EliteaAI/EliteaUI@3762995c`) | Wired via `UserAvatar`'s existing `testId` prop — zero new DOM node. |
| Send button (real) | `chat-send-button` | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused. |
| Model name text | `model-selector-name` | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused. |
| Sent/AI message item | `chat-message-item` | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused (`messages_container`). |

## Network Behavior
- Step 5's Send fires the same `POST .../conversations/.../messages` (or
  equivalent) mutation the covering test's own Step 1 already documents —
  not re-verified independently here (out of this AFS's own scope; the
  covering test's Step 1 already asserts the resulting message + input
  clear).
- Steps 1-4 (composer state toggling, focus) — zero network requests,
  pure client-side React state.

## Known Defects Found During Exploration
None. Every observable in both cases matches live product behavior exactly
(after the "waveform reappears" clarification above, which is a wording
nuance, not a functional defect).

## Blocked Steps
None. All steps executable via existing + newly-added testid'd handles.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Landed as a new test method in the covering file
  (`test_composer_send_button_toggles_with_empty_input_and_waveform_reappears`,
  tagged with BOTH TMS IDs via two `@allure.issue` decorators) — the
  existing `test_streaming_response_progressive_display` method is
  byte-identical, untouched.
- New page-object locators (`ChatPage`): `voice_mode_button`,
  `voice_input_button`, `model_settings_button`, `plus_menu_button`,
  `composer_focus_border`, plus two scoped string-constant sub-selectors
  `MESSAGE_SENDER_NAME`/`MESSAGE_SENDER_AVATAR` (used via
  `messages_container.nth(i).locator(...)`, the same scoped-sub-selector
  idiom `RENDERED_TABLE_ROW`/`MERMAID_NODE` already use elsewhere in this
  file).
- Reused verbatim: `chat.navigate_to_chat()`, `chat.is_input_empty()`,
  `chat.send_button`, `chat.message_input`, `chat.get_message_count()`,
  `chat.send_message()`, `chat.messages_container`,
  `chat.wait_for_ai_response()`, `chat.model_selector_name`.
