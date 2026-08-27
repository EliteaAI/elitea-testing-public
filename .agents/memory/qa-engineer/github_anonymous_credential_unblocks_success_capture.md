---
name: GitHub Anonymous credential is an honest source of a SUCCESSFUL GitHub toolkit call
description: Anonymous-auth GitHub credential + public repo produces a real list_branches_in_repo success, no PAT needed (routes around #1673)
type: reference
aliases: [anonymous github credential, github 1673 workaround, github toolkit without PAT, GitHubAuthenticationTypes.None]
tags: [area/toolkits, area/credentials, type/workaround]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

`GIT_HUB_TOKEN` in the master `.env.test` is expired (#1673), which blocks any case
needing a **successful** GitHub toolkit call. **Anonymous auth is a full workaround
for read-only tools on public repos**, and it is honest — the tool really runs
against the real GitHub API.

Recipe (verified live 2026-08-27, 3 runs, byte-identical output):

```python
CredentialAPI(browser_cookies=[]).create_credential({
    "type": "github", "elitea_title": f"github_anon_{ts}", "label": "...",
    "data": {"base_url": "https://api.github.com"},     # NO access_token key at all
    "shared": False,
})
# check_connection -> 200 {"success": true}
```

Then a normal `github_toolkit_settings()`-shaped toolkit pointed at a **public**
repo — `settings.github_repo` is already `EliteaAI/elitea-testing-public`, which is
public. `list_branches_in_repo` executes and returns a real 200 payload.

This is exactly what the UI's `GitHubAuthenticationTypes.None` / `label: 'Anonymous'`
option produces (`EliteaUI/src/common/constants.js:753-756`, `ToolSection.jsx:46-53`).

## The boundary

It is NOT a drop-in swap for `TOOLKIT_CONFIGS["github"]`. Swapping the parameterized
test to an anonymous credential changes **what the case verifies** (a credentialed
toolkit becomes an uncredentialed one) — a human scope decision per
`.agents/role-overrides.md` § declared-improvisation ceiling, not an IC's call. Use it
for **capture and probing**; route the fixture change.

Related: [[toolkit_tool_failure_is_only_visible_in_tool_output]]
