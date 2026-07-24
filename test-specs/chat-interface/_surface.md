# Chat Interface — exploration digest

Seeded 2026-07-24 (GAP-018, first case in this batch to touch the chat voice
mini-player sub-surface in depth). A handle *cache*, not a substitute for
execution — verify each handle live as you use it.

## Core chat handles (confirmed live)

- **New-conversation trigger**: sidebar `[data-testid="sidebar-create-button"]`
  (labelled "Chat" in the sidebar) — existing `ChatPage.click_create_new_conversation()`.
- **Message input**: `[data-testid="chat-message-input"]` (a `<textarea>`) —
  existing `ChatPage` send-message flow. Enter submits.
- **Message list items**: `[data-testid="chat-message-item"]` (one per user OR
  AI message, alternating) — existing `ChatPage.messages_container`. A
  conversation with N prompts has 2N message items (user + AI pairs); AI-only
  elements (e.g. `chat-read-out-button`) render inside a subset of these, so
  don't assume `messages_container.nth(i)` maps 1:1 to "AI answer #i".
- **Conversation URL**: `/chat/{conversation_id}?name=...` — id extractable via
  regex `r"/chat/(\d+)"` on `page.url` (existing `capture_conversation_id()`
  helper pattern in `test_voice_configuration.py`).

## Voice / TTS mini-player sub-surface (GAP-018 — full findings)

- **Source**: `EliteaUI/src/[fsd]/features/chat/ui/voice-control-button/VoiceControlButton.jsx`,
  `.../voice-mini-player/VoiceMiniPlayer.jsx`,
  `.../lib/hooks/useReadAloud.hooks.js` + `useTextToSpeech.hooks.js`.
  Read-out trigger lives in `.../chat-box/ApplicationAnswer.jsx`.
- **State machine (important — do not assume "click Read-out = playback starts"):**
  1. Click `chat-read-out-button` → **stages** the answer's text and reveals
     `chat-voice-mini-player` in the **idle/Play** state. Audio has NOT started.
  2. Click `chat-voice-play-stop-button` (idle) → `onPlay()` → `speak()` →
     `isPlaying` becomes `true`: icon flips to Stop (SVG path
     `M12 4.72727V11.2727...`, from `stop_record.svg`), tooltip "Stop speaking",
     `chat-voice-settings-button` becomes disabled, and **every**
     `chat-read-out-button` on the page (not just other messages') becomes
     disabled (`!!speakingMessageId` in `ApplicationAnswer.jsx`, unconditional —
     no `messageId !== speakingMessageId` guard).
  3. Click `chat-voice-play-stop-button` (Stop) → `isPlaying` false → the
     `useReadAloud` cleanup effect **unmounts** `chat-voice-mini-player`
     entirely (not a visual reset to Play) and clears `speakingMessageId`,
     re-enabling every read-out button + the settings button (which is gone
     along with the mini-player).
  4. Playback also ends naturally on its own once the TTS audio finishes —
     same cleanup effect fires. **A short one-sentence answer can finish in
     under ~1 second** — use a longer answer (6+ sentences) if a test needs a
     reliable window to assert the Stop state, or wait on the DOM condition
     itself rather than a fixed poll/sleep.
- **Icon disambiguation** (tooltips are timing-fragile — MUI only renders
  tooltip text in the DOM while actually hover-shown): the two SVG `<path d>`
  values are stable and cheap to compare —
  Play = `M13 8C13.0003 8.11753...` (`play.svg`),
  Stop = `M12 4.72727V11.2727...` (`stop_record.svg`).
- **Testids** (all four already on `main`, `EliteaAI/EliteaUI@a3f9b260`, fresh-fetched 2026-07-24):
  `chat-read-out-button` (per-AI-answer, N instances coexist),
  `chat-voice-mini-player` (single container, mounts/unmounts — not just hidden),
  `chat-voice-play-stop-button`, `chat-voice-settings-button`.
- **Existing page-object coverage** (`automation/pages/chat_page.py`):
  `click_read_out()`, `is_voice_mini_player_visible()`, `wait_for_tts_controls()`,
  `open_voice_settings_from_tts()`, `trigger_tts_and_open_settings()`,
  `is_tts_playing()` (misnomer — actually just checks the play/stop button is
  *present*, not that `isPlaying` is true). **Gap**: no existing method clicks
  `chat-voice-play-stop-button` itself, and no method reads its
  Play-vs-Stop icon state or any button's `disabled` state — see
  `l3_voice-mini-player-play-stop-toggle-and-disabled-controls_GAP-018.md`
  § Automation Hints for the exact methods to add.
- **Existing test coverage** (`automation/tests/ui/voice/test_voice_configuration.py`,
  merged to `automation/base`): TC1–TC5 cover the Voice Settings **dialog**
  (voice/speed/volume selection, Apply/Cancel, Personalization↔Chat sync,
  mini-player-absent-by-default) — none of them click or inspect the
  play/stop toggle's own state or any disabled-state assertion. Different
  observable, not overlapping — confirmed by full-file read, 2026-07-24.

## Network / timing

- Model-TTS playback is **Socket.IO-driven** (`tts_start`/`tts_audio_chunk`/
  `tts_done`/`tts_stop`), not HTTP — no XHR/fetch to `wait_for_response()` on
  for play/stop transitions; wait on the DOM/icon state instead.
- Auth on localhost is fully transparent (`VITE_DEV_TOKEN` build-time env) —
  works identically whether driven via Playwright MCP or a fresh CDP
  (`browser-verify`) session with no storage state at all; no login flow to
  navigate around for chat cases.
