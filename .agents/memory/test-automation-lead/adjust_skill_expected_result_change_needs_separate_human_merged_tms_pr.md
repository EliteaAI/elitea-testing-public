---
name: adjust-automated-test expected-result changes need a separate, human-merged TMS PR
description: when an adjust-automated-test repair genuinely changes a case's expected result, open the TMS-case-text PR yourself (not the implementer) and NEVER merge it — only the test PR goes through your normal gate+merge
type: feedback
---

## What happened (issue #2396, ELITEA-1862, PR #2398, TMS PR onetest-ai-tm-Elitea#159)

A drift repair (class A) genuinely changed what the test asserts — Save/Discard
buttons went from "present and disabled" to "structurally absent" because the
product changed. `adjust-automated-test` Step 3's preserve-the-nature rail is
explicit: an assertion may change only because the case's expected result
genuinely changed, **and then the TMS case changes in the same PR pair**
(Step 8: a test PR → `automation/factory` AND a TMS PR → the cases repo).

The implementer correctly fixed the code and opened PR #2398 but never opened
the TMS PR — its remit is this repo only (`.agents/role-overrides.md` §
Implementer slot: "your PR in this repo is the only artifact"), and the skill
is role-agnostic about who does Step 8, so it fell through the gap. The fresh
reviewer caught the gap correctly (checked the live case file, found a PR
search for "1862" returned nothing, flagged CHANGES_REQUESTED) but recommended
re-dispatching the implementer — the implementer still shouldn't touch the TMS
repo. The orchestrator's own repo-ownership convention wins: the lead opens the
TMS PR.

The skill is also explicit, independent of role, that this PR is **never
merged by any agent** — case-text/expected-result changes are a human
sign-off item, unlike the metadata-only back-write (`execution_type`/
`status`/`automation_test_id`) which the orchestrator edits directly without a
PR per `.agents/test-automation.yaml` § `backwrite_on_done`. Two different
TMS-write mechanisms for two different kinds of change: metadata = direct edit
by the orchestrator; case *content* = PR, orchestrator opens it, human merges.

## Rule going forward

1. If the PR body's "Expected-result changes" is anything but "none", a
   companion TMS PR is mandatory before the unit is complete — check for it
   BEFORE dispatching the reviewer, not after a review round catches the gap.
2. The orchestrator opens that TMS PR, never the implementer (different repo,
   different authority) and never leaves it for a re-dispatch.
3. Merge the test PR after your normal gate (3× green, independent, DEV) —
   that part is unchanged, you retain standing merge authority there.
4. Do NOT merge the TMS PR. Note it under the closure record's "Still open"
   row — this is itself anticipated by the record's own template field, not an
   incomplete delivery. The card still goes to `Ready` with the test merged;
   the TMS PR is the human's remaining action, same as any other
   awaiting-external-acceptance item.
5. Set `automation_pr` on the TMS case in the SAME PR as the content change
   (the skill bundles them) — don't do a separate direct-edit back-write for
   that field when a content-change PR is already in flight.

## Converse case (issue #2401, ELITEA-1866, PR #2402) — "Expected-result
changes: none" means NO TMS PR at all, not a smaller one

A class-A repair whose own PR body correctly says "Expected-result changes:
none" (e.g. widening an expected-dict literal to tolerate a legitimately new,
non-observable response key — nothing a human reading the TMS case's steps
would notice) has **no case-content change to carry**. The implementer still
opened a TMS PR here — containing only the `automation_pr` frontmatter field,
nothing else — by analogy with Step 8's "two PRs" instruction. That PR
shouldn't have existed: `automation_pr` is exactly the kind of field
`test-automation.yaml` § `backwrite_on_done` already governs as a **direct
orchestrator edit against the TMS repo's main**, no PR, done once the test PR
is actually merged. A PR for a pure-metadata field is scope creep in the
opposite direction from rule 5 above (rule 5 says "don't do a separate direct
edit when a content PR is already in flight" — but there's no content PR to
piggyback on when there's no content change).

**Decision rule:** check the PR body's "Expected-result changes" line BEFORE
deciding whether a TMS PR exists at all. "none" → close/skip any TMS PR an
implementer opened anyway, do the `automation_pr` back-write as a direct edit
yourself once the test PR is merged. Anything else → rule 5 applies as written.

Also confirmed while fixing this: `index.json` does not store `automation_pr`
at all (checked the actual entry — only `status`/`execution_type`/
`automation_test_id`/etc.) — so an `automation_pr`-only back-write never needs
an index rebuild. Don't reach for `build_index`/`_index.py` unless
`status`/`execution_type`/`automation_test_id` actually changed.

**Also:** the lead's own merge gate is non-negotiable even on an adjust-path
PR the implementer already gated 3/3 — `.agents/testing.md` is explicit that
the implementer's green run is never the gate. Nearly skipped this one
because the generic `adjust-automated-test` skill text ("never merge either
PR") reads as if the lead doesn't merge at all on this path; this entry's own
rule 3 already said otherwise, but almost got overridden by the louder,
more-recently-read generic skill text. When a project-specific memory entry
and a bundled skill's generic text conflict, the memory entry (born from a
real past correction, scoped to this project) wins — re-read it before taking
the skill's text as the full picture, don't let recency bias decide.
