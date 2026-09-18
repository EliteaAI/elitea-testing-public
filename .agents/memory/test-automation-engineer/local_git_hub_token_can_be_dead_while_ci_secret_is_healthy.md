---
name: Local GIT_HUB_TOKEN can be dead while the CI secret is healthy
description: A GitHub-toolkit tool returning `401 Bad credentials` locally is test-data rot in `.env.test`, not a flow defect — prove it with the untouched chat[github] sibling + CI's PASSED line before touching anything
type: project
aliases: [Bad credentials 401 github toolkit, GIT_HUB_TOKEN expired, list_branches_in_repo 401]
tags: [area/toolkits, type/env]
created: 2026-09-18
updated: 2026-09-18
---

## Symptom

`test_toolkit_test_settings[github]` / `test_chat_with_toolkit[github]` reach the tool run, the
Results card shows `✅ list_branches_in_repo (0.2s)` and the payload is
`Failed to list branches: 401 {"message": "Bad credentials", …}`. The UI flow is fine — the
toolkit's stored token is what GitHub rejected.

## How to classify it in two commands (2026-09-18, #2358)

1. `curl -s -o /dev/null -w '%{http_code}' -H "Authorization: token $TOK" https://api.github.com/user`
   with `TOK` read via `config.settings.git_hub_token` — **401 = the local `.env.test` token is dead.**
   Never print the token.
2. `gh run view <latest DEV Stable run> --log | grep 'test_chat_with_toolkit\[github\]'` — CI PASSED
   means the repo secret is healthy, so the red is local-only and out of scope for a spec repair.

Matched control for free: `TestChatWithToolkit[github]` is untouched by any Test-Settings diff
and asserts the tool's real success frame (#1817); if it fails locally with the same 401 the
diff is exonerated.

## Do not

- Do **not** substitute the shell `GITHUB_TOKEN` — that is the github-MCP infra identity
  (`.agents/profile.md` § Roles), not test data. Renewing `GIT_HUB_TOKEN` in the master
  `.env.test` is a human's job; report it.
- Do not weaken `test_tool_result_content` to make the param green.

Related: [[toolkit_detail_indexes_panel_and_test_route]]
