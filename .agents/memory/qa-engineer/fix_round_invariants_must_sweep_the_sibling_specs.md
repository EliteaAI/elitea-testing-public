---
name: A fix round's new invariant must sweep every sibling spec, not just the named one
description: Re-review move — when a fix ships a shared helper + a source-grep guard, check the guard's module list covers every spec making the same claim.
type: feedback
aliases: [fix round sibling sweep, positive control missing, guard module list incomplete]
tags: [area/review, type/triangulation-trap]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

A fix round that answers one finding well tends to answer it *narrowly*. The
ELITEA-2298 fix (PR #1976, settings-w09) did everything right: extracted the
inline listener into `utils/request_capture.collect_requests`, added the
positive control (`len(delete_requests) == 1` at the step that genuinely
deletes), and pinned both with a source-grep unit test —
`tests/unit/test_request_capture_backs_absence_claims.py`.

But the guard's `_SPECS_CLAIMING_NO_DELETE_WAS_ISSUED` listed **two** of the
**three** specs in the same PR. `test_users_batch_delete.py` (ELITEA-2299)
makes the identical claim ("opening the batch-delete confirmation must issue no
DELETE"), still hand-rolls `page.on("request", ...)`, and has **no** positive
control — so its absence assertion is the unfalsifiable shape the round was
convened to retire, now sitting one file away from the guard that would have
caught it.

## The review move

On a re-review, do not stop at "the named finding is fixed". Two extra checks,
both cheap:

1. **Grep the whole unit for the claim, not the file** — e.g. `grep -rn "must
   issue no DELETE\|assert not .*_requests" automation/tests/` — and confirm
   every hit uses the new shared shape.
2. **Read the guard's own module list.** A source-grep meta-test names the
   modules it protects; a sibling omitted from that list is invisible to it
   forever, and the omission looks like a decision.

An absence assertion (`assert not requests`) needs three things every time:
registered before the action, read after an anchor, and paired with a positive
control. Missing the third is the silent one.

Related: [[afs_no_request_clause_downgraded_to_a_table_read]] ·
[[absence_of_request_assertion_registration_window]]
