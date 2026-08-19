---
name: Chat response header participant-name has no testid
description: ApplicationAnswer.jsx's "<Name> to Message" header row carries no testid on main or automation/testids — an "attributed to <Name>" assertion cannot be written under the testid-only policy without first adding one
type: feedback
---

## What happened

ELITEA-2208/2470 fix round 1 (PR #1600, 2026-08-19). The AFS Coverage Map
row for "Type a message and send" claimed the shipped test would assert
'header shows "to \<Pipeline Name\>" attribution' — inherited via copy-paste
from the already-merged ELITEA-2207/2469 sibling AFS, which made the same
claim and also never implemented it (its covering test
`test_add_agent_via_hash_search_joins_participants_and_responds` has no
attribution assertion either).

Checked `EliteaUI/src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx`
directly (fresh `git fetch origin`, both `main` and `automation/testids`):
the header row renders `{participantName}` + `"to"` + `"Message"` as plain
MUI `Typography` elements inside `styles.headerRow`/`styles.headerLeft` —
**no `data-testid` anywhere in that block.** The only testids in the whole
component are `chat-message-item` (the outer `<li>`), `chat-answer-content`,
`chat-artifact-file-list`, and the four hover-action buttons
(copy/regenerate/delete/read-out).

## Why it matters

Any future case whose expected result mentions "the response is attributed
to \<X\>" or "the header shows \<X\>" for an AI/agent/pipeline message cannot
be honestly automated as a real assertion today under this project's
testid-only locator policy (no fallback ladder). Two honest options:

1. **Amend the case/AFS wording** if the underlying behavior is already
   proven some other way (e.g. single-participant construction + message-
   count growth, as this fix round did) — don't file a `testid needed` for
   a string a case doesn't actually ask to see.
2. **Add a real testid** to the header row (`add-data-testid` on
   `ApplicationAnswer.jsx`'s `participantName` Typography or its wrapping
   `Box`) only when a case's own wording genuinely requires reading that
   exact string — this is a shared component across every message type
   (agent/pipeline/sub-agent), so scope the testid to that one Typography,
   not the whole header row, and check for `isSwarmChild`/sub-agent
   variants nearby (a separate "Sub-agent response" branch exists ~line
   580 with its own header shape).

`MESSAGE_SENDER_NAME` (`chat-message-sender-name`, in `chat_page.py`) is a
DIFFERENT testid on a DIFFERENT component (`UserMessage.jsx`) — it identifies
the human *sender* of a USER message, not the *recipient/participant*
attribution on an AI/agent/pipeline response. Don't reach for it by
association; it resolves nothing on `ApplicationAnswer.jsx`.
