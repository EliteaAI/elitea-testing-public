---
name: Participants dropdown name-click inserts plain-text mention
description: Users-dropdown row click mentions correctly (appends, doesn't replace); distinct from composer @-popper; fill() destroys it
type: project
---

Clicking a participant's NAME (not the delete icon, not "All users") inside
the chat Users participants dropdown (`UserMenu.jsx` row `onClick`) correctly
inserts `"@DisplayName "` into the message composer — confirmed live,
ELITEA-2173/2174 (chat-remaining-w10). This is a DIFFERENT code path than the
composer's own typed-`"@"` mention popper (`UserMentionList.jsx`,
`onSelectUserMention` — ELITEA-2168's mechanism) even though both eventually
write into the same composer.

Key findings:
- Clicking a SECOND user's name (after reopening the dropdown) correctly
  **appends** to the existing mention text, space-separated
  (`"@User1 @User2 "`), not replaces.
- The inserted text has **no highlighting/formatting** — plain, unstyled text,
  same as the composer's own `@`-typed mentions. If a TMS case expects
  "highlighted/formatted", that's case-text drift (filed as CLARIFICATION,
  e.g. issue #1558), not a product defect.
- **`fill()` on the composer REPLACES the whole value**, silently destroying
  an in-progress mention. Always `click()` + `press("End")` +
  `press_sequentially(text)` to append after a dropdown-inserted mention —
  never `.fill()` once a mention is present.
- The row's own delete icon (hover-only, `visibility:hidden` by default)
  does NOT intercept a plain `.click()` on the row's testid element at rest —
  no `.hover()` needed before clicking a row's name to mention it (only
  needed before clicking ITS delete icon).
- Zero new testids needed for this whole family — `chat-participant-row-
  user_{userId}_` (dynamic PARTICIPANT_ROW template, ELITEA-2168) already
  covers the row; a single new page-object method
  (`mention_user_via_participants_dropdown`) suffices.
- The "All users" footer item's own mention-insertion is BROKEN (issue #1119,
  separate bug, unrelated to individual name rows which work correctly).

Related: `.agents/memory/qa-engineer/agent_instructions_tilde_mention_quirks.md`,
`test-specs/chat-interface/l2_participants-dropdown-click-name-inserts-mention_ELITEA-2173.md`.
