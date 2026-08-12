---
name: A reviewer's absence/negative claim is cheap for the orchestrator to independently re-verify live before trusting it
description: When a reviewer's finding contradicts the AFS/analyst's own claim about live product state (e.g. "this element doesn't exist" turns out false), use the orchestrator's own Playwright MCP access to check ground truth directly before routing another fix round — it's cheap and catches narration-vs-reality gaps the same way pasted-evidence checks do
type: feedback
---

On #212/ELITEA-1808/PR#643 round 2, a fresh reviewer reported that the AFS's claim
"the file table has no timestamp column" was FALSE — a real "Last update" column
existed, just clipped off-screen in the analyst's narrow exploration viewport. This
was a significant reversal (it meant CLARIFICATION #642 was itself wrong, and the
shipped test under-asserted a real observable). Rather than trust the reviewer's
prose description and route a fix round on faith, I used `mcp__playwright__browser_resize`
(1600×900) + `browser_navigate` + `browser_evaluate` to independently read the live
DOM myself (`artifacts-file-row`'s child cell texts) and confirmed the exact same
5th populated timestamp cell the reviewer described — before dispatching the fix.

This is the same discipline as the closure-record "claims require pasted output" rule
(`reviewer_narration_is_not_pasted_evidence.md`, `closure_record_claims_need_artifact_backing.md`)
extended to mid-pipeline reviewer findings, not just closure-record claims: the
orchestrator has direct browser-tool access and near-zero marginal cost to check a
live-product factual claim before trusting it as the premise for another implementer
round. Apply this whenever a reviewer/analyst claim is (a) about observable live
product state (not narrated test-run logs), (b) cheap to check directly (a page
load + one DOM read), and (c) consequential enough that acting on a wrong claim would
waste a full fix-and-review cycle.
