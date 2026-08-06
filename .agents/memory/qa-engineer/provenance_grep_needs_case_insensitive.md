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

**Third gap, found ELITEA-2347 (2026-08-06): `-i` alone still isn't enough for
an OBJECT-LITERAL prop.** `testId: 'secrets-add-button',` (colon, no `=` at
all) fails the filter EVEN WITH `-i`, because the regex
`testid.*=.*$t` requires a literal `=` character between the "testid" match
and the value — an object-literal key:value pair has none. Confirmed live:
`git grep -qiE -- "secrets-add-button" origin/automation/testids -- src/ |
grep -qiE "(data-testid|testid.*=.*secrets-add-button)"` reports NO MATCH
even though `git grep` itself finds the line
`testId: 'secrets-add-button',` in `SecretsContent.jsx`. **When the filter
says "no" and you're not certain, don't trust it — re-run the STAGE-1 `git
grep` alone (no filter) and eyeball the matched lines by hand.** The filter
is a convenience for the common `data-testid="x"` / `testId={x}` shapes; it
is not exhaustive, and treating a filtered "no" as ground truth produced a
false negative here that a 10-second manual check caught. For a small
handle set (typical AFS Concrete Handles table, &lt;20 testids), skip the
filter regex entirely and just read the raw `git grep` output per testid.
