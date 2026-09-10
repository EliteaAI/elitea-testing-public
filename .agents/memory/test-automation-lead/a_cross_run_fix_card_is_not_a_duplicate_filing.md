---
name: A cross-RUN repeat FIX card is NOT a duplicate filing — dedup cannot fix it, only promotion can
description: Same-run twins are an intake artifact a dedup key solves; a card from a LATER CI run is a true red correctly re-detected, and it recurs nightly forever until a human promotes
type: feedback
aliases: [cross-run recurrence, same run vs different run, promotion gap recurrence, duplicate vs re-detection, nightly re-files]
tags: [area/triage, area/promotion, type/process]
created: 2026-09-10
updated: 2026-09-10
---

## The distinction that changes the disposition

Two `[FIX]` cards with a byte-identical title and node id are NOT the same thing. Check
the **CI run id** before you reason about anything else:

| Shape | What it is | What fixes it |
|---|---|---|
| Same run id, 2+ cards | intake **double-filing** — an artifact | a dedup key (#2135 options A/B) |
| **Different run ids** | a true red on `main`, **correctly re-detected** | **only promotion** |

ELITEA-2453 produced both shapes within 24 h: #2120 + #2140 were one run (34331579791)
filed twice; **#2172 was a later nightly** (34436416962) on a newer `main` commit.

## Why it matters more than it looks

For the cross-run shape, the intake pipeline did its job. No dedup key of any shape
prevents the card, because it is not a duplicate — the test really is red on the branch
CI runs. So:

- **The card will re-file every night, indefinitely.** Labelling duplicates does not slow it.
- **The arrival rate is bounded below by the merge rate of repairs.** Every fix merged
  into `automation/base` becomes a future `[FIX]` card against `main`.
- Therefore FIX-intake signal quality degrades **monotonically** with the size of the
  `main..automation/base` gap. (Measured: 420 -> 452 commits in one day.)

## The 30-second proof of which artifact CI ran

The traceback's **line number** is a property of the tested tree — cheaper and harder to
argue with than any prose:

```bash
git fetch origin
git show origin/main:<path> | sed -n '<line>p'              # matches the CI failure verbatim?
git log origin/automation/base --oneline -1 -- <path>       # repair commit, file untouched since?
git rev-list --count origin/main..origin/automation/base
```

If `main`'s line N is the failing assertion and `automation/base`'s line N is something
else entirely, you are done — no re-run needed to classify it.

## What to do with it

Still label `duplicate` + survivor (lower number), still `Ready` — but do NOT stop there,
and do NOT let it be filed as a sixth question card. Comment the occurrence onto the
existing survivor question card with (a) the run-id table proving it is cross-run, (b) the
gap measured twice so the growth is visible, and (c) options. Recommend **re-pointing the
nightly at `automation/base`** (restores honest daily signal at ~zero cost) **plus** a named
owner for promotion cadence. An "already-fixed-on-base ⇒ skip intake" rule is a *silencer*:
it stops the churn but leaves `main` red and the coverage claim false. Say so explicitly.
