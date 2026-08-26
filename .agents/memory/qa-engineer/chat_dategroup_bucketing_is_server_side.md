---
name: Chat date-group bucketing is server-side, not client
description: This Week/Older sections can't be reached via clock-mocking or API backdating — data must genuinely age
type: feedback
---

Analyzing ELITEA-2096/ELITEA-2097 (open conversation from This Week /
Older sidebar sections): confirmed via source read
(`EliteaUI/src/[fsd]/features/chat/conversation-list/api/
conversationList.api.js:47-91`) that the Today/This-Week/Older bucketing
sent to `GET .../conversations/prompt_lib/{project_id}?grouped=true` is
computed **server-side** from the conversation's real `created_at`, not by
client-side date math. This means:

- Playwright `page.clock` (or any client-time trick) has ZERO effect on
  which bucket a conversation renders in — don't try it, it looks like it
  should work (timing control is normally fidelity-compliant) but doesn't
  touch the actual grouping logic.
- The `ConversationUpdate` API schema has no timestamp field at all — you
  cannot backdate a conversation via the API either.
- The DEV environment resets/gets cleaned frequently enough that
  non-today conversations essentially never exist (every AFS in this area
  deletes its own seeded conversations in `finally`) — don't assume aged
  data will be sitting around.

**Verdict for any This-Week/Older-dependent case with no aged data
available: `blocked`, not "find a workaround."** Full writeup:
`test-specs/chat-interface/_surface.md` § "Date-group bucketing... is
SERVER-computed" and the family AFS
`test-specs/chat-interface/l3_open-existing-conversation-this-week-older-sections_ELITEA-2096.md`.

Related, same session: `automation/CLAUDE.md`'s "API Quirks" table claims
conversation DELETE is an exception that uses the plural path — this is
STALE/WRONG. Confirmed live: plural `DELETE .../conversations/...` 404s;
singular `DELETE .../conversation/...` is correct (204). The
`ConversationAPI.delete_conversation()` docstring already has this right;
only the top-level doc table is wrong.
