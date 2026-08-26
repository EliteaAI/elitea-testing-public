---
name: Closure grep must catch testId colon prop form
description: workflow.md's stage-2 filter `testid.*=.*$t` misses `testId: 'x'` (colon) in JSX object-literal arrays — 5 false negatives on ELITEA-2464
type: feedback
---

## The gap

The closure-record promotability check in `.agents/workflow.md` uses a two-stage
grep whose stage-2 filter is `grep -E "(data-testid|testid.*=.*$t)"`. That
pattern requires an `=` after "testid" — but EliteaUI also wires testids through
**object-literal arrays** with a **colon**:

```jsx
// PlusChatButton.jsx SUBMENU items — the form the filter misses
{ key: SUBMENU_KEYS.AGENTS, label: 'Agents', Icon: ApplicationsIcon, testId: 'agents-menuitem' },
```

On ELITEA-2464 (2026-08-07) this produced **5 false negatives** (agents/pipelines/
toolkits/mcps-menuitem showing "absent on BOTH refs", internal-tools-menuitem
showing on-main-but-not-testids — a logically impossible result, since
`automation/testids` contains `main`).

## The fix

Use a colon-or-equals, case-tolerant stage-2 filter:

```bash
grep -qE "(data-testid|[Tt]est[Ii]d.*[:=].*$t)"
```

## The tell that your filter is broken

Any testid reported **on `main` but NOT on `automation/testids`** is impossible
(the integration branch always contains main) — treat that row as proof the
filter missed a wiring form, and fall back to the non-quiet grep to inspect the
actual JSX before writing the closure record.

Related: qa-engineer's `testid_on_main_provenance_claim_needs_two_ref_grep.md`
and the DotMenu `${item.key}-menuitem` template gotcha (naive grep false
negatives from *constructed* testids — a third wiring form with no literal
string at all).
