---
name: Onboarding suite flakes with a DIFFERENT symptom nearly every run
description: tests/ui/onboarding/ intermittently fails with a different test+error class each run; re-run before treating an onboarding red as real.
type: project
aliases: [onboarding-welcome-card, mock_fresh_user_state, ELITEA-2232 flake, onboarding gate flake, onboarding suite flaky]
tags: [area/onboarding, type/flake]
created: 2026-08-24
updated: 2026-08-24
---

## Symptom — it is NOT one flaky assertion

Originally logged as a single welcome-card precondition miss. Widened
2026-08-24: the whole `tests/ui/onboarding/` directory is intermittently
unstable, and **the failing test and the error class differ almost every run.**

Four consecutive invocations of the identical command
(`HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/ -v -p no:cacheprovider`),
same session, same machine, only a comment-text diff between them:

| Run | Result | Symptom |
|---|---|---|
| 1 | 1 failed, 3 passed, 1 error (47s) | provisioning: poll count `1 >= 2` false; tips_card: `TargetClosedError` — `Route.fetch: Request context disposed` |
| 2 (control, pristine HEAD) | **5 passed**, 1 auto-rerun (112s) | — |
| 3 | 2 failed, 3 passed (81s) | jump_in: `Locator expected to be visible`; provisioning: `TypeError: JSONDecodeError.__init__() missing 2 required positional arguments` |
| 4 | **5 passed** clean (60s) | — |

Note run durations swing 47s → 112s, and run 1 was the *fastest* because an
early context disposal cascaded.

## Why this matters

A red here proves nothing on its own. Both a pristine tree and a
comment-only diff produced reds *and* clean 5/5 passes. Anyone bisecting an
onboarding red against a code change will chase a ghost — I nearly did, and
only a pristine-control run plus a repeat settled it.

## What to do next time

1. **Re-run before believing it.** One clean 5/5 is normal after a red.
2. If you are checking whether *your change* caused it, run a **pristine
   control** (`git checkout --` the files, run, re-apply) — cheap and decisive.
3. Only if a symptom repeats *identically* across runs treat it as real; the
   signature of this noise class is that it does not.
4. Mechanisms still unruled-out: route-mock racing the first `authorDetails`
   call from `ProtectedRoutes.jsx`; storage carry-over
   (`sessionStorage.onboarding_state`,
   `localStorage["interactive-tour:first-elitea:pending"]`) between contexts;
   shared-backend strain (same class as the `#1082` chat pollution notes).

Consistent with the broader documented noise culture in `.agents/testing.md`
§ Known issues / Unconfirmed. Worth a `.agents/testing.md` entry by the lead if
it keeps costing gate time.

Related: [[onboarding_provisioning_state_entry]] · [[onboarding_tour_state_without_mocks]]
