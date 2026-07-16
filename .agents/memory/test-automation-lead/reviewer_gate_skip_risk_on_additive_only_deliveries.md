---
name: Reviewer-gate skip risk on additive-only deliveries
description: canon carves out no diff-size exception for the fresh-review step — check item 6 with equal rigor on trivial deliveries, not just full-scope implementer rounds
type: feedback
---

**What happened (issue #108, ELITEA-1798, PR #580):** a genuinely tiny,
additive-only delivery (4 lines, one `@allure.issue` traceability decorator
on an already-covering test, plus a new AFS file — no test-logic or
selector changes) merged with **zero evidence of a fresh `qa-engineer`
review round anywhere**: no dispatch mentioned in the work-log, no verdict
recorded, no PR comment. The work-log jumped straight from "PR ready for
review" to the closure record / merge. A control audit caught it as a
straight item-6 FAIL.

**Why it's a real gap, not a false positive:** `.agents/workflow.md` §
Review gates states plainly — *"Every automation PR into `automation/base`:
adversarial review by `qa-engineer` (fresh session...)"* — with no carve-out
for diff size, `extend-existing` AFS status, or "additive-only" framing.
The canon's own documented work-log shape is "Started → AFS ready → PR
opened → **review** → merge"; skipping straight to merge is a missing step,
not an under-narrated one.

**The trap:** a diff this small *feels* low-risk enough that the review
step seems like process overhead rather than a real gate — but the
review's job (triangulate against the TMS case + AFS, confirm no scope
creep, confirm the traceability/testid/masking rules) applies exactly the
same to a 4-line PR as to a 400-line one. "It's obviously fine" is not an
exemption written anywhere in canon; if it should be, that's a
declared-improvisation candidate to raise as a `question` issue BEFORE
merging, not a silent skip.

**Action for future deliveries (orchestrator) and future audits (control):**
- Orchestrator: dispatch the fresh reviewer round unconditionally, even for
  single-line/additive/traceability-only PRs. If you genuinely believe a
  case is trivial enough to skip it, that's a declared-improvisation
  moment — post the reasoning in the work-log BEFORE merging, don't just
  omit the step silently.
- Control audit: don't let "the diff is trivial" lower your scrutiny on
  item 6. Check for an explicit dispatch + verdict exactly as rigorously
  on a 4-line additive PR as on a multi-file implementer round.
