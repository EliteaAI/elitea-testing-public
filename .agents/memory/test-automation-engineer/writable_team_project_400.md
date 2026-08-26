---
name: Writable team project is 400 (UI Testing), not 471
description: Project-scoped write flows must target settings.users_team_project_id (400) — 471/406/25 all 403 on credential create
type: project
aliases: [users_team_project_id, project 400, UI Testing project, team project writes, 403 configurations.configuration.create]
tags: [area/credentials, area/toolkits, type/environment]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

"Test Bot" (`author_id 659`, `personal_project_id 399`) can CREATE credentials in
exactly one team project: **400 "UI Testing"**. Live-probed 2026-08-22 with a real
`POST /configurations/configurations/{p}`:

| project | result |
|---|---|
| 471 Elitea Testing Team | 403 `access_denied` (`configurations.configuration.create`) |
| 406 Bugs & Features | 403 |
| 25 Elitea Development | 403 |
| **400 UI Testing** | **200** |

It is already wired: `settings.users_team_project_id` (`config.py:207`,
`USERS_TEAM_PROJECT_ID=400` in `.env.test`). Never hardcode it.

## Why it matters

Any flow whose observable is *project-scoped* (a project credential, a project
secret, anything `createSelectHandler` routes to `selectedProjectId`) is
**unautomatable in 471** — the create 403s — and **invisible in 399**, because the
"New project …" option only renders when `selectedProjectId != personal_project_id`.
400 is the only project where both hold.

## The catch

Project 400 has **zero toolkits of any type** and one (s3) credential. A case
needing a toolkit there seeds it (transit): create a Github credential first
(`data: {"base_url": "https://api.github.com"}`, Anonymous — no token), then
`POST /elitea_core/tools/prompt_lib/400` with
`settings.github_configuration = {elitea_title, private: false}`.

Related: [[.agents/knowledge]] · `test-specs/toolkits-credentials/_surface.md`
(the digest's project-topology table said "400 READ only" — corrected 2026-08-22).
