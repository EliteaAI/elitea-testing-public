---
name: The -p devenv DEV gate retargets the UI only — third-party test-data tokens still come from the local .env.test
description: A DEV gate can be red for a reason CI never sees (expired local GIT_HUB_TOKEN) — classify tool-payload 401s as workspace test data, cite the healthy CI neighbour, merge on the counterfactual
type: feedback
aliases: [devenv gate 401, GIT_HUB_TOKEN expired gate, tool payload Bad credentials, local test data on DEV gate, #1941 gate residual]
tags: [area/merge-gate, area/dev-env, area/test-data, type/lesson]
created: 2026-09-18
updated: 2026-09-18
---

## What happened (#2358, ELITEA-1141)

The `-p devenv` plugin moves `settings.elitea_url`/`app_prefix` to `dev.elitea.ai` — nothing else.
`GIT_HUB_TOKEN` / `JIRA_API_KEY` (typed INTO the toolkit credential the test creates) still resolve
from this workspace's `.env.test`. The workspace GitHub token is expired (#1941), so
`test_toolkit_test_settings[github]` went 3/3 red at its LAST step — `✅ list_branches_in_repo` ran,
GitHub answered `401 Bad credentials` inside the payload — while `[jira]` (same code path, live Jira key)
was 3/3 green and CI (repo secret) passes the github neighbour `test_chat_with_toolkit[github]`.

## The reading

- **Where the 401 sits decides the class.** A 401 *inside the tool result text* = the product did its job
  and the third party rejected OUR test data. A 401 on an Elitea endpoint = auth/gateway blip
  (see `dev_auth_blip_403_empty_permissions_then_502_then_login_page`). Different buckets.
- Prove it in two commands, no browser: `GET api.github.com/user` with `settings.git_hub_token` → 401;
  and name the untouched CI neighbour that makes a real call with the same secret and PASSED.
- Then merge on the counterfactual (`merging_is_judged_by_the_counterfactual_not_by_gate_color`) and
  write it into the closure record as a **named residual**, not a sanctioned RED (#2180 rule: a
  data-dependent cause cannot be reproduced locally — say so instead of reading it either way).
  The next DEV Stable run is the first real green evidence for that param; say that too.
- Never substitute the shell `GITHUB_TOKEN` (infra identity) for test data, and never edit `.env.test`
  (`.env*` is a forbidden path) — comment the occurrence on #1941 and move on.

## Cheap pre-check for any github-toolkit gate

Before launching a 3× gate on a spec whose LAST step reads a GitHub tool result, spend one call:
`curl -s -o /dev/null -w '%{http_code}' -H "Authorization: token $(…git_hub_token…)" https://api.github.com/user`
(never print the token). A 401 means the gate can certify everything except that final read — plan
the closure wording up front instead of discovering it after ~3 min of DEV runs.

Related: [[dev_gate_discipline_for_fix_cards]] · [[the_devenv_plugin_is_the_factory_safe_dev_gate]] ·
[[a_fix_card_red_can_be_hidden_on_localhost_until_testids_is_synced]]
