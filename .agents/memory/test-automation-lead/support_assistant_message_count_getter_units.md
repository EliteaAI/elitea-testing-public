---
name: SupportAssistantPage has two differently-scoped count getters — don't conflate them
description: get_message_count() returns TOTAL messages (user+assistant); get_assistant_message_count() returns only the assistant subset — any test comparing counts across a New-Chat/History-restore boundary must capture both baseline and post-restore values in matching units
type: feedback
---

## What happened (ELITEA-1799, issue #148, PR #608)

An implementer's first-draft assertion (checking that a New-Chat/History-
restore round trip preserves message content, tied to defect #607) captured
`count_before = support_page.get_assistant_message_count()` (assistant-only)
in one step, then compared it against `restored_message_count =
support_page.get_message_count()` (total, user+assistant) in a later step.
Since a normal exchange is 1 user + 1 assistant message, total ≈ 2x
assistant-only — the comparison was structurally biased and, checked against
the analyst's own real repro numbers (100 total wrappers vs 48 assistant-only
messages that run), would NOT have fired on the actual confirmed defect
(`100 < 48` is False). Caught at fresh-session review (R1), not before.

## The lesson

`automation/pages/support_assistant_page.py`:
- `get_message_count()` → total `.elitea-assistant-message-wrapper` count (all roles)
- `get_assistant_message_count()` → only the `--assistant` subset

Any test/assertion spanning a state-changing action (New Chat, History
restore) that compares counts before/after MUST capture both sides in the
same units — pick one getter and use it consistently for that particular
comparison. Don't assume "message count" is unambiguous just because both
getters return an int.
