---
name: Provenance grep needs case-insensitive
description: testid on-main/testids grep must use -i — camelCase prop names (buttonTestId=) hide from a bare `testid` filter
type: feedback
---

When verifying a testid's PROVENANCE against `origin/main` / `origin/automation/testids`
(AFS Concrete Handles, closure-record rows), the standard two-stage grep
(`.agents/workflow.md` § Closure record) is:

```bash
git grep -- "$t" origin/main -- src/ | grep -E "(data-testid|testid.*=.*$t)"
```

**Always add `-i` to BOTH stages.** A testid wired via a camelCase prop name —
`buttonTestId="generate-agent-open-button"`, `closeButtonTestId="..."` — does
NOT contain the lowercase substring `testid`, so a case-sensitive filter
reports a false `main:no` even when the testid is genuinely present and
wired (confirmed: `generate-agent-open-button` IS on `origin/main` via
`GenerateAgentButton.jsx`'s `buttonTestId=` prop; a case-sensitive grep in a
prior AFS missed it entirely). Use:

```bash
git grep -qiE -- "$t" origin/main -- src/
```

for the presence check, or add `-i` to the second-stage filter if you need
to see the matching line. Cross-reference: `.agents/workflow.md` § Closure
record's "two-stage grep pattern" note already documents the bare-substring
vs literal-`data-testid=` false-negative history (#73/#95/#166/#175/#262) —
this is the SAME family of bug, one layer up (case, not just prop-vs-literal
shape). Worth folding into that section's canonical command next time
someone touches it.
