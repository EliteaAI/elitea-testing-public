---
name: 22 of 28 promotability rows can be FALSE NEGATIVES — runtime-composed testids are invisible to the closure grep
description: On a case whose testids are composed from a prop plus a suffix, the two-stage closure grep reported "no" on BOTH refs for 22 of 28 handles. All 22 were present. Read the composition site; never ship a grep's "no" on a composed testid.
type: gotcha
---

## What happened

Writing the closure record for ELITEA-2219 (#2382), the prescribed verification block
(`git fetch origin` + two-stage grep, `-i` and `[:=]` both applied) produced:

```
help-center-card-documentation-title       no     no
help-center-card-documentation-icon        no     no
help-center-tour-link-chat-interactive-tour no    no
… 22 rows in total reading "no" on BOTH refs
```

**All 22 were present on `automation/testids`.** They are composed at runtime:

```jsx
// ResourceCard.jsx                        // ResourcesPage.jsx (call site)
data-testid={testId}                       testId={`help-center-card-${config.testidCategory}`}
data-testid={testId && `${testId}-title`}  data-testid={`help-center-card-${config.testidCategory}-icon`}
```

No literal `help-center-card-documentation-title` exists anywhere in the source, so
no substring grep can ever find it. `.agents/workflow.md` § Closure record already
warns stage-1 "cannot see these at all" — but the warning is a footnote, while the
grep is a copy-pasteable loop that produces a clean-looking table. **The table is the
trap: 22 confident `no`s look like a finding, not like a tool limitation.**

Shipping them would have been the #73/#95/#166/#175/#262 failure again — a closure
record asserting "not on main" as verified fact when it was never checked.

## The rule

**A `no` from the closure grep is only evidence for a testid that appears LITERALLY in
source.** For any composed testid, the grep result is *undefined*, not negative.
Resolve it by reading the composition:

```bash
git show origin/main:<component> | grep -nE 'data-testid|testId'
git show origin/automation/testids:<component> | grep -nE 'data-testid|testId'
# and count testid lines per file on each ref to see at a glance which ref has the wiring
```

Then state in the record **which rows were resolved by reading rather than grepping**,
and say so explicitly. A promotability row derived by inference must be labelled as
inference — this case's tour-link row is: `main` carries its own *older* composition,
ours only refines the colliding `-more` slug, and both asserted slugs are non-`more`,
so they resolve on `main` too. That is a chain of reasoning, not a grep hit, and the
record says so.

## How to spot the risk before running the grep

If the case's testids follow a `{prefix}-{variable}` shape, or the AFS handle table
names a `testId` prop, or the page object stores the pattern as an UPPER_CASE
template constant (`CARD = '[data-testid="help-center-card-{}"]'`) — expect the grep
to be blind and plan to read instead. The template constant in the page object is the
tell that is easiest to notice, because you are looking at it anyway.

Carded as one of four structural blind spots in #2384 (with `data-*` state
attributes, second occurrences of a surviving value, and single-quote/expression
forms), alongside a proposed occurrence-count check that closes one of them cheaply.
