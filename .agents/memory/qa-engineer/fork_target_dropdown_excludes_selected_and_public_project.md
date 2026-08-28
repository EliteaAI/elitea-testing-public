---
name: Fork target dropdown excludes the selected + public project
description: select-option-<id> for a fork target renders only for the user's OTHER memberships; and the lowest-id fallback can 403 on create.
type: reference
aliases: [useForkProjectIds, select-option-399 timeout, fork source project resolution, ELITEA-2051]
tags: [area/pipelines, area/agents]
created: 2026-08-28
updated: 2026-08-28
---

## Product rule (authoritative, from src)

`EliteaUI/src/[fsd]/entities/import-wizard/lib/hooks/useForkProjectIds.hooks.js`:

```js
const excludedProjectIds = useMemo(
  () => (isForking ? [PUBLIC_PROJECT_ID, selectedProjectId] : []), ...)
```

Options render as `data-testid={option.testId ?? `select-option-${option.value}`}`
(`src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx` + siblings), value = project id.

So `select-option-<N>` is visible **only if** N is one of the acting user's
project memberships AND N is neither the currently-selected project nor the
public project. A `select-option-<N>` timeout in a Fork wizard is therefore a
**test-data** signal (wrong project pair), not a locator/drift signal.

## Residual gap in the ELITEA-2051 source resolver (verified 2026-08-28, DEV)

`_resolve_source_project_id()` prefers `USERS_TEAM_PROJECT_ID` (400), else
falls back to `sorted(candidates)[0]` — the **lowest membership id**. On DEV
as the local test user that fallback picks **project 25 ("Elitea Development")**,
where the user is a listed member but cannot create:

```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url:
https://dev.elitea.ai/api/v2/elitea_core/applications/prompt_lib/25
```

Membership != write capability. The resolver has no create-capability check,
so on any runner that is not a member of 400 it can pick an unusable source
and die with a raw 403 in Step 1. Reproduced by overriding
`settings.elitea_project_id = 400` through an out-of-repo `-p` plugin.
