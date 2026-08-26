---
name: Fix round — diff-check each named finding before calling the round done
description: A "fix round 1" commit that doesn't literally touch every named finding's file/line still gets classified unaddressed next round — grep your own diff per finding before handoff, don't rely on memory of what you fixed.
type: feedback
---

## What happened (ELITEA-2226/2228/2229/2230, PR #1495)

Round 1's dispatch named two findings: (1) all 4 AFS "Insertion point"
sections claim methods were appended into `TestHelpCenterSidebarTour`, but the
diff creates a sibling `TestHelpCenterSidebarTourExtras`; (2)
`test_sidebar_interactive_tour_starts_on_link_click` uses strict `==` against
a hardcoded literal, contradicting the AFS's own twice-stated guidance to use
substring/`.to_contain_text()` matching. Round 1's actual commit
(`738b1baf`) only added a `p1` marker and fixed the Linked Story field — it
never touched either named finding. Round 2 arrived with the reviewer saying
explicitly "NOT addressed last round — no attempt was visible in the diff."

## The fix

Before reporting a fix round done, for EACH named finding: `grep`/`git diff`
for the exact file + symptom named in the finding and confirm the change is
present in your commit, not just "I remember thinking about this." A finding
addressed only in your head (or addressed in a *different*, earlier commit
that predates the round the reviewer is scoring) reads as untouched — the
reviewer diffs the round's actual commits, not your intent.

Two-line self-check before handoff, one per finding:
```
git show <this-round's-commit> --stat | grep <affected file>   # touched at all?
git diff <this-round's-commit>^..<this-round's-commit> -- <file> | grep -n "<the symptom text>"
```
If either comes up empty for a finding you believe you fixed, you didn't fix
it in this round — go fix it now, don't hand off believing otherwise.

See also: verify_your_own_delivery_before_handoff.md ·
fix_round_findings_earn_a_regression_guard_not_just_a_line_fix.md
