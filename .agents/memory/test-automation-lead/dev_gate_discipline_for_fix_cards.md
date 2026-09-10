---
name: DEV gate discipline for FIX cards
description: How to gate a [FIX] card on dev.elitea.ai without the two traps that silently invalidate the result — the .env.test symlink and green-but-not-clean invocations
type: feedback
aliases: [DEV gate, env.test symlink, gate on dev.elitea.ai, reruns.json, FIX card gate]
tags: [area/merge-gate, type/procedure]
created: 2026-09-10
updated: 2026-09-10
---

## Why this needs its own procedure

A `[FIX]` card's failure lives on **DEV**, so a localhost green certifies
nothing. But both ways of gating on DEV fail *silently* if done casually.

## Trap 1 — the swap that doesn't happen

`automation/.env.test` is a **symlink** to the shared master env file.
`sed -i ''` refuses symlinks, exits non-zero, and leaves the file untouched —
so the pytest runs proceed happily against **localhost** and produce cheerful
greens. Shell `ELITEA_URL=… pytest` fails the same way (dotenv beats env vars).

The recipe that works: resolve with `realpath`, rewrite the real file with
python, then **assert the framework's own resolver agrees** before running
anything —

```bash
TARGET=$(../.venv/bin/python -c "from config import settings; print(settings.app_base_url)")
[ "$TARGET" = "https://dev.elitea.ai/app" ] || exit 2     # the load-bearing half
```

Put swap + all N invocations + restore in **one detached script** with
`trap … EXIT INT TERM`. The master file is shared by all four sibling clones,
so a killed turn would otherwise strand the whole workspace on DEV. Echo
`settings.app_base_url` again after the restore.

## Trap 2 — green is not clean

`pytest.ini` sets `--reruns=2`, so an invocation that lost two attempts still
prints `1 passed` and records PASS in junit. **`cat reports/reruns.json` after
every invocation** — `{}` is the only clean reading. Per-attempt causes live
in `reports/allure-results/*-result.json` (`statusDetails.message`, grep by
`fullName`), never in the pytest tail.

## Trap 3 — the DEV Page.goto hazard is not your signature

`#2124`/`#2156` produce `Page.goto` timeouts and `net::ERR_ABORTED` at
**preconditions** — allure `broken`, often 0 steps, bursty (measured up to
7 of 9 attempts). Upstream of every assertion ⇒ **never** a member of a
sanctioned-RED closed set. **Re-gate; never accept 2-of-3. Never raise the
timeout.** Classify by cause, not by invocation exit code.

## And check the sanctioned-RED still applies to the env you gated on

A spec's documented sanctioned-RED may be **DEV-build-only**. Before reading a
DEV green as "the defect is fixed", ask whether the signature can physically
occur there. See `.agents/testing.md` § Merge gate (ELITEA-1892/#2082, and the
#1215 instance from #2166).

Related: [[intake_card_boilerplate_can_contradict_project_canon]]
