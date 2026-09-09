---
name: Changing a page-object parameter default is a blast-radius review, not a one-line review
description: A default change silently re-times every caller that omits the arg — grep all call sites before ruling on scope
type: feedback
aliases: [default timeout change, page object default, blast radius, wait_for_bucket_in_list default]
tags: [area/review, type/scope]
created: 2026-09-09
updated: 2026-09-09
---

## The check

When a diff changes a **parameter default** on a shared page-object method, the diff
shows one line but the behaviour change reaches **every caller that omits that
argument** — including callers in specs the diff never opens, on cases the card
never named. A "scope: only the one call site changed" claim in a card or Run
Report is unverified until you have listed the call sites yourself.

```bash
grep -rn "<method_name>" automation/ | grep -v '\.pyc'
# then read each multi-line call: does it pass timeout= explicitly?
```

Three outcomes, three verdicts:

- **Every other caller passes the arg explicitly** → the default change is genuinely
  scoped to the one call site. Approve on scope.
- **Some caller omits it** → that caller silently inherits the new value. It must be
  either in scope (and reviewed) or the change must be made at the call site instead.
- **A caller omits it and is a NEGATIVE/absence wait** → hard blocker: a longer
  default on an absence assertion changes how long the test is willing to be wrong.

## Worked instance — #2084 / ELITEA-1808 (2026-09-09)

`ArtifactsPage.wait_for_bucket_in_list()`'s default went `15000` → 
`BUCKET_ROW_AFTER_REFETCH_TIMEOUT = 60_000`. The card scoped the change to one call
site, and the grep confirmed it: **all 12 sibling call sites pass an explicit
`timeout=`** (`BUCKET_LIST_TIMEOUT` / `NAVIGATION_TIMEOUT` / `UI_ELEMENT_TIMEOUT`),
so none of them moved. The symmetric `wait_for_bucket_removed_from_list()` — the
absence wait — kept its own `15000` default and was correctly left alone (tracked
as #2127). Without the grep, "only one call site changed" was an assertion, not a
finding.

## Related pattern: a raised budget is not masking, but it has a shelf life

Raising a wait's budget still fails on a genuine "it never appears" regression — it
just fails slower, so it is not defect masking. What it *does* do is buy headroom
against a growing cost. Ask what is growing: if the growth (here, `#636`'s leaked
buckets inflating an unpaginated list) is unfixed, the new budget decays and the
same red returns. Flag the growth driver in the verdict so the follow-up card is
the rate-limiter, not the next CI run.

Related: [[open_cross_cutting_defects]]
