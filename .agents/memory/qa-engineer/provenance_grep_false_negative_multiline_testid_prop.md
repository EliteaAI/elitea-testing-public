---
name: Provenance grep false-negative — testid on a continuation line of a multi-line prop
description: The closure-record two-stage grep reports "not on main" for testids passed via a prop whose value sits on its own JSX line (e.g. a wrapped ternary)
type: feedback
aliases: [provenance grep, closure record testid row, artifacts-file-row not on main, two-stage grep false negative]
tags: [area/testids, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

`.agents/workflow.md` § Closure record's two-stage grep filters stage-1 hits with
`grep -iE '(data-testid|testid[[:space:]]*[:=])'`. That filter is a **line** filter,
so it drops a hit whose line carries only the testid *string* because prettier
wrapped the prop:

```jsx
// ArtifactTable.jsx (origin/main)
  testId={                                              // <- line N   (matches filter)
    row.type === ARTIFACT_TYPES.FOLDER ? 'artifacts-folder-row' : 'artifacts-file-row'
  }                                                     // <- line N+1 (the stage-1 hit; filter drops it)
```

Result on 2026-08-21: `artifacts-file-row` reported `main:no testids:no` while it is
in fact present on BOTH refs. The documented caveats cover runtime-composed
templates, the `TestId` case form and the `testId:` colon form — not this one.

## What to do

When a row comes back `no` on **both** refs but the test demonstrably passes
locally, do not write it into a closure record — re-read the hits instead of
counting them, with context:

```bash
git grep -n -B2 -- "$t" origin/main -- src/
```

Same rule as the existing caveat: a `no` is a prompt to look, never a fact.
