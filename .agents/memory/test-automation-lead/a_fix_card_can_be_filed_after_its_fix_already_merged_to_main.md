---
name: A [FIX] card can be filed AFTER its fix already merged to main — check main HEAD at filing time, not the run's commit
description: The intake keys on the CI run's commit; a promotion that lands between the run and the filing produces a card whose failure string is already gone from main — one git grep on origin/main HEAD proves it before any log is opened
type: feedback
aliases: [filed after promotion, stale run card, intake lag, run commit vs main head, message grep on main head, same-run twin after promote]
tags: [area/triage, area/promotion, type/process]
created: 2026-09-16
updated: 2026-09-16
---

## What happened (#2336, ELITEA-2022, 12th card on one node id)

Run #167 executed `main@7e33cd5` at 14:50Z. The #2330 session promoted the repair to `main`
(PR #2334, `79b380eeb`) at **15:39:57Z**. The intake filed #2336 at **15:53:50Z** — against the
run, whose artifact was already 3 commits stale. Both #2330 and #2336 cite the same run id, so this
is a same-run twin, but with a twist: by the time it existed, there was nothing left to promote.

## The one-command disposition

```bash
git fetch origin
git grep -nF '<failure message from the job log>' origin/main -- automation/   # 0 hits ⇒ already on main
git log <ci-commit>..origin/main --oneline                                       # names the promotion PR
```

The message-string grep is the cheapest proof there is — cheaper than the ancestry check (no
repair SHA needed) and immune to the #2175 call-path false negative. Run it against `origin/main`
HEAD, not against the commit the card names: **the card's `Commit:` line tells you what CI ran,
never what `main` is now.**

## Still owes a gate

A null delta is not a no-op delivery. The previous session gated the *PR head*; `main` HEAD had
moved (#2335 touched `fixtures/data_fixtures.py`). Detached `origin/main` checkout, `-p devenv`
harness, 3/3 on DEV, `reruns.json {}` each — that is what makes the closure record stand on its own
instead of pointing at someone else's gate of a different SHA. ~2 min of wall clock.

## Housekeeping that bit

`git checkout --detach origin/main` refuses if a *tracked* memory file has uncommitted edits
(`.agents/memory/test-automation-lead/MEMORY.md` is tracked). `git stash push -- <file>` before,
`git stash pop` after. Also check `git status -sb` for `[ahead N]` — the previous session's memory
commit was unpushed.
