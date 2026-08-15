---
name: Participants dropdown name-click mention quirks
description: ELITEA-2173/2174 — clicking a Users-dropdown row's NAME (not delete icon) mentions that user; distinct from composer's own "@" popper
type: project
---

Implemented via `ChatPage.mention_user_via_participants_dropdown(user_id, timeout)`
(`automation/pages/chat_page.py`), additive alongside `open_remove_user_dialog()` /
`hover_participant_user_row()`.

- **Two genuinely different mention code paths exist — don't conflate them.**
  1. Composer's own typed-`"@"` mention popper (`UserMentionList.jsx` /
     `onSelectUserMention`) — what ELITEA-2168's test exercises.
  2. Users **participants dropdown**'s row NAME click (`UserMenu.jsx`'s
     `onClick` → `UsersParticipantDropdown`'s `handleSelectUser` →
     `NewChat.jsx`'s `onSelectParticipant(participant, true)` →
     `mentionUser('@<name> ')`) — what ELITEA-2173/2174 exercise. Same
     `PARTICIPANT_ROW` testid template as `open_remove_user_dialog()`, but
     click the row's content Box directly (no hover needed — the hover-only
     delete icon is `visibility:hidden` by default and never intercepts a
     plain click at the row's center).
- **Selecting a row auto-closes the popover** (`UsersParticipantDropdown`'s
  `handleSelectUser` sets `open=false` unconditionally). A second mention
  needs a fresh `open_participants_popover()` call — my new method already
  does this internally on every call, so looping it for N users "just
  works" without any special reopen logic in the test.
- **Second mention APPENDS, doesn't replace** — composer reads
  `"@User1 @User2 "` after two sequential row clicks (space-separated,
  confirmed live). `fill()` on the composer DESTROYS an in-progress
  mention (replaces the whole value) — always `click()` + `press("End")` +
  `press_sequentially(suffix)` to append text after a mention, never
  `fill()`.
- **Case-text drift, not a defect:** ELITEA-2173's own step 3 ("mention is
  highlighted/formatted") doesn't hold — the inserted mention is plain,
  unstyled text (same as the composer's own `"@"` path). Filed as
  CLARIFICATION #1558, not automated as a hard assertion.
