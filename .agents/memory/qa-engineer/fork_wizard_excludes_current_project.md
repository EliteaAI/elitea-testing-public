---
name: Fork wizard excludes the currently-selected project from its target list
description: A fork test whose SOURCE and TARGET are the same project can never pass — the product filters the current project out of the target dropdown.
type: reference
aliases: [fork target project, select-option missing, useForkProjectIds, fork dropdown]
tags: [area/pipelines, area/agents, type/product-behaviour]
created: 2026-08-26
updated: 2026-08-26
---

## The rule (product source, verified 2026-08-26)

`EliteaUI/src/[fsd]/entities/import-wizard/lib/hooks/useForkProjectIds.hooks.js`
(since `7515f444`, 2026-04-08):

```js
const excludedProjectIds = isForking ? [PUBLIC_PROJECT_ID, selectedProjectId] : [];
```

→ `IWModalContent.jsx:105` `filterIds` → `ProjectSelect.jsx:107`.

**When forking, the target dropdown = the user's project memberships MINUS the public
project MINUS the currently-selected (source) project.** No permission/role filter beyond
that. The *sidebar* project switcher has no such exclusion — it shows all memberships,
including the current one. Confirmed live both directions on localhost:5173.

So `[data-testid="select-option-<X>"]` missing in a Fork wizard means one of exactly two
things: X is the source project, or the acting user is not a member of X.

## Project ids are per-user, not shared

`ELITEA_PROJECT_ID` (locally `399` = `project_user_659`, labelled **"Private"** because
`ProjectSelect.jsx` renames `user.personal_project_id` to "Private") is the acting user's
OWN project — in CI it is `TEST_USER_PROJECT_<n>` per matrix cell
(`.github/workflows/test-ui-custom.yml:506`), a DIFFERENT id per user. Any test hardcoding
`399` is pinned to one operator's private project and cannot pass in CI.

Read memberships the same way the UI does:
`GET {ELITEA_API_BASE}/projects/project/default/{public_project_id}?check_public_role=true`.

Related: [[MEMORY]] · worked case ELITEA-2051 / issue #1800.
