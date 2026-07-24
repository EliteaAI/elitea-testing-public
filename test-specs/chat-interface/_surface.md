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

## Folders + conversation-item reuse (ELITEA-2098)

- **`ConversationItem.jsx` is the SAME component whether rendered under a date-group
  (`DateGroup.jsx`, e.g. "Today") or inside a folder accordion (`FolderAccordion.jsx`)** — the
  `chat-conversation-item-{id}` testid and its `data-active` state attribute (from ELITEA-2114) work
  identically in both contexts, confirmed live. No folder-aware variant of `CONVERSATION_ITEM` /
  `is_conversation_active()` is needed — just scope the `.locator()` chain off
  `chat.get_folder_item(folder_id)` instead of `chat.get_conversation_group_header(group)`.
- **A folder auto-renders EXPANDED (`data-expanded="true"`) whenever it contains the conversation
  the current URL points at** — this is re-derived on every navigation/reload, not a one-time
  default. A test that needs a genuine collapsed→expanded transition for its own "click to expand"
  step must force-collapse first (click the scoped `chat-folder-icon` — confirmed to toggle
  reliably in both directions) rather than assume the folder starts collapsed.
- **Click-target risk for `expand_folder()`/`get_folder_item(folder_id).click()` on a
  EXPANDED + NON-EMPTY folder**: the testid sits on the whole outer accordion (header + body, per
  the ELITEA-2132 design). Collapsed, or expanded-but-empty (ELITEA-2132's only tested shape), a
  center-click safely lands on the header. Expanded AND non-empty (this case's shape), the
  bounding box spans the conversation list too — a blind center-click risks landing on a
  conversation row instead of the header. Untested in the suite so far (no existing test does this);
  scope to `chat-folder-icon` instead when a future test needs to COLLAPSE a non-empty, already
  expanded folder.
- **Moving a conversation into a folder via a direct API `PUT`** (`/elitea_core/conversation/
  prompt_lib/{project_id}/{id}` body `{"folder_id": <id>}`, the SAME endpoint the app's own
  `useMoveToFolderConversation.hooks.js` calls via the `conversationEdit` RTK mutation) is safe —
  it's a metadata edit, not a message send, so ELITEA-2095's defect #691 (first-message-to-
  zero-message-conversation) does not apply. **Requires a `page.reload()` afterward** — the app's
  Redux/RTK state doesn't reactively pick up a side-channel API mutation.
- **API inconsistency (not a defect)**: `ConversationAPI.get_conversation(id)` (the singular
  single-conversation endpoint) returns `folder_id: null` even for a conversation genuinely inside a
  folder; the folder-list endpoint's nested `conversations[].folder_id` is correct. Use the latter
  if a future case needs to verify folder membership via API.
- **Doc-drift (not a product defect)**: `automation/CLAUDE.md`'s API-quirks table claims conversation
  delete uses a PLURAL path; the real, merged `ConversationAPI.delete_conversation()` uses SINGULAR
  (confirmed live: plural 404s, singular succeeds `204`). Trust the client code, not that table row.

## Expanded PARTICIPANTS panel (distinct from the collapsed badge's popper — don't confuse the two)

- **Two entirely different UI surfaces render a "Users" list, and only one had a testid'd avatar
  before ELITEA-2098:**
  1. **Collapsed badge → click → small popper** (`chat-participants-badge-users` →
     `chat-participants-badge-button` → `chat-participants-popper`). Renders via
     `UsersParticipantDropdown/UserMenu.jsx`, whose own `<UserAvatar>` call carries **NO testid at
     all** (confirmed live — genuine, still-open gap, not touched by ELITEA-2098 since that case
     didn't need this surface).
  2. **The real "Participants" panel** (title "Participants", collapse/expand toggle with
     `DoubleLeftIcon`/`DoubleRightIcon`), which switches between `CollapsedPerticapantsList` (icon
     rail) and `ExpandedParticipantsList` (full names — this is where `UserParticipantItem.jsx`'s
     `chat-participants-users-avatar` testid, added back in ELITEA-2095, actually lives). Before
     ELITEA-2098, the ONLY way to reach this expanded state was `chat_page.py`'s legacy `expand_
     participants_panel()`/`is_participants_panel_expanded()` — raw `get_by_text("Participants")` +
     JS-evaluate button-hunting (tracked tech debt, still present, not removed by this pass).
- **ELITEA-2098 added 2 real testids** closing that gap: `chat-participants-panel` (container,
  `data-expanded` state attribute) + `chat-participants-panel-toggle-button` (the collapse/expand
  `IconButton` — one stable testid regardless of which chevron icon renders, per the
  testid=identity/icon-choice=cosmetic-state ruling). `EliteaAI/EliteaUI@d1b89d8a` on
  `automation/testids`, confirmed live via HMR both directions.
- **Project choice is load-bearing for BOTH participants surfaces**: `showUsersSection =
  !isPrivateProject` in `CollapsedPerticapantsList.jsx` omits the whole Users section for the
  account's own default Private project (`399`). Use the Team project (`471`, "Elitea Testing
  Team") for any case that needs a real participant to render — same precondition ELITEA-2095/2094
  already established, re-confirmed live by ELITEA-2098.

## Network / timing

- Model-TTS playback is **Socket.IO-driven** (`tts_start`/`tts_audio_chunk`/
  `tts_done`/`tts_stop`), not HTTP — no XHR/fetch to `wait_for_response()` on
  for play/stop transitions; wait on the DOM/icon state instead.
- Auth on localhost is fully transparent (`VITE_DEV_TOKEN` build-time env) —
  works identically whether driven via Playwright MCP or a fresh CDP
  (`browser-verify`) session with no storage state at all; no login flow to
  navigate around for chat cases.
