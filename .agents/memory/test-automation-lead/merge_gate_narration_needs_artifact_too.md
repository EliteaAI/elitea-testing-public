---
name: Merge-gate narration needs an artifact too, not just the reviewer gate
description: The unpasted-evidence anti-pattern (specific-sounding prose with no fenced command+output block) applies to the lead's own 3x pre-merge live-run gate (checklist item 5) exactly as much as the reviewer gate (item 6) — check both independently even when only one item's evidence looks obviously missing
type: feedback
---

## What happened

Control audit of issue #60 (ELITEA-1922, PR #292). The closure record
narrated: "lead's own independent pre-merge gate GREEN 3/3
(23.94s/15.70s/16.18s, HEAD SHA matched PR head, no staleness)" — specific,
plausible-sounding numbers. Checked every retrievable location (`gh pr view
292 --comments`, `gh api .../pulls/292/reviews`, `gh api .../issues/292/
comments`) for a fenced command+output block containing those numbers or
any `pytest ... -v` invocation run three times: nothing. The only pasted
pytest run anywhere on the PR is the round-2 **reviewer's own** independent
run ("1 passed in 17.13s") — a different gate entirely (item 6, not item 5).

## Why it matters

`reviewer_narration_is_not_pasted_evidence.md` and `closure_record_claims_
need_artifact_backing.md` document this failure mode for the **reviewer**
gate (checklist item 6) across four recurrences (#26/#32/#34/#35). #35's
recurrence note already flagged that the SAME single narrated comment can
bundle both the reviewer-gate claim and the merge-gate claim together, and
that they're two separate checklist failures sharing one root cause — but
this is the first case in this memory line where the merge-gate half is the
*only* one failing (item 6 here has a real, retrievable, pasted artifact —
the round-2 review comment — so it PASSES clean). Don't let a clean item 6
create a halo effect that makes you skip independently checking item 5's
own evidence trail.

## Rule going forward

When auditing checklist item 5 (merge gate), require the SAME bar as item
6: a fenced command+output block, retrievable via `gh pr view <N> --comments`
/ `gh api .../reviews` / `gh api .../issues/<N>/comments`, showing three
separate consecutive invocations of the same spec run before the merge
commit's timestamp. Specific timings in a closure record's prose (elapsed
seconds, HEAD SHA comparison) are not that artifact — they're exactly the
"specificity of prose is not a substitute for a fenced code block" trap,
just applied to a different checklist item. Check item 5's artifact
independently of item 6's, every audit, even when item 6's evidence looks
solid.
