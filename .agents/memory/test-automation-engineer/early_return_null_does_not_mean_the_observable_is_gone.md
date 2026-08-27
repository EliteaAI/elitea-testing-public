---
name: Early-return null does not mean the observable is gone
description: "component X returns null" proves absence from X, not from the surface — grep the product for the TEXT
type: feedback
---

**The trap (cost a fix round on ELITEA-1866 / #1815, 2026-08-27).**

While repairing drift I found `ToolkitTestResults.jsx:29` early-returning `null`
while `messages` is empty, concluded "the pre-run welcome message is gone from the
product", wrote that into a code comment AND into the AFS, and proposed a TMS
amendment that would have **deleted a case-mandated observable** from ELITEA-1866's
Step 25 upstream. It was false. The message had been **relocated and reworded** into
the sibling component in the same panel:
`toolkit-test/ToolkitTestEmptyState.jsx:29,35`, mounted at `ToolkitTestPanel.jsx:70`
— the very component carrying `toolkit-test-empty-tool-select`, the testid the step
already asserted.

**Rule.** An early return / a removed branch proves the observable is absent from
**that component**, never from the **surface**. Before writing "removed" anywhere:

```bash
cd ../EliteaUI && git fetch origin
git --no-pager grep -n "<a distinctive phrase of the message>" origin/main -- src/
# then grep the SIBLINGS of the component you were reading — a redesign usually
# parks the string two files away in the same panel
```

**Why it is expensive, not cosmetic.** A false "the observable is gone" (a) ships a
lie into a comment the next reader trusts and will not re-grep, (b) retires a
legitimate `TODO: add testid` on a false premise — under `.agents/testing.md`
§ Locator policy a missing testid is *work to do*, never a deleted observable, and
(c) via the AFS § TMS case-text amendments row it **permanently deletes a requirement
from the upstream contract**. The declared-improvisation ceiling is explicit: a
declaration can never authorise a change to *what* is verified.

**Correct disposition when the observable moved but carries no testid, and adding one
would create a deployed-env red** (new testid → born on `automation/testids` → reaches
EliteaUI `main` only by human cherry-pick → green on localhost, RED on dev): do NOT
add the testid, do NOT assert it, do NOT claim it is gone. State the relocation with
file:line, keep a live `TODO(#<issue>)`, and file an issue owning testid + assertion
together with the promotion sequenced. A visible, tracked gap beats a false closure.
