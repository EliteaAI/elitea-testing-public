---
name: A duplicate FIX card is the cheapest place to deliver the verification the ORIGINAL never ran
description: Confirming a duplicate costs ~zero; spend the freed budget on the evidence the survivor's closure record lacks (e.g. the DEV run behind a DEV-raised red), so a zero-code session still ships something new
type: feedback
aliases: [duplicate card value, zero-work session, re-certification, DEV verification on a duplicate, what to add on a dupe]
tags: [area/triage, area/test-repair, type/gate]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Once a card is confirmed a duplicate, the obvious move is: label it, point at the
survivor, go `Ready`. That is *correct* but *under-spent* — the triage cost about two
`gh` calls, and the session budget is otherwise unused. Meanwhile the survivor's
closure record almost always has a gap, because the survivor was under time pressure
to ship a repair.

## What happened (#2115, ELITEA-2367)

#2079 repaired the Catalog filter-rail drift and gated it **3× on localhost**. But the
red it repaired was raised by the **DEV Stable nightly** — and the rail mixes frontend
constants with *backend data*, which need not match between environments. So
"the expectation is derived from the response, therefore it holds everywhere" was an
**argument**, not evidence. Nobody had run it on DEV.

On the duplicate card I ran 3× localhost (12.47/11.11/11.08 s) **plus one run against
`https://dev.elitea.ai`** — PASS in 22.43 s, `reruns.json {}`. Zero lines of code
changed and the session still produced a fact that did not previously exist.

## The DEV run recipe (shell env is IGNORED — `config.py` orders dotenv first)

`ELITEA_URL=… pytest` silently runs localhost. The env FILE must be swapped and
restored; do it in ONE bash call with a trap so a dead session cannot leave the
shared `.env.test` (a symlink to the master in the parent folder) polluted:

```bash
REAL="$(cd "$(dirname "$(readlink .env.test)")" && pwd)/$(basename "$(readlink .env.test)")"
BAK="/tmp/envtest.bak.$$"; cp -p "$REAL" "$BAK"
restore() { cp -p "$BAK" "$REAL"; diff -q "$BAK" "$REAL" >/dev/null && echo "[ENV RESTORED OK]" || echo "[RESTORE FAILED]"; }
trap restore EXIT
sed -i '' -E 's|^ELITEA_URL=.*|ELITEA_URL=https://dev.elitea.ai|; s|^APP_PREFIX=.*|APP_PREFIX=/app|' "$REAL"
HEADLESS=true ../.venv/bin/pytest "$NODE" -v -p no:cacheprovider
```

Never print the file. Assert the restore in the output — that line IS the receipt.

## The menu, in value order

1. **Run the environment the original could not / did not** (above). Highest value:
   it can *disagree*, and then the duplicate has caught a real miss.
2. **Re-derive the promotability row.** It is the row most often copied rather than
   verified, and the documented grep still has false-negative shapes (#2100 —
   `chipTestIdPrefix=` reported `main:no` when the truth is `main:YES`).
3. **Re-verify Form C** against this run's own `reports/junit.xml`.
4. **Name the promotion gap with a NUMBER.** `git rev-list --count origin/main..origin/automation/base`
   — 399 on 2026-09-09. "Not promoted" is a shrug; "399 commits behind, staged in no
   open PR" is something a human can act on.

## Rule

Confirm the duplicate in the first two calls, then ask: **what does the survivor's
closure record ASSERT but not SHOW?** Deliver exactly that, and say in the record
that it is what this pass adds. Never re-do the survivor's work to re-do it.
