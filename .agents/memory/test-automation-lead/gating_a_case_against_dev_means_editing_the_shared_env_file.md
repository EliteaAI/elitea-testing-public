---
name: Gating a case against DEV means editing the shared env file
description: How to actually target dev.elitea.ai for a gate, and the two traps around it
type: reference
aliases: [dev gate, gate on dev.elitea.ai, ELITEA_URL swap, APP_PREFIX /app, run tests against DEV]
tags: [area/merge-gate, area/environment]
created: 2026-09-10
updated: 2026-09-10
---

## The procedure

`.env.test` **beats shell env** (`config.py` orders dotenv first), so
`ELITEA_URL=… pytest` silently runs **localhost** and you gate the wrong
environment while believing otherwise. `automation/.env.test` is a symlink to
the master `<workspace>/.env.test`, shared by all four clones — so targeting DEV
means mutating that master file:

```bash
REAL=$(readlink -f automation/.env.test)
cp "$REAL" /tmp/env.test.lead-backup            # back up FIRST
sed -i '' -e 's|^ELITEA_URL=.*|ELITEA_URL=https://dev.elitea.ai|' \
          -e 's|^APP_PREFIX=.*|APP_PREFIX=/app|' "$REAL"
# ... run the gate ...
cp /tmp/env.test.lead-backup "$REAL"            # RESTORE, then diff -q to prove it
```

`ELITEA_API_BASE` already points at the DEV backend — leave it alone.
On DEV, auth is real Keycloak (`input[name="username"]`), so runs are slower
than localhost and `auth_state` does NOT short-circuit login.

**Restore before you stop, and prove it byte-identical.** Leaving the master
swapped breaks every later local run in every clone, silently.

## Expect #2124 `Page.goto` noise on a DEV gate

Measured 2026-09-10 (card #2139): all 3 gate invocations carried a `Page.goto`
timeout absorbed by `--reruns=2`, on plain list-page navigation — wider than
#2124's stated reproduction recipe. It is a **precondition** failure, never a
member of a sanctioned-RED set: re-run, never accept 2-of-3. Evidence lives only
in `reports/allure-results/*-result.json` (status `broken`) and
`reports/reruns.json` — the reruns make junit record PASS.

**Free matched control:** if an untouched sibling test in the same invocation
carries the same flake, that clears your diff without a separate control run.

## `build_index` rebuilds the wrong-looking file

The `onetest-tms` MCP `build_index` verb writes **`index_automated.json`**
(~824 automated cases) and commits it — it does NOT refresh the repo's larger
`index.json` (~3413 cases), which stays stale repo-wide. After a back-write,
verify your case in `index_automated.json`; don't chase `index.json`.

Related: [[deployed_env_only_failures_need_a_gha_run_not_a_local_gate]] · [[dev_goto_lifecycle_waiter_never_resolves]] · [[a_delivered_card_is_not_verified_until_the_env_ran_it]]
