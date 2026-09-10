---
name: A duplicate FIX card is the cheapest place to deliver the verification the ORIGINAL never ran
description: Confirming a duplicate costs ~zero; spend the freed budget on the evidence the survivor's closure record lacks (e.g. the DEV run behind a DEV-raised red), so a zero-code session still ships something new
type: feedback
aliases: [duplicate card value, zero-work session, re-certification, DEV verification on a duplicate, what to add on a dupe]
tags: [area/triage, area/test-repair, type/gate]
created: 2026-09-09
updated: 2026-09-10
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

## Second confirmation (2026-09-10, #2137 / ELITEA-0679) — same play, same payoff

#2112 repaired the dead `select_model("GPT-5.2")` literal and gated **3x on localhost**,
justifying DEV equivalence in prose ("localhost talks to the same DEV backend, and the
localhost identity is the weaker one"). Sound reasoning — but still an argument. The
red it repaired came from the **DEV Stable nightly**, and the card's own Work Scope
named DEV as the verification environment.

On the duplicate I ran the two specs **3x against `https://dev.elitea.ai`**: 9 attempts,
**5 clean end-to-end greens**, and the card's reported signature (`Locator.wait_for:
Timeout 10000ms exceeded` on *Select model*) **0 times**. Zero lines of code, and the
argument became a measurement.

Two transferable details:

- **One counterexample retires a deterministic failure.** CI recorded 3/3 identical
  failures, so a single clean run is logically sufficient; I ran three for margin, not
  for proof. Don't reflexively spend a full 3x gate re-certifying someone else's merge —
  nothing is merging on a duplicate card, so § Merge gate does not even apply.
- **Budget for the environment's own noise.** 4 of the 9 attempts hung in
  [[dev_goto_lifecycle_waiter_never_resolves]] — a precondition failure, upstream of
  every assertion, never a sanctioned-RED member. Classify those OUT before reading the
  result, or a DEV verification looks like a red when it is a clean green.

## Third confirmation (2026-09-10, #2140 / ELITEA-2453) — when menu item 1 is ALREADY spent

#2120 had *already* run DEV 3/3, so the highest-value item was gone. The gap that was left is
one worth looking for every time: **it gated the pre-merge BRANCH, not the squash-merged
artifact.** #2154 squashed to `716777790` with the AFS amendment in a separate commit — exactly
the shape where a pre-merge green stops certifying what shipped. Re-running the merged
`automation/base` artifact on DEV is a new fact, and it is cheap.

**Add to the menu as item 1b: certify the MERGED artifact when the original gated a branch.**

The other half of this pass: 4 invocations = 9 attempts, and the raw tally (2 passed, 7 not)
reads like a failure. By cause it is 7x `Page.goto` (`broken`, a precondition) and **0**
assertion failures — the card's own signature appeared 0 of 9 times. **Read attempt CAUSES
from `reports/allure-results/*-result.json`, never invocation exit codes**, or a passing
repair reports as a DEV red. See [[dev_goto_lifecycle_waiter_never_resolves]].

Also worth the two `gh` calls before filing anything: the promotion-gap finding I was about to
file as a new `question` was **already** card #2157, which had even predicted this recurrence.
Commenting the occurrence there beat splitting the evidence.

## Fourth confirmation (2026-09-10, #2144 / ELITEA-2448) — the DEV green certifies the PROMOTED UI

#2076 gated 3x with a **localhost UI pointed at the DEV backend** while the card's Work Scope
named `dev.elitea.ai`. Ran the squash-merged artifact 3x on real DEV: 104.40 / 64.50 / 67.63 s,
all green.

**The new, transferable fact — promote this above menu item 2:** `dev.elitea.ai` serves the
EliteaUI build from **`main`**. So a green there proves the repair is compatible with the
*promoted* UI and leans on zero unpromoted testids. That is strictly stronger than the closure
record's testid grep, which proves only *presence* and has two known blind spots — false-absent
on runtime-composed testids (#2100) and main-side **value** divergence (#2142). When a repair's
oracle is an attribute value, also read main's source directly: here `RunStatus.jsx:16` is
`data-status={status}`, a raw pass-through, so no divergence is possible. The grep cannot make
that call; one `git show origin/main:<file>` can.

**Dedup shape #3 — classification, not wording or run id.** #2076 and #2144 share run id *and*
node id (the key the #2143 pass recommended). What varied was intake's own failure-pattern
label: `assertion-failure` -> `element-not-found`, description reworded, so titles diverge after
the `[FIX][ELITEA-2448]` stem. With the ELITEA-1866 cross-run triple (differing run ids) on the
other side, **only the ELITEA id survives every observed shape.**

**Name the generator, not just the symptom.** The gap is now 428 commits and grew 8 in one day.
Intake dedup stops the re-file; the promotion backlog *creates* it. Every repair merged to
`automation/base` today is a guaranteed re-file tomorrow. Say that in the closure record with a
number — it is the only part a human can act on.

## The menu, in value order

1. **Run the environment the original could not / did not** (above). Highest value:
   it can *disagree*, and then the duplicate has caught a real miss.
1b. **Certify the MERGED artifact** when the original gated a pre-merge branch (squash +
   side commits mean the branch green is not the shipped green).
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

## Third occurrence — #2141, same case again (2026-09-10)

ELITEA-2367 has now generated **three** cards off one repair: #2079 (the delivery),
#2115, #2141. The pattern is stable and so is the value-add: #2079 gated on localhost,
#2115 added a single DEV run, #2141 added the **3× DEV gate on the squash-merged
`automation/base` artifact** (32.15 / 127.34 / 51.69 s, 3/3 green; the only non-green
attempts were two #2124 `Page.goto` reruns, allure `broken`, at a precondition).

The recurrence itself is the finding, and it is not the survivor's fault: the repair
is merged to `automation/base` and CI runs `main`, so **every** nightly re-files it
until a human promotes. Say that in the closure record with the naming of the owner —
and log the occurrence on #2157 rather than filing a fourth card.

Cheapest possible confirmation, two calls:
`git log --oneline origin/main -- <path>` vs `origin/automation/base` — if the repair
sha is absent from `main`, you are done reasoning.

