---
name: A deployed-env-only failure cannot be gated locally — run the branch on dev via test-ui-dev-stable
description: APP_PREFIX/env-conditional defects are invisible to the localhost gate by construction; a 3x-green local run is not evidence the fix works
type: feedback
aliases: [app_prefix, deployed env verification, test-ui-custom, test-ui-dev-stable, ELITEA_PROJECT_ID 0, /app prefix, env-conditional failure, GHA verification]
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

Run the fix branch against the real env — **through the ENVIRONMENT workflow,
never `test-ui-custom.yml` directly**:

```bash
env -u GITHUB_TOKEN gh workflow run test-ui-dev-stable.yml \
  --repo EliteaAI/elitea-testing-public \
  --ref main \
  -f ref=<fix-branch> -f suite=<suite>
```

The `ref` **input** is what the checkout step uses; `--ref` only picks which
copy of the workflow file runs (keep it on `main`).

### Why not `test-ui-custom.yml` directly — CORRECTED 2026-08-28 (#1896)

`test-ui-custom.yml` is a **reusable** workflow whose credentials arrive as
`workflow_call` `secrets:` mapped BY THE CALLER. The repo's secrets are
environment-qualified (`TEST_USER_PROJECT_DEV_1`, `..._STAGE2_1`, …), and
`test-ui-dev-stable.yml` maps them onto the unqualified names the reusable
workflow reads:

```yaml
TEST_USER_PROJECT_1: ${{ secrets.TEST_USER_PROJECT_DEV_1 }}
```

`test-ui-custom.yml` line 506 reads
`secrets[format('TEST_USER_PROJECT_{0}', matrix.suffix)]`. Dispatch it
**directly** and no caller populated that block, so every one resolves EMPTY —
`ELITEA_PROJECT_ID` becomes `0` and every project-scoped fixture dies.

**This supersedes this entry's earlier claim that `parallel_jobs=1` causes the
`403 access_denied … project_id: None` family.** Controlled comparison, same
branch, same session, 2026-08-28:

| Dispatch | `parallel_jobs` | Result |
|---|---|---|
| `test-ui-custom.yml` (direct) | 1 | `ELITEA_PROJECT_ID resolved to 0` |
| `test-ui-dev-stable.yml` | 1 | ✅ target test PASSED |

`parallel_jobs=1` is **exonerated** — it was a coincident variable, not the
cause. The dispatch entry point was.

### Harvesting the result

**The job conclusion is not the answer — grep the log for your own test.** A
suite job goes `failure` on any member. `gh run view <id> --log`, then grep your
test name for its `PASSED [ nn%]` line, and check whether the other failures
pre-date your branch (look them up in the originating nightly run) before
attributing any of them to your change.

## Prefer a self-proving assertion

Parameterising by the setting (`== f"{settings.app_prefix}/pipelines/create"`)
makes the deployed green **self-proving**: it can only pass if the prefix really
resolved to `/app`. Never repair this class by weakening to `.endswith(...)`/`in`
— that trades a real deployed bug for a permanently weaker assertion.

Related: [[running_the_suite_against_dev_without_editing_env_test]] (the local
alternative when you need a DEV run without CI) · [[tms_index_backwrite_surgical_not_full_rebuild]]
