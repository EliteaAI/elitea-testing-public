# Test Case: Chat — Voice Mini-Player: Play/Stop toggle and controls disabled during read-out playback

## Metadata
- **TMS ID**: GAP-018
- **Linked Story**: none — coverage-gap case (cov60 campaign, `.agents/automation-board/batches/cov60/cases/GAP-018/`); no numbered TMS/tracker issue exists for the case itself, only the local board ledger
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project "Bugs & Features" / `${ELITEA_PROJECT_ID}`)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths (`auth_state` fixture)
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost: automatic via `auth_state`).
- App running on `http://localhost:5173`.
- A TTS model is configured on the target environment — confirmed live: voice features are enabled by default on localhost (`VOICE_FEATURES_ENABLED` true, no per-test setup needed); the TTS model itself is resolved automatically via `useListModelsQuery({section: 'tts'})` inside `useReadAloud`, independent of the chat LLM model selected (observed chat model `GPT-5.4-mini`, unrelated to TTS voice resolution).
- A conversation is open with **≥2 completed AI answers** containing prose (speakable text) — each shows its own `chat-read-out-button`.

## Test Data

### reuse-existing
- No credentials/env vars needed beyond `auth_state` — voice/TTS is pre-configured on localhost.

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh conversation with two prompts, confirmed live to work exactly as the case's Test Data table suggests: `"Say hello in one sentence."` then `"Now say goodbye in one sentence."`.
- **Timing caveat found during exploration (important for the implementer):** a genuinely one-sentence answer (e.g. `"Goodbye!"`) can finish TTS playback in **under ~1 second** — fast enough that a test polling every second (or asserting "Stop state" without a tight wait) can race past the `isPlaying=true` window entirely and only ever observe the before/after idle state, never the actual "Stop" state. Confirmed live: clicking Play on the short "Goodbye!" answer, the mini-player had already auto-hidden (playback complete, `isPlaying` back to `false`) by the time of the very next poll ~1s later.
  **Recommendation:** use a longer prompt for the answer that plays (e.g. *"Write a 6 to 8 sentence paragraph describing a peaceful morning by a lake."* — confirmed live to give several seconds of stable "Stop" state to assert against), while the "other" answer (used only for the cross-message-disable assertion, step 5 of the case) can stay short. Alternatively/additionally, don't rely on a fixed poll interval — assert the Stop-state DOM condition with the framework's own wait-for (`expect(...).to_have_attribute` / a `page.wait_for_function` on the button's disabled/icon state), which naturally tolerates a short playback window.

## Test Steps

1. Navigate to Chat, create a new conversation, send two prompts (a short one, then a longer one — see Test Data), wait for both to finish streaming.
   - **Verify**: two assistant answers rendered; `chat-read-out-button` present and **enabled** on both (confirmed live: `.disabled === false` on both buttons once each answer's generation completes — gated by `isProcessing` false + `realAnswer` non-empty + `speakingMessageId` null, per `ApplicationAnswer.jsx:827-832`).
2. Hover the most recent (longer) assistant answer and click its `chat-read-out-button`.
   - **Verify**: `chat-voice-mini-player` appears (confirmed: `showPlayer` branch fires — `onAutoSpeak` sets `speakingMessageId` + `setShowPlayer(true)`), containing `chat-voice-play-stop-button` and `chat-voice-settings-button`. **Important nuance confirmed live, beyond the case's literal step 2 wording:** clicking Read-out alone does **not** start audio playback — it only stages the text and reveals the mini-player in the **idle/Play** state (`isPlaying` stays `false` until the Play button itself is clicked, per `useReadAloud.hooks.js`'s `onPlay` callback which is wired to `chat-voice-play-stop-button`'s `onClick`, not to the read-out click). This matters for automation: playback truly begins only after the NEXT step (clicking `chat-voice-play-stop-button`).
3. Click `chat-voice-play-stop-button` (currently in Play/idle state) to start playback, then immediately inspect it.
   - **Verify**: button now renders the **Stop** icon (confirmed live: SVG `<path d>` matches `EliteaUI/src/assets/stop_record.svg`'s path, replacing `play.svg`'s path) and its tooltip reads **"Stop speaking"** (confirmed via screenshot — MUI `StyledTooltip` shown after the click's pointer stays over the button: `isPlaying ? 'Stop speaking' : 'Start speaking'`, `VoiceControlButton.jsx:44-47`).
4. While audio is still playing, inspect `chat-voice-settings-button`.
   - **Verify**: disabled (confirmed live: `.disabled === true`, `disabled={isPlaying}` — `VoiceControlButton.jsx:75`).
5. While audio is still playing, inspect the **other** answer's `chat-read-out-button`.
   - **Verify**: disabled (confirmed live: `.disabled === true`, driven by the `!!speakingMessageId` branch of `ApplicationAnswer.jsx:827-832`).
   - **Finding beyond the case's literal wording (Axis 2 — see Coverage Map):** the disable condition `!!speakingMessageId` is **not** scoped to "the other answer" — it disables **every** `chat-read-out-button` on the page, **including the currently-speaking answer's own button** (confirmed live: with 3 AI answers rendered and the 3rd one playing, all 3 `chat-read-out-button` elements read `.disabled === true` simultaneously, not just the 2 that weren't clicked). The case's Pass criteria ("every OTHER answer's button is disabled") is satisfied by this — it's a superset, not a contradiction — but the automated assertion should check **all** rendered `chat-read-out-button` elements are disabled while `isPlaying`, not just the ones excluding the currently-speaking message, to fully capture the real (stricter) behavior.
6. Click `chat-voice-play-stop-button` (currently Stop) to stop playback.
   - **Verify**: playback stops; confirmed live per `useReadAloud`'s cleanup effect (`if (!isPlaying) { setSpeakingMessageId(null); setSpeakingSegments(null); setShowPlayer(false); }`): the mini-player **disappears entirely** (`chat-voice-mini-player` count → 0) rather than resetting in-place to a visible Play icon — confirmed live, `showPlayer` unmounts the whole component. (The case's expected-result wording "returns to the Play state" is satisfied in the sense that, if re-opened via Read-out again, it starts in the Play/idle icon — but the visible artifact right after Stop is "gone", not "visible-showing-Play".)
7. After stopping, re-inspect every rendered `chat-read-out-button`.
   - **Verify**: all are **enabled** again (confirmed live: `.disabled === false` on all 3, `speakingMessageId` cleared). `chat-voice-settings-button` is not present to re-check (mini-player unmounted per step 6) — this is expected, not a gap.
8. Click the same answer's `chat-read-out-button` again, then click `chat-voice-play-stop-button` while it shows Play, confirm Stop state, then click it again to return to Play/gone.
   - **Verify**: round-trips cleanly a second time — confirmed live: mini-player reappears in Play state → clicking shows Stop icon (SVG path match) → clicking again returns to fully-hidden with all read-out buttons re-enabled. No accumulation/leak of state observed across the two full cycles.

## Expected Results
- `chat-voice-play-stop-button` renders the Play icon + tooltip "Start speaking" when idle, and the Stop icon + tooltip "Stop speaking" while `isPlaying` — confirmed via SVG path comparison and tooltip screenshot.
- `chat-voice-settings-button` is disabled exactly while `isPlaying` (`disabled={isPlaying}`) and enabled otherwise.
- **Every** `chat-read-out-button` on the page (not just "other" answers) is disabled while any message is speaking (`!!speakingMessageId`), and re-enabled once playback stops.
- `chat-voice-mini-player` appears when Read-out is clicked (idle/Play state, audio not yet started) and fully unmounts (not just resets) once playback stops — either via explicit Stop-click or natural completion.
- No console errors at any point in the flow (confirmed: zero `error`-level console entries across the full session, `get-console`/`get-network --status error` both clean).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: conversation with ≥2 AI answers, speakable text | setup exists | step 1 | step 1: 2× `chat-read-out-button` present+enabled | asserted |
| Test Data: tooltip values (`Start speaking`/`Stop speaking`/`Read out`) | tooltips match | steps 3, (idle tooltip) | step 3: screenshot + code cross-check; idle tooltip confirmed via separate hover+screenshot | asserted |
| Test Data: disabled conditions (read-out / settings) | conditions match code | steps 4–5 | steps 4–5: `.disabled` reads matched against `ApplicationAnswer.jsx`/`VoiceControlButton.jsx` source | asserted |
| 1 Send 2 prompts, wait for streaming | 2 answers rendered, read-out present+enabled | step 1 | step 1 | asserted |
| 2 Click last answer's read-out | mini-player appears with play-stop + settings | step 2 | step 2: `chat-voice-mini-player` count, child testids present | asserted *(enriched — see Axis 2: clarified this step alone does not start audio)* |
| 3 Inspect play-stop while playing | Stop icon + "Stop speaking" tooltip | step 3 | step 3: SVG path match + tooltip screenshot | asserted |
| 4 Inspect settings while playing | disabled | step 4 | step 4: `.disabled === true` | asserted |
| 5 Inspect OTHER answer's read-out while playing | disabled | step 5 | step 5: `.disabled === true` | asserted *(enriched — see Axis 2: ALL read-out buttons disabled, not just "other")* |
| 6 Click play-stop to stop | returns to Play state, per `useReadAloud` mini-player hides + `speakingMessageId` clears | step 6 | step 6: mini-player count → 0, confirmed against hook source | asserted |
| 7 Re-inspect both read-outs + settings after stop | both read-outs enabled; settings enabled if present | step 7 | step 7: `.disabled === false` on all read-outs; settings correctly absent (component unmounted) | asserted |
| 8 Round-trip the toggle a second time | mini-player reappears, Stop→Play round-trips again | step 8 | step 8: repeated svg-path + count checks | asserted |
| Expected Final State: playback stopped, mini-player hidden/Play, `speakingMessageId` cleared, all read-outs enabled, no leftover audio | — | steps 6–8 | steps 6–8 | asserted |
| Pass/Fail criteria (toggle, disable/enable, mini-player appear/hide) | — | all steps | all steps | asserted — no defect found, all criteria hold as specced (with the two Axis-2 clarifications above being stricter/superset findings, not contradictions) |

### Axis 2 — Analyst additions

- Step 2 clarifies that clicking Read-out alone only **stages** playback (shows the mini-player in Play/idle state) — it does not itself start audio. *Added: the case's step 2 wording ("Read-out starts... `chat-voice-mini-player` appears") could be misread as "playback begins immediately"; confirming the actual state machine (staged vs. playing) prevents the implementer from writing an assertion against the wrong intermediate state.*
- Step 5 additionally asserts that **every** `chat-read-out-button` — including the currently-speaking answer's own button — is disabled while `isPlaying`, not only the "other" answer's. *Added: directly observed in the live DOM (`ApplicationAnswer.jsx`'s disable condition is unconditional on `!!speakingMessageId`, with no `messageId !== speakingMessageId` guard); asserting the full set is strictly more correct and would catch a future regression that accidentally scoped the disable to "other messages only".*
- Step 6 documents that the mini-player fully **unmounts** on stop (rather than resetting visually to a Play icon) — *added: this is the literal, code-confirmed behavior of `useReadAloud`'s `useEffect` on `isPlaying`, and differs subtly from a naive reading of the case's "returns to the Play state" wording; the implementer should assert `to_have_count(0)` on `chat-voice-mini-player`, not a Play-icon check on it.*
- Test Data documents a timing/flakiness hazard (very short answers can finish playback in under 1 second) as an added automation caution — *added: observed directly during exploration (the "Goodbye!" answer's mini-player was already gone one second-poll later); this is not a product defect, but a naive test using a fixed poll/sleep against a short answer would be flaky through no fault of the product.*
- No console-error assertion was in the original case text; added it as a side-channel check — *zero console errors or failed network requests observed across the whole session (`get-console`, `get-network --status error` both clean); no defect to report on this axis.*

## Cleanup

1. Exploration created one scratch conversation (id `8850`, "Say hello one sentence.") on the shared DEV backend via localhost — attempted an API delete (`DELETE /elitea_core/conversation(s)/prompt_lib/{project}/{id}` via Bearer token) but got `404` (the conversation-delete endpoint requires the cookie-authenticated `ConversationAPI` client per `.claude/rules/api-patterns.md`, not the generic Bearer `APIClient` used for the quick attempt). Left the conversation in place — consistent with the many other scratch conversations already visible in the dev sidebar from prior exploration sessions (not a novel cleanup burden). **Implementer's test should use the existing `conversation_api` fixture's `delete_conversation(int(conv_id))` in a `finally` block**, exactly as `test_voice_configuration.py`'s existing tests already do — that path is cookie-authenticated and known to work.
2. No pipeline/agent/toolkit state was touched — nothing else to clean up.

## Concrete Handles (discovered during exploration)

All four testids the case names are **already wired, already used by an existing page-object method, and already on `main`** — no `add-data-testid` work needed for this case.

| Element | Locator | PROVENANCE | Notes |
|---|---|---|---|
| Read-out (speaker) button, per AI answer | `[data-testid="chat-read-out-button"]` — existing `ChatPage.read_out_button` field / `click_read_out()` method | on-main ✓ (`EliteaAI/EliteaUI@a3f9b260`) | Renders once per AI answer with speakable text — a conversation with N AI answers has N of these in the DOM simultaneously. Disabled state must be checked per-instance (`[...locator.all()]` → `.is_disabled()` each), not just the one the test clicked. |
| Voice mini-player container | `[data-testid="chat-voice-mini-player"]` — existing `ChatPage.voice_mini_player` field / `is_voice_mini_player_visible()` | on-main ✓ (`EliteaAI/EliteaUI@a3f9b260`) | Confirmed: mounts on Read-out click (Play/idle state), fully unmounts on Stop — assert `to_have_count(0)`/`(1)`, not just visibility, since it's not merely hidden. |
| Play/Stop toggle button | `[data-testid="chat-voice-play-stop-button"]` — existing `ChatPage.voice_play_stop_button` field | on-main ✓ (`EliteaAI/EliteaUI@a3f9b260`) | **No existing page-object method calls this yet** (existing tests only check its *presence* via `is_tts_playing()`, never click it). Implementer needs a new method, e.g. `click_play_stop()`. State read: SVG `<path d="...">` distinguishes Play (`M13 8C13.0003...`) vs Stop (`M12 4.72727V11.2727...`) — do NOT assert on the tooltip text alone as the primary signal (MUI tooltips only render in the DOM while actually hover-shown, timing-fragile for automation); prefer the SVG path or, if available, an assertion on the button's accessible/tooltip title via Playwright's own hover-then-`get_by_role('tooltip')` API. Disabled-state note: this button was **never observed disabled** during exploration (only settings + read-out buttons gate on `isPlaying`/`speakingMessageId`) — no disabled-state assertion needed for the toggle itself. |
| Voice settings (gear) button | `[data-testid="chat-voice-settings-button"]` — existing `ChatPage.voice_settings_button` field / `open_voice_settings_from_tts()` | on-main ✓ (`EliteaAI/EliteaUI@a3f9b260`) | `open_voice_settings_from_tts()` currently *clicks* it — for this case the implementer needs to read its `.disabled` state instead/as well, which the existing method doesn't expose. |

No new testids required. No `testid needed:` rows.

## Network Behavior

Voice playback for the model-TTS path is Socket.IO-driven (`tts_start`/`tts_audio_chunk`/`tts_done`/`tts_stop` events per `useTextToSpeech.hooks.js`), not plain HTTP — confirmed no new XHR/fetch requests fire on Play/Stop clicks (only the existing chat WebSocket traffic). Nothing for the implementer to `wait_for_response()` on; the play/stop and disabled-state transitions are pure client-side React state driven by the socket events, so wait on the DOM condition itself (icon/disabled state), never on a network call.

## Known Defects Found During Exploration

None found. All 8 case steps + the Pass/Fail criteria hold exactly as specced (the two Axis-2 findings — "clicking Read-out doesn't itself start playback" and "ALL read-out buttons disable, not just the other one" — are stricter/more-precise readings of the intended behavior, not defects; both are consistent with, not contradicting, the case's own Pass criteria).

## Blocked Steps

None. All 8 case steps executed to completion against the live local environment, twice (steps 2–7 once, then the step-8 round-trip a second full cycle).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`) — no `add-data-testid` work needed, all 4 handles exist on `main` already.
- Recommended home: extend `automation/tests/ui/voice/test_voice_configuration.py` (same file as the existing TC1–TC5 voice tests) as a new `test_play_stop_toggle_and_disabled_controls` method on `TestVoiceConfiguration` — it already imports `ChatPage` and follows the same 2-prompt-conversation setup/teardown pattern; this case's observable (play/stop toggle + cross-message disable) is NOT covered by any of the existing 5 tests (TC1 only opens Voice Settings via `open_voice_settings_from_tts()` without ever inspecting the play/stop button's own state or the settings button's disabled state; TC5 only checks the mini-player is absent by default) — confirmed by reading the full file, hence `ready-for-automation` rather than `extend-existing` (the observable itself is new, even though the file/fixtures are shared).
- New page-object method needed: `ChatPage` has no method to click `chat-voice-play-stop-button` yet (only to check its presence via `is_tts_playing()`). Add e.g. `click_play_stop_button()` and, ideally, a state-reading helper (`is_play_stop_showing_stop_icon()` via the SVG-path check, or `get_read_out_buttons_disabled_states()` returning a list across all rendered instances) rather than reaching into `page.locator()` directly from the test body (per `.claude/rules/page-objects.md`).
- Wait strategy: after clicking `chat-voice-play-stop-button` to start playback, wait on the button's own icon/attribute change (Playwright auto-waiting `expect(locator).to_have_attribute(...)` or a short `page.wait_for_function` on the SVG path) rather than a fixed sleep — and use a long-enough answer (see Test Data timing caveat) so the Stop-state window isn't racing playback completion.
- Multiple `chat-read-out-button` instances coexist in the DOM once ≥2 AI answers exist — always assert against the full `.all()` list (or explicitly index by conversation position), never assume a single-element locator.
