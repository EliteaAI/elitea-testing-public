---
name: Project-switch waits must key on the NEW project id, not networkidle
description: networkidle returns before a project switch settles; wait on project_info + auth/permissions for the new id
type: feedback
aliases: [project switch race, isPrivateProject guard, ensure_team_project_selected, settings users redirect]
tags: [area/ui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## Symptom

`AdminUsersPage.navigate()` intermittently timed out 10 s on
`user-row.first` — "the table never rendered". **3 of 10 invocations** in one
session (2026-08-29, settings-w09).

## Real cause (screenshot, not inference)

The failure screenshot showed the sidebar still on **"Project: Private" /
"Project ID: 399"** at `/settings/project-general`. The project switch had not
landed, so `Settings.jsx`'s `isPrivateProject` guard redirected
`/settings/users` straight back — a zero-row page. The timeout was a downstream
symptom, three steps from the cause.

**Read the failure screenshot before theorising about a locator timeout.** It
cost one `Read` call and turned "flaky wait" into a named race.

## Fix

`wait_for_network()` (`networkidle`) is a poor completion signal on this app —
the always-open Socket.IO poll means the network is never idle for 500 ms
(the `#1847` mechanism). Wait on the product's own switch signals instead, keyed
by the **new** project id:

- `GET /api/v2/elitea_core/project_info/prompt_lib/{id}/project-info` (what the guard reads)
- `GET /api/v2/auth/permissions/prompt_lib/{id}` (what gates the page's controls)

and **delete** the trailing `wait_for_network()`. Result: flake gone (8/8,
`reruns.json == {}`) and the 8-spec run **~56 s faster** — every navigation had
been paying a networkidle wait it did not need.

## Companion trick

Re-selecting an already-active project fires **no** request, so a response wait
would hang. Detect it testid-only via the checkmark `SingleSelect` renders
INSIDE the selected option: `option.locator('[data-testid="select-option-selected-icon"]').count()`.

The same element is a trap elsewhere: it makes a bare
`[data-testid^="select-option-"]` count read one too high whenever an option is
preselected.

Related: [[mui_required_label_double_asterisk]]
