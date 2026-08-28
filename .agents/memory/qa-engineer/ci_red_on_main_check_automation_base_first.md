---
name: CI red on main — check automation/base for an existing fix FIRST
description: A merged test red in CI on `main` is often already fixed on `automation/base`; diff the two refs before triaging drift.
type: feedback
aliases: [test-code promotion gap, main vs automation/base drift, CI red already fixed, adjust-automated-test class F]
tags: [area/ci, type/triage]
created: 2026-08-28
updated: 2026-08-28
---

## The class the triage table does not name

`adjust-automated-test` § Step 2 has a **class F promotion gap**, but it is
scoped to *testids* (`automation/testids` vs EliteaUI `main`). There is a
second, distinct promotion gap: **the TEST CODE fix lives on
`automation/base` and was never promoted to `main` — and CI runs `main`.**

Symptom is indistinguishable from fresh drift: a real, reproducible failure
with a real root cause. The difference is that the fix already exists.

## First move, before any live exploration

```bash
git fetch origin
git log --oneline origin/main..origin/automation/base -- <test file>
git diff origin/main origin/automation/base -- <test file>
```

A commit there ⇒ the job is a **port**, not an adjustment: no re-analysis,
no new AFS, no testid work. Costs one command; saves a full triage session.

## Worked case — ELITEA-2051 (issue #1896, GHA 33066098636)

`test_pipeline_fork_to_different_project` red on `main` with
`select-option-399` never visible. `9bb6badd5` (PR #1803, issue #1800) had
fixed it on `automation/base` two days earlier. `main` still carried
`e42e71536`, a direct-to-`main` human commit that made SOURCE env-derived
while leaving TARGET hardcoded `399` — inverting the case's project pair.

**Do not assume the local `.env.test` masks it.** Locally
`elitea_project_id == 399`, so main's version resolves source == target ==
399, and the product excludes the selected project from the Fork target
dropdown — the same red, by a different mechanism. Reproducing it locally
against DEV took one run.

Related: [[running_the_suite_against_dev_without_editing_env_test]] (lead layer)
