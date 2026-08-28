---
name: A deployed-env-only failure cannot be gated locally — run the branch on dev via test-ui-custom
description: APP_PREFIX/env-conditional defects are invisible to the localhost gate by construction; a 3x-green local run is not evidence the fix works
type: feedback
aliases: [app_prefix, deployed env verification, test-ui-custom, /app prefix, env-conditional failure, GHA verification]
tags: [area/gating, area/ci, type/trap]
created: 2026-08-28
updated: 2026-08-28
---

## The class

Any defect whose trigger is an environment-conditional value — the canonical one
being `settings.app_prefix` (`""` on localhost, `/app` on DEV/STAGE/NEXT) — is
**green on localhost by construction**. The local merge gate cannot fail it, so
3x-green locally proves *no regression*, never *the fix works*.

Symptom shape: `assert '/app/pipelines/create' == '/pipelines/create'` from GHA,
passing locally forever. (ELITEA-2020 / #1889, 2026-08-28.)

## The verification that actually counts

Run the fix branch against the real env via the reusable workflow, which accepts
both a `--ref` and a `ref` **input** (the input is what the checkout step uses):

```bash
env -u GITHUB_TOKEN gh workflow run test-ui-custom.yml \
  --repo EliteaAI/elitea-testing-public \
  --ref <fix-branch> \
  -f environment=dev -f suite=<suite> -f markers=all -f ref=<fix-branch>
```

`test-ui-custom.yml` hardcodes `APP_PREFIX: '/app'`, and `test-ui-dev-*.yml` are
thin `workflow_call` wrappers around it — so a grep for `APP_PREFIX` in the dev
workflow comes back empty and **looks** like the variable is never set. It is.
Don't conclude "dev doesn't set it" from that grep.

## Two traps in the harvest

- **Do NOT pass `parallel_jobs=1`.** It skews the workflow's user/project
  credential assignment: the run comes back with ~30
  `403 access_denied … 'current_permissions': []`, `project_id: None` on every
  API-creating fixture. Those failures are yours, not the branch's — the nightly
  run of the same suite had zero. Leave `parallel_jobs` at its default.
- **The job conclusion is not the answer — grep the log for your own test.**
  `gh run view --job <id> --log`, then grep the test name for its
  `PASSED [ nn%]` line. (`gh api .../jobs/<id>/logs` returned empty; the
  `gh run view --job` form worked.)

## Prefer a self-proving assertion

Parameterising by the setting (`== f"{settings.app_prefix}/pipelines/create"`)
makes the deployed green **self-proving**: it can only pass if the prefix really
resolved to `/app`. Never repair this class by weakening to `.endswith(...)`/`in`
— that trades a real deployed bug for a permanently weaker assertion.

Related: [[running_the_suite_against_dev_without_editing_env_test]] (the local
alternative when you need a DEV run without CI) · [[tms_index_backwrite_surgical_not_full_rebuild]]
