---
name: Gating a fix on DEV via workflow_dispatch instead of local credentials
description: The dev-stable workflow takes a `ref` input, so you can run any branch against DEV in CI — the only DEV gate available to an agent, since local .env.test fails the dev realm
type: reference
aliases: [DEV gate, run branch against DEV, workflow_dispatch ref, dev-stable dispatch, verify on dev.elitea.ai]
tags: [area/ci, type/technique]
created: 2026-08-26
updated: 2026-08-26
---

## Why

`.env.test`'s test user **fails the Keycloak `dev` realm**, so an agent cannot run
against dev.elitea.ai locally (the `-p devenv` retarget harness works — only the
credential is missing; see [[running_the_suite_against_dev_without_editing_env_test]]
and issue #1820). CI holds the working credentials as per-user secrets.

## The technique

`test-ui-dev-stable.yml` exposes a **`ref` input** that selects which code is checked
out, independent of the `--ref` the workflow definition comes from:

```bash
env -u GITHUB_TOKEN gh workflow run test-ui-dev-stable.yml \
  --repo EliteaAI/elitea-testing-public --ref main \
  -f ref=<your-branch> \
  -f custom_suites=pipelines,pipelines_2 \
  -f parallel_jobs=2 \
  -f publish_to_tms=false
```

- `--ref main` = stable workflow definition; `-f ref=<branch>` = the tests to run.
- `custom_suites` is comma-separated **directory names** under `automation/tests/ui/`.
  There is **no `-k` / node-id input** — suite granularity is the finest available
  (proposed in #1820 option 2).
- `-f publish_to_tms=false` keeps a verification run out of the TMS.
- `suite=all -f parallel_jobs=9` reproduces the nightly's user distribution, which is
  what you want when comparing against a specific nightly failure.

## Non-negotiable follow-up

**Never read the conclusion as the result** — download the artifacts and check
`skipped` vs `tests` first. See [[ci_green_can_mean_zero_tests_ran]]; both of the runs
I dispatched on 2026-08-26 reported `success` having run nothing.

Related: [[ci_green_can_mean_zero_tests_ran]]
