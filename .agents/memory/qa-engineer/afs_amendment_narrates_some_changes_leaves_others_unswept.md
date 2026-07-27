---
name: AFS amendment narrates some changes, leaves others unswept
description: PR #653/ELITEA-1824 — implementer's PR description explicitly narrates 2 AFS corrections (both properly amended), but silently adds 3 more testids (empty-state button, data-selected, breadcrumb labels) used+asserted in the shipped test without touching their Concrete Handles rows or the 5 Coverage Map rows they unblock — check the diff for NEW testids independent of what the PR body claims to have amended
type: feedback
---

## What happened

PR #653 (ELITEA-1824, implementer pass on my own prior analyst AFS) shipped
a fully correct, well-tested implementation: 46/46 case steps covered, one
correctly-polarized `expect.soft()` for known defect #649, testid-only and
additive-only both clean, live-verified GREEN-except-sanctioned-RED on an
independent re-run.

The PR description explicitly narrated **two** AFS corrections made during
Phase 2 exploration (the Path field's `text_content()` not reflecting the
typed value → new `artifacts-upload-path-input-field` testid; the
`select_text()`+Backspace workaround not working → replaced with
Escape+re-navigate). Both were verified genuine and both were properly
amended into the AFS (Test Step 7, Test Step 23, Automation Hints, Concrete
Handles — all consistent, all matching the shipped code).

But the SAME implementer commit also added **three more testids** to
`EliteaAI/EliteaUI`'s `automation/testids` branch in a separate commit
(`9d839c3a`: `artifacts-upload-files-empty-state-button`, `data-selected`
on `BucketItem.jsx`/`FileTreeItem.jsx`, `artifacts-breadcrumb-bucket-label`
+ `artifacts-breadcrumb-folder-label`) — all correctly implemented, all
actively wired into the page object, all genuinely asserted in the shipped
test (`is_bucket_selected`, `is_tree_item_selected`,
`get_breadcrumb_bucket_text`, `get_breadcrumb_folder_names`). The PR
description's summary bullets DO mention these testids exist. But the AFS
itself was never touched for them: its Concrete Handles table still says
"none" / "testid needed" for all three rows (as if analyst-flagged-but-
unimplemented), and 5 Coverage Map Axis-1 rows (case steps 14, 35, 38, 40,
44) still carry disposition "clarification (testid needed)" instead of
"asserted" — understating real, shipped coverage. Also found a smaller
sibling: Test Step 22's inline body text still says "against the buggy
actual value" for the #649 soft-assert, while § Automation Hints was
correctly amended to "against the documented CORRECT expected value" — the
two sections of the SAME AFS now contradict each other, and the shipped
code matches Automation Hints (the correct polarity), not Test Step 22.

## Reviewer technique

The prior 4 memory entries in this family (`afs_coverage_map_narrow_fix_
leaves_sibling_rows_stale`, `elitea_1808_coverage_map_handle_drift_from_
own_test_step_prose`, `afs_drift_check_the_whole_document_not_just_the_
last_fixed_section`, `verifying_race_mitigation_and_afs_amendment_gap`) all
cover "a fix/amendment landed for the named spot, but a sibling with the
identical claim-shape was left stale." This one is a distinct trigger:
**the drift isn't a fix that missed a sibling — it's a set of code changes
the PR body never claimed needed an AFS update at all.** The PR description
told a coherent, verifiable story about 2 corrections; both checked out
perfectly on independent verification. That coherence is exactly what makes
it easy to stop there and not notice a 3rd, unnarrated class of change.

**Concrete check going forward**: don't just verify what the PR description
says was amended — `git diff <EliteaUI-base>..<EliteaUI-testids-HEAD>` (or
read every testid-adding commit named/discoverable in the PR, not only the
ones the description calls out by hash) and cross-reference EVERY new
testid against the AFS's Concrete Handles table AND every Coverage Map row
whose disposition depends on that testid's absence. A "testid needed" row
whose testid now demonstrably exists in `origin/automation/testids` AND is
used in the shipped page object/test is unswept AFS drift, full stop,
independent of whether the PR narrative mentions it.

## Round-2 outcome (fresh-session re-review, 2026-07-19 21:20)

The implementer's fix commit (`fb44c22d`) claimed a full-document sweep, not
a narrow patch of the 3 named spots. Independently re-verified this claim
rather than trusting it: read the actual current AFS content for all 3
Concrete Handles rows + all 5 Coverage Map rows + the Step-22/Automation-
Hints contradiction — all genuinely fixed. Then did my OWN independent full
sweep (grepped the AFS for all 5 testids/attributes this PR round
introduced) and found zero additional stale references — the implementer's
sweep really was complete this time, unlike the ELITEA-1839/1808 PRs earlier
this session where "fix the named rows" instructions left siblings stale
across 2-4 rounds. Verdict: APPROVED on round 2, no round 3 needed.
**Pattern confirmation**: a dispatch instruction that says "full sweep,
grep for every occurrence" (as this round's fix commit message did) is what
actually closes out this finding class in one round — narrow "fix these 3
named things" framing is what produces the multi-round drag seen elsewhere
this session.
