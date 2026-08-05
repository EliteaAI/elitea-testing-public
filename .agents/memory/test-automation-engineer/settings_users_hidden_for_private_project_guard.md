---
name: Settings -> Users hidden/redirected for the private project
description: A bare navigate("/settings/users") against the env's default ELITEA_PROJECT_ID silently redirects to /settings/project-general after ~2-3s — that project is the test user's PRIVATE project, and Settings.jsx hides Users for it.
type: feedback
---

## What happened (ELITEA-2292)

`Settings.jsx` computes `isPrivateProject = projectId == user.personal_project_id`
and `showUsersSection = !isPrivateProject`, then has a guard `useEffect` that
fires once project/user data resolves (client-side, ~2-3s after the route
first renders): if `tab === 'users' && !showUsersSection`, it calls
`handleSettingsItemClick(DEFAULT_TAB)` → client-side navigate to
`/settings/project-general`. The URL briefly shows `/settings/users`, table
markup never mounts, then the URL flips.

`.env.test`'s `ELITEA_PROJECT_ID` (399 as of 2026-08-05) IS this test user's
PRIVATE project — confirmed by triggering the redirect and reading
`user.personal_project_id` indirectly via the guard firing. A raw
`AdminUsersPage.navigate()` → `super().navigate("/settings/users")` always
loses this race: `page.expect_response()` waiting on the users/roles-list
GETs times out after 15s because those requests never fire (the component
never mounts far enough to call the query hooks).

Symptom in a fresh test: `playwright._impl._errors.TimeoutError: Timeout
15000ms exceeded while waiting for event "response"` — looks like a
selector/predicate bug, is actually a wrong-project precondition.

## The fix — switch to a TEAM project before navigating

Project selection persists in localStorage across a HARD navigation
(`page.goto`), but NOT across the SPA's own internal redirect once you're
already mid-navigation to `/settings/users` — so the switch must happen
BEFORE that route is requested, not after. Two-hop pattern:

```python
def navigate(self):
    super().navigate("/settings/project-general")   # always reachable, no guard
    self.ensure_team_project_selected()               # click sidebar switcher -> select-option-{id}
    with self.page.expect_response(...):
        super().navigate("/settings/users")            # guard's isPrivateProject already false
```

`project-selector-trigger-combobox` + `select-option-{id}` are pre-existing
testids (same family `ChatPage.switch_project` / `TEAM_PROJECT_ID` already
use for a different reason — team collaboration features). ELITEA-2292 used
project `400` ("UI Testing") — the AFS's own Preconditions/Test Data section
had already named it (the analyst was on it during exploration, via the
sidebar badge), just hadn't flagged the SWITCH as a required navigation
action for automation.

## Where else this could bite

Any Settings sub-page test that assumes the env's `ELITEA_PROJECT_ID` is a
team project should double-check — `Settings.jsx` has the same
`showUsersSection`-style pattern for `project-context` (hidden for the
PUBLIC project, inverse condition) and `prompts`/`environment` (public-only).
If a case's Concrete Handles table cites a specific project id that differs
from `.env.test`'s `ELITEA_PROJECT_ID`, that's a signal to check for exactly
this class of guard before assuming it's just stale AFS provenance.
