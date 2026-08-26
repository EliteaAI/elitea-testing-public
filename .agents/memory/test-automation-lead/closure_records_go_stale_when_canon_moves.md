# A closure record's "verified promotable" row expires when canon moves

**Learned:** 2026-08-27, #110 / ELITEA-1802 rework.

#110's 2026-07-16 closure record stated: *"Nothing pending on automation/testids or a
main promotion — fully self-contained, verified promotable."* It was honestly derived
under the rules of that day: the Support Assistant was treated as a third-party npm
package, so "no testids apply" implied "nothing to promote".

Then `.agents/testing.md` gained the connected-first-party-repo bullet (#705), which
names #110 as the framing it supersedes. Overnight the same test depended on 5 testids
living on two `automation/testids` branches and **none on either `main`** — i.e. green
on localhost, red on any deployed env. The record did not change; it just became false.

## Rule

On ANY rework, re-run the promotability verification from scratch (fresh `git fetch`
in every repo involved, two-stage grep, paste the output). Never inherit a
promotability row from a prior closure record, however well-evidenced it looks —
`.agents/workflow.md` already forbids copying the AFS/implementer's claim; this
extends it to your OWN past self's claim.

## Tell

If a prior record's promotability argument rests on a *classification* ("third-party",
"out of scope", "not applicable") rather than on a *grep output*, treat it as
unverified. Classifications are exactly what canon revises.

## Connected repos carry an extra hop

For `EliteaAI/elitea_assistant`, "on main" is not sufficient for a deployed env:
EliteaUI must also bump the `@eliteaai/elitea-assistant` git-dependency. A closure
record that stops at "on main" is still incomplete. (`.agents/workflow.md` § Connected repos)
