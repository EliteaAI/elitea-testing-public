---
name: A duplicate FIX card is the cheapest place to deliver the verification the ORIGINAL never ran
description: Confirming a duplicate costs ~zero; spend the freed budget on the evidence the survivor's closure record lacks (usually a DEV run), so a zero-code session still ships a new fact
type: feedback
aliases: [duplicate card value, zero-work session, re-certification, DEV verification on a duplicate, what to add on a dupe]
tags: [area/triage, area/test-repair, type/gate]
created: 2026-09-09
updated: 2026-09-10
---

## The trap

Once a card is confirmed a duplicate, the obvious move is: label it, point at the
survivor, go `Ready`. Correct but **under-spent** — triage cost two `gh` calls and the
session budget is otherwise unused. Meanwhile the survivor's closure record almost
always has a gap, because the survivor was under pressure to ship a repair.

Cheapest possible confirmation, two calls: `git merge-base --is-ancestor <repair-sha>
<the-commit-CI-tested>` and `git rev-list --count origin/main..origin/automation/base`.
If the repair is absent from the tested tree, you are done reasoning.

## The menu, in value order

1. **Run the environment the original could not / did not.** Highest value: it can
   *disagree*, and then the duplicate has caught a real miss.
   1b. **Certify the MERGED artifact** when the original gated a pre-merge branch —
   squash + side commits mean the branch green is not the shipped green.
2. **Re-derive the promotability row** — the row most often copied rather than
   verified, and the canonical grep has known false-negative shapes (#2100).
3. **Re-verify Form C** against *this* run's own `reports/junit.xml`.
4. **Name the promotion gap with a NUMBER**, and name its vehicle.

## Promotability is provable by EXECUTION, and that beats the grep

`dev.elitea.ai` serves the EliteaUI build from **`main`**, and `LocatorDescriptor` has
no fallback rung — so a testid absent from `main` *cannot* resolve there. **A spec that
runs end-to-end green on DEV has proven every testid on its executed path is on `main`**,
immune to both grep blind spots (multi-line attributes #2100, main-side value divergence
#2142). One DEV gate therefore delivers menu items 1, 1b and 2 at once. When the oracle
is an attribute *value*, still read main's source (`git show origin/main:<file>`) — the
grep cannot judge divergence.

## The DEV run recipe (shell env is IGNORED — `config.py` orders dotenv first)

`ELITEA_URL=… pytest` silently runs localhost. `.env.test` is a **symlink** (BSD `sed -i ''`
refuses it, silently). Resolve it, edit the real file, assert the resolver agrees, restore
via `trap` — all inside ONE detached script, so a dead session cannot leave the shared
workspace pointed at DEV:

```bash
REAL=$(python3 -c "import os;print(os.path.realpath('.env.test'))")
BAK=/tmp/envtest.bak.$$; cp -p "$REAL" "$BAK"
restore(){ cp -p "$BAK" "$REAL"; diff -q "$BAK" "$REAL" >/dev/null && echo "[ENV RESTORED OK]"; }
trap restore EXIT INT TERM
# python re.sub ELITEA_URL=https://dev.elitea.ai / APP_PREFIX=/app in "$REAL"
T=$(../.venv/bin/python -c "from config import settings;print(settings.app_base_url)")
[ "$T" = "https://dev.elitea.ai/app" ] || exit 2      # REFUSE — a failed swap yields
                                                      # cheerful localhost greens
```
Echo the target again after the restore — that line IS the receipt.

**Budget for the environment's own noise.** Classify attempt CAUSES from
`reports/allure-results/*-result.json`, never invocation exit codes: DEV `Page.goto`
failures ([[dev_goto_lifecycle_waiter_never_resolves]], #2124) run 30–78% of attempts in
bursts and are a *precondition*, never a sanctioned-RED member. Read `reruns.json` after
every invocation — `1 passed` hides two dead attempts.

**One counterexample retires a deterministic failure.** CI recorded 3/3 identical; a
single clean run is logically sufficient. Nothing merges on a duplicate card, so
§ Merge gate does not even apply — 3× is margin, not obligation.

## Occurrence ledger (each: confirmed, zero code changed)

| Dupe | Case | What the survivor lacked, and what this pass added |
|---|---|---|
| #2115 | ELITEA-2367 | survivor gated localhost on a DEV-raised red → added 1 DEV run |
| #2137 | ELITEA-0679 | survivor argued DEV equivalence in prose → 3× DEV, card's signature 0 of 9 |
| #2140 | ELITEA-2453 | DEV already spent → certified the **squash-merged** artifact (menu 1b) |
| #2141 | ELITEA-2367 (3rd) | → 3× DEV on the merged artifact |
| #2144 | ELITEA-2448 | localhost-UI-on-DEV-backend gate → real DEV proves the **promoted** UI |
| #2165 | ELITEA-1901 (4th) | two survivors both gated localhost → 3× DEV green on the merged artifact |

**Dedup key: only the ELITEA id survives every observed shape.** Run id varies
(#2165 came from a *different* nightly), and intake's own failure-pattern label
rewrites the title after the `[FIX][ELITEA-…]` stem.

## Rule

Confirm the duplicate in the first two calls, then ask: **what does the survivor's
closure record ASSERT but not SHOW?** Deliver exactly that, and say in the record that
it is what this pass adds. Never re-do the survivor's work to re-do it.

**Name the generator, not just the symptom.** The re-file is not the survivor's fault:
repairs land on `automation/base`, CI runs `main`, so every nightly regenerates the card
until a human promotes. Say it with a number and a vehicle — 2026-09-10: gap **438**
commits, growing ~5/day, and the only open promotion PR (#1084, draft since 08-01) is
1,402 commits behind and does not contain the repair. That is the only part a human can act on.

Related: [[dev_goto_lifecycle_waiter_never_resolves]] · [[a_fix_card_can_have_no_work_in_it]] · [[a_delivered_card_is_not_verified_until_the_env_ran_it]]
