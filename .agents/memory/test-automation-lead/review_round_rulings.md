---
name: Review-round rulings
description: How review rounds are dispatched, when a verdict counts, and when the R2 cap applies — signature-based, not round-count-based
type: feedback
---

## Rules

1. **Every re-review dispatch prompt says "verify the fix is real AND re-check the
   rest of the PR — don't rubber-stamp just the delta."** A fix pass is a new diff;
   round 2 legitimately finds what round 1 missed. Without the line, the reviewer
   answers only the named question and stops looking.
2. **A dispatch is not a verdict.** A work-log that goes "Dispatching a fresh
   reviewer" → closure record, with nothing in between, is a review-gate FAIL even
   though the dispatch is evidenced. Find the specific comment/artifact recording
   APPROVED / CHANGES_REQUESTED / findings. Applies to FIRST rounds too, not just
   re-reviews. Mechanical tell: grep merged PR bodies for unfilled template
   placeholders like `(orchestrator fills in)`.
3. **No diff-size carve-out for the review gate.** A 4-line additive
   traceability-only PR gets a fresh `qa-engineer` round exactly like a 400-line
   one. If you truly believe a case is trivial enough to skip, that is a
   declared-improvisation moment — post the reasoning BEFORE merging, never omit
   silently.
4. **A CHANGES_REQUESTED can target the AFS's *reasoning*, not the code.** On an
   extend-existing whose Known-Defects section argues *why* a defect doesn't
   threaten the assertions, that argument is adversarially checkable even when the
   diff is one decorator. Route the fix-only round at re-establishing the TRUE
   reasoning via live verification — say so explicitly — not at rewording prose
   into internal consistency.
5. **The R2 cap counts failure SIGNATURES, not rounds.** A round-N finding that is
   a genuinely new root cause — especially one round N-1's own *correct* fix
   causally exposed (moving a console listener earlier makes an existing product
   defect observable) — is forward progress; keep going. Corollary: an
   implementer's "clean 3/3, no flake" self-report goes stale the moment a later
   commit in the same PR changes timing.
6. **The cap DOES apply when the same failure class repeats across two consecutive
   rounds.** Then the orchestrator stops dispatching, enumerates the remaining
   scope itself mechanically, and hands ONE closed worklist ("these 3 lines only").
   Only valid when (a) the class is doc-only/cosmetic with an independently-green
   test underneath, and (b) the full remaining scope is grep/diff-enumerable. If
   either fails — functional risk, or adversarial judgment still needed — dispatch
   the reviewer again.
7. **Additive-only and testid-only are orthogonal checks on the same diff.**
   Additive-only (`git diff <file> | grep -E '^-[^-]'` → empty) answers "did we
   break an existing caller". Testid-only answers "did we add a policy-violating
   handle" — a NEW raw locator removes nothing, so it is invisible to the
   additive-only grep. An implementer reporting a clean additive-only self-check
   has said nothing about locator policy. Run both, independently, every time.

## Seen 7×

- ELITEA-1954 / #61 / PR #513 — R2 full-recheck found 2 new Important findings (raw `page.locator()` in the SPEC file; a console listener registered at Step 9 missing steps 1–8).
- #66 / ELITEA-1944 / PR #523 — re-review dispatched, no verdict ever recorded; PR body still read `(orchestrator fills in)`. Recurred on a FIRST round: #139 / ELITEA-1991 / PR #604.
- #108 / ELITEA-1798 / PR #580 — 4-line additive PR merged with zero evidence of any review round.
- …plus 4 earlier occurrence(s) — full per-case detail in the source entries below.

See also: reviewer_full_recheck_catches_new_findings_on_rework.md ·
reviewer_gate_skip_risk_on_additive_only_deliveries.md ·
re_review_dispatch_without_recorded_verdict.md ·
reviewer_finding_can_be_afs_reasoning_not_code.md ·
r2_cap_applies_to_repeated_review_round_failure_class.md ·
new_root_cause_via_correct_fix_is_not_r2_cap_violation.md ·
additive_only_and_testid_only_checks_are_orthogonal.md
