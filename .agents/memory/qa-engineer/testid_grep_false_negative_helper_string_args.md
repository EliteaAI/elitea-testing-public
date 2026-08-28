---
name: Testid grep false-negative on helper string arguments
description: The closure-record two-stage testid grep reports "not present" for testids passed as bare string args to a slotProps helper
type: feedback
aliases: [testid provenance grep, closure record false negative, getDateFieldSlotProps]
tags: [area/locators, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

Reviewing PR #1945 (ELITEA-2314..2319, Analytics date filter) I ran the canonical
`.agents/workflow.md` § Closure record two-stage grep against `origin/automation/testids`
for the case's testids. Four came back `no` on BOTH refs:
`analytics-date-{from,to}-open-button`, `analytics-date-{from,to}-popper`.

They exist. `AnalyticsContainer.jsx` wires them through a helper:

```jsx
slotProps={getDateFieldSlotProps(
  'analytics-date-from-input',
  'analytics-date-from-open-button',
  'analytics-date-from-popper',
)}
```

Stage 1 (bare substring) FINDS those lines. **Stage 2 is what drops them** — the
matching line is a bare string argument on its own line, carrying neither
`data-testid` nor `testid[:=]`, so the `-iE '(data-testid|testid[[:space:]]*[:=])'`
filter discards it. Same class as the already-documented runtime-composed
`` data-testid={`${PREFIX}-x`} `` blind spot, but this one *does* survive stage 1.

## What to do instead

When a testid reports `no` on `automation/testids` for a case whose AFS claims it was
just added, do NOT write "not present" — re-run stage 1 alone and READ the hits:

```bash
git grep -n -- "$t" origin/automation/testids -- src/
```

A hit inside a helper call (`getXSlotProps(...)`, `buildTestIds(...)`, an options
object) is real wiring. Only "no stage-1 hit at all" means absent.

Related: [[static_review_verify_new_page_object_attrs_exist]]
