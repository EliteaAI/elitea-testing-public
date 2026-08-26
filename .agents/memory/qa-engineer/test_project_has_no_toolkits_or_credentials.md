---
name: Test project has no toolkits or credentials
description: The localhost test user's personal project is empty of toolkits/credentials — index-triggered flows are unautomatable there
type: project
aliases: [no toolkits, no credentials, pgvector missing, index run blocked]
tags: [area/toolkits, status/blocker]
created: 2026-08-26
updated: 2026-08-26
---

## Confirmed 2026-08-26 (localhost:5173, DEV backend, project 399 "Private")

- `/toolkits/all` redirects to `/toolkits/create` — **zero toolkits**.
- `/credentials/all` redirects to `/credentials/create-credential` — **zero credentials**.
- The `artifact` toolkit form's vector-store select
  (`toolkit-credential-select-pgvector-combobox`) offers only `"None"`.
- No `PGVECTOR*` key in `automation/config.py` or `.env.test`.

⇒ Any case whose trigger is an **index run** (`index_data_changed` notification) is
`blocked`: no indexable toolkit can be created, and fabricating the notification would be
a terminal substitution. First hit: ELITEA-2265.

Note the contrast: `.env.test` DOES carry `GIT_HUB_TOKEN` / Jira keys as toolkit *test
data*, so a GitHub toolkit can be created — but indexing still needs the vector store.

Related: [[notification_read_unread_visual_signal]]
