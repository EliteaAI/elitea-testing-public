---
name: Invite-users Step 1 weak blank-conversation guard causes a Step 4 search timeout, not a search defect
description: test_invite_users_add_cancel_close.py Step 4 "Hrach Sargsyan" search timeout is #1082 (stale conversation landed via weak _open_blank_conversation), not a product defect or test-data drift — fixed by swapping to _open_genuinely_blank_conversation.
type: feedback
---

`TestInviteUsersAddCancelClose::test_invite_users_add_persists_cancel_and_close_discard`
(ELITEA-2167) hit a NEW deterministic (2/2 in the lead's independent gate)
`Locator.wait_for` `TimeoutError` on Step 4 — searching `"sa"` never surfaced
`"Hrach Sargsyan"`.

**Root cause (confirmed live, Playwright MCP, 2026-08-15):** Step 1 still called
the WEAKER `_open_blank_conversation()` (greeting-visible-only guard), which
landed on the stale pre-existing "HI Chat" conversation (id 507) instead of a
genuinely new one — same delayed SPA restore-to-last-viewed-conversation effect
`_open_genuinely_blank_conversation()`'s own docstring already documents (added
for ELITEA-2175/2176, in the SAME file, but never back-applied to this
original test's own Step 1 call site). That stale conversation already has
BOTH `USER_1_NAME` ("Hrach Sargsyan") and `USER_2_NAME` ("Levon Dadayan") as
participants — confirmed via its own participants popover — so the Add-users
modal's `excludedUserIds` correctly drops them from every search. The option
can never appear; the 10s timeout is not a slow/broken search, it's a
structurally-correct empty result.

**Not test-data drift** — verified both users ARE live org members (present
in the full unfiltered 11-person org-user list for project 471) at the time
of investigation. **Not a new product defect** — same root cause as #1082
(test-isolation, project-switch/conversation-restore settling), just
surfacing one step earlier via a different observable than the
already-tracked stale-participants-badge symptom. Commented on #1082 instead
of filing a sibling/duplicate.

**Fix:** swap the Step 1 call from `_open_blank_conversation()` to the
already-existing sibling `_open_genuinely_blank_conversation()` — additive
only, does not touch the shared `_open_blank_conversation()` (still used
unmodified by this file's `_create_single_owner_control_conversation()`).
Verified green post-fix (1/1, zero soft-failures fired — the fix avoided the
whole #1082 mechanism this run, not just papered over a symptom).

**Still open:** the underlying fix belongs in `_open_blank_conversation()`'s
own setup path (per #1082's own "What NOT to do" section) — this is a
per-call-site mitigation, not the root fix. If `_open_blank_conversation()`
itself is ever hardened, re-run the shared-file regression protocol on BOTH
its callers in this file.
