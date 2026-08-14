---
name: Users page admin rights scoped to project 400 only
description: testbot@elitea.ai (the acting TEST_USER) is admin on Users only in project 400 ("UI Testing") — every other project (471/406/25) shows viewer/absent, no batch-edit/delete UI renders at all there.
type: feedback
---

## What happened (ELITEA-2304 analysis, 2026-08-05)

Exploring the batch-edit-roles case, I checked every project reachable from
the sidebar selector for the Settings → Users page's write-capable UI
(header batch-Edit/Delete buttons, per-row Edit/Delete icons):

| Project | id | Test Bot's role there | Write UI renders? |
|---|---|---|---|
| UI Testing | 400 | `admin` | YES — full header + per-row Edit/Delete |
| Elitea Testing Team | 471 | `viewer` | NO — header shows only search, no Edit/Delete/Invite; rows have no Actions cell at all |
| Bugs & Features | 406 | not on page 1 of 29 users | NO |
| Elitea Development | 25 | `viewer` | NO |

This is **permission-gated at render time**, not merely disabled:
`checkPermission(PERMISSIONS.users.edit)` in `Users.jsx` controls whether
`EditUsersButton`/`DeleteUserButton` even mount, not just their `disabled`
prop. So project 400 is the ONLY project where any Users-page write-flow
case (batch-edit-roles, single edit, delete, invite) can be automated
against this test account at all.

## Consequence for future cases on this surface

Project 400 has exactly 2 real users (`Levon Dadayan`, `Test Bot` — the
acting account itself), which is too few for any case needing 3+ users
(e.g. "select 2, verify a 3rd unselected one is unaffected"). **Never
select/mutate Test Bot's own row** — it's the shared automation account;
changing its own role there would strand every later test in the project.

**Resolution pattern (used in ELITEA-2304, works well):** seed disposable
users via the existing "Invite users" dialog. A freshly-invited row appears
INSTANTLY with full Edit/Delete row actions and an editable role — no
email acceptance or login needed for it to be a normal mutable row. Batch
operations, delete-cleanup, and role assertions all work on it exactly like
a real user. Clean up via each seeded row's own Delete icon → the shared
`Modal.DeleteEntityModal` confirm (testid `delete-confirm-button`) in a
`finally`/fixture teardown.

## If this recurs

Any NEW Users-page write-flow case: check project 400's live user count
first before assuming enough safe test data exists; default to seeding 2+
disposable invited users rather than trying to find/reuse real ones in
project 400, and NEVER include Test Bot's own row in a selection that will
be mutated.
