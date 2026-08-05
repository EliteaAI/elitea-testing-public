---
name: Team project id env key collision (471 vs 400)
description: Two distinct non-private team projects exist in test data — grep for existing TEAM_PROJECT_ID usage before adding a new env key for "the team project"
type: project
---

The env already carries `ELITEA_TEAM_PROJECT_ID=471` ("Elitea Testing Team") in
`.env.test`, but **no code reads it via `config.py`** — several chat/toolkit
tests instead hardcode a *local* module constant `TEAM_PROJECT_ID = "471"`
(`test_team_users_mention_and_remove_participants.py`,
`test_invite_users_add_cancel_close.py`, `test_open_conversation_today_section.py`,
`test_credential_create_private_from_toolkit_dropdown.py`).

Settings -> Users (ELITEA-2292) needed a *different* team project — id 400
("UI Testing") — confirmed live to carry existing users. The first pass
hardcoded `USERS_TEAM_PROJECT_ID = "400"` as a module constant in
`admin_users_page.py`, duplicating the "team project" concept with a
conflicting value against the already-present (if unused) `ELITEA_TEAM_PROJECT_ID`
key. Reviewer caught it twice (round 1 unaddressed, round 2 fixed).

**Fix pattern:** added `settings.users_team_project_id` to `config.py`, sourced
from a **deliberately distinct** env key `USERS_TEAM_PROJECT_ID=400` in
`.env.test` — never repurpose/alias `ELITEA_TEAM_PROJECT_ID` (471 is a
different, already-relied-on project). `select-option-{399,400,471}` are all
live, distinct project ids on this env (see `agent_detail_page.py:391`
comment) — before adding a "team project id" env var/constant for a new
feature, `grep -rn "TEAM_PROJECT_ID" automation/` first to see which of the
existing project ids (if any) is actually the one you need, and if none
match, pick a feature-scoped key name (not a generic `TEAM_PROJECT_ID`) so it
can't collide the same way again.
