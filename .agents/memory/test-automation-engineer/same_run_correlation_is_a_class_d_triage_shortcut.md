---
name: Same-run correlation is a class-D triage shortcut
description: Before deep-diving a [FIX] timeout card, check sibling [FIX] cards from the same CI run/job — shared signature across unrelated tests means infra, not drift.
type: reference
aliases: [adjust-automated-test triage, class D shortcut, CI navigation timeout wave]
tags: [area/test-execution, area/triage, area/environment]
created: 2026-09-08
updated: 2026-09-08
---

## The signal

`adjust-automated-test` Step 2 asks you to classify A(UI drift)/B/C/D(infra)/E/F. Before
reading any AFS/code diff, check whether OTHER `[FIX][ELITEA-<id>]` cards reference the
**same CI run id** (or an adjacent run within the same job window). If several unrelated
tests — different pages, different flows, different page objects — failed with the same
`Locator.wait_for`/`Locator.click` Timeout signature in the same job, that is strong,
cheap, up-front evidence for **class D (infra/flake)**, not per-test UI drift. Pull the
job log and grep for `FAILED`/`Timeout` — a handful of unrelated navigation timeouts in
one job is the tell.

## Worked example (ELITEA-1898 / issue #2049, 2026-09-08)

CI run 34244735426 (`UI Tests DEV Stable [main]`, job `dev-stable - agents`) failed 6
unrelated tests in one job, all navigation/interaction timeouts: "Navigate back" (→ sibling
card #2042/ELITEA-1869, actually a DIFFERENT but adjacent run #105), "Navigate to agent"
(→ #2049/ELITEA-1898, THIS card), "Navigate to agents list" (→ #2050/ELITEA-1870, SAME
run), "Select a version by name from the VERSION dropdown" (×2, unticketed). All from the
same job run within a ~17-minute window. Reproduced ELITEA-1898's own spec against DEV
(`https://dev.elitea.ai`) locally: **green, single-shot, 0 reruns, 46.62s** — confirming
"green locally, red in CI" = class D per the skill's own rule, not drift. No code change
made; case text and AFS remain accurate.

## Also see

`dev_env_run_harness_and_goto_flake.md` — documents the underlying mechanism (browser/SPA
navigation latency against a deployed env, pre-existing, "re-run" is the correct response)
and, critically, the **correct way to point a local run at DEV** (out-of-repo `-p` plugin
harness) — do NOT edit the shared `.env.test` directly, even temporarily-and-reverted.
