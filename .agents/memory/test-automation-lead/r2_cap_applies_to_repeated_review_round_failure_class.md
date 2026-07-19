---
name: R2 cap applies to a repeated review-round failure CLASS, not just repeated root cause
description: When review round N finds the same failure CLASS as round N-1 (not a genuinely new one), the orchestrator can stop dispatching more reviewer rounds, do the remaining mechanical verification itself, and hand the implementer one closed-set worklist instead of looping
type: feedback
---

On #212/ELITEA-1808/PR#643, 4 review rounds ran: R1 (POM discipline + step-description
accuracy) → R2 (a genuinely new root cause — the AFS's "no timestamp column" claim was
FALSE) → R3 (AFS-internal doc drift: a Coverage Map cell citing a retired handle) → R4
(the IDENTICAL failure class as R3: two more stale-fact spots not swept). R1→R2→R3 were
each legitimately different root causes (per `new_root_cause_via_correct_fix_is_not_r2_cap_violation.md`,
correctly NOT capped). But R4 repeating R3's exact class — "AFS restates a fact in
multiple sections; a fix scoped to the cited line misses siblings" — is where the
distinction matters: this is 2 occurrences of the SAME signature, which the R2-cap
rule's "count matching failure signatures, not raw round numbers" language does cover.

**What I did instead of dispatching a 5th reviewer round:** read the full AFS myself,
exhaustively grepped it for every remaining occurrence of both stale fact-strings
(`Control+a`/`press_sequentially`, the retired wait-condition handle), classified each
hit as either a live instructional claim (needs fixing) or legitimate historical/
corrective prose (leave alone — the AFS accumulates "Implementer correction" notes by
design, those aren't drift), built a closed, exact 3-line worklist, dispatched ONE
final targeted fix-only round with explicit "these 3 lines only, nothing else" scope,
and verified the result myself mechanically (grep for zero remaining instances + diff
scope confirms only the AFS file changed) rather than spending a 5th reviewer round on
a documentation-only class of issue with zero functional/test-code risk (the actual
test had been GREEN and unchanged since R2's real fix).

**Generalizable trigger for applying the R2 cap to the review loop itself:** the SAME
underlying failure class recurring across two consecutive review rounds, where (a) the
class is doc-only/cosmetic with an independently-confirmed-green test underneath, and
(b) the orchestrator can enumerate the full remaining scope itself via a mechanical
check (grep, diff) with high confidence — not a case where genuine adversarial judgment
is still needed. If either condition doesn't hold (functional risk, or the remaining
scope isn't mechanically enumerable), don't self-resolve — dispatch the reviewer again.
