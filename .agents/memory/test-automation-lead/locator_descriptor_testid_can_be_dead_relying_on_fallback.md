---
name: LocatorDescriptor testid can be dead, relying on fallback
description: a testid= value with zero grep hits on main AND automation/testids means the locator is silently resolving via its legacy fallback= only
type: feedback
---

During closure-record verification (any testid the case's diff USES, not just
the ones it ADDS), a `LocatorDescriptor(testid="x", fallback=...)` field can
have a `testid=` value that matches **zero** `data-testid` anywhere in
EliteaUI `src/` — on `main` or on `automation/testids`. When that happens the
locator has been resolving purely through its legacy CSS `fallback=` this
whole time, and the tests using it have never actually exercised the testid
path at all — a silent gap in the testid-coverage metric the team measures.

This is easy to miss because the tests still pass (the fallback works) and
the page object LOOKS testid-configured. Catch it the same way the closure
record's promotability check already does — it's just one more row in the
same grep sweep, not extra work:

```bash
for t in <every testid the diff's page-object calls touch, including reused pre-existing ones>; do
  git grep -- "$t" origin/main -- src/ | grep -qE '(data-testid|testid.*=.*'"$t"')' && echo YES || echo "NO — check fallback="
done
```

A "NO" on BOTH refs (not just `main`) is the tell — a rename would still show
up on one side or the other; total absence means the testid string was never
real, or the element it targeted was removed and nobody re-pointed the
`LocatorDescriptor`.

Don't silently note-and-move-on: dedup-check the tracker before filing (light,
one `gh issue list` + keyword grep) — this exact shape is often ALREADY
tracked as tech debt (case: `pipeline-yaml-view`/`pipeline-flow-view` in
`pipeline_detail_page.py`, found 2026-08-07 during ELITEA-2026's closure,
already tracked as #1161 — cross-referenced, not refiled).
