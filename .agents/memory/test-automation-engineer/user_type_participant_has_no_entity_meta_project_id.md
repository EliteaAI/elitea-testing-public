---
name: Users-type chat participant's entity_meta has no project_id — row uniqueId ends in a bare trailing underscore
description: getChatParticipantUniqueId() for a "user"-entity participant resolves to user_{id}_ (empty project_id segment), not user_{id}_{project_id} like agent/pipeline/toolkit participants — an AFS's own source-reading claim got this wrong; verify live before trusting the format.
type: feedback
---

`participants.helpers.js`'s `getChatParticipantUniqueId(participant)` builds
its trailing segment as `(participant.entity_meta?.project_id || '')`. For
agent/pipeline/toolkit/mcp participants this is always populated
(`application_4687_399`, confirmed live in `remove_agent_participant()`).
For a **Users**-type participant (`entity_name === 'user'`), the live API
response's `entity_meta` carries **only `id`** — no `project_id` key at
all (confirmed live, ELITEA-2170: `{'id': 43, 'entity_name': 'user',
'entity_meta': {'id': 43}, 'meta': {'user_name': 'Hrach Sargsyan', ...}}`).
The trailing `|| ''` fallback then produces an **empty string**, so the
real rendered row testid is `chat-participant-row-user_{id}_` — a
**trailing underscore with nothing after it** — never `user_{id}_{someProjectId}`.

This matches (and is explained by) `ParticipantDetailsContext.jsx`'s own
detail-fetch guard, which explicitly excludes
`p.entity_name !== ChatParticipantType.Users` from its
`entity_meta?.id && entity_meta?.project_id` required-fields check — Users
simply don't carry a `project_id` by design, not by omission/bug.

**The AFS for this case claimed `user_{entity_meta.id}_{project_id}`**
(reading `getChatParticipantUniqueId`'s source without live-verifying the
actual `entity_meta` shape for a Users-type record specifically) — this
cost one full debug round (10s Playwright timeout waiting on the wrong
testid) before a diagnostic pytest run dumping the live API participant
records + `document.querySelectorAll('[data-testid^="chat-participant-row-"]')`
settled it definitively. **Lesson: when an AFS's Automation Hints state a
dynamic-testid FORMAT (not just that a testid exists), live-verify the
exact string before writing the page-object method** — "confirmed by
reading the source" is not the same claim as "confirmed live," and this
project's own canon (`.agents/testing.md` § Locator policy) already
distinguishes them.

Page-object fix: `ChatPage.get_user_participant_row(user_id, timeout=...)`
builds `f"user_{user_id}_"` directly — no `project_id` parameter at all
(it would be silently unused/misleading for this participant type).
`remove_agent_participant()`'s `application_{agent_id}_{project_id}`
pattern is correct as-is and NOT the same bug — agent/pipeline/toolkit
participants genuinely do carry `project_id`.
