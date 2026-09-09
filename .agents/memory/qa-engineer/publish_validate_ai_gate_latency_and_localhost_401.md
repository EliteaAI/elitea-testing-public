---
name: publish_validate AI gate — DEV latency and the localhost user_token wall
description: publish_validate is a 15-47s LLM gate; localhost 400s on it, so publish-wizard specs cannot be gated locally
type: project
aliases: [publish_validate, publish_skill_validate, publish wizard timeout, VALIDATE_TIMEOUT, user_token not found, ai_validation_failed]
tags: [area/agents, area/skills, type/flake]
created: 2026-09-09
updated: 2026-09-09
---

## The endpoint is slow, by design

`POST /api/v2/elitea_core/publish_validate/prompt_lib/{project}/{versionId}` (agents) and
`POST .../publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}` (skills) are
**LLM-backed content-quality gates**. Measured live on DEV 2026-09-09, real `TEST_USER`
Keycloak session, trivial seeded agent:

- agents, n=24 (18 direct POST + 6 end-to-end through `AgentDetailPage`):
  min 15.46 s · median 26.82 s · p95 33.76 s · max 36.88 s · **6/24 over 30 s** · 24/24 HTTP 200.
- skills, n=6: min 20.52 s · median 27.19 s · **max 46.23 s**.

It **never hangs** — every sample resolved. So a `publish_validate` timeout is a wait-budget
bug, not a product hang. Any budget at or below ~60 s is thin; 90 s is the shape that matches
the measured tail (and `PIPELINE_RUN_START_TIMEOUT = 150_000` is the in-repo precedent for
budgeting a nondeterministic backend generously).

Once the response lands, the Validation step's confirm button renders in **0.013–0.023 s**
(6/6) — never let one constant serve both waits.

## Localhost cannot exercise it at all

The localhost app authenticates as `Authorization: Bearer <VITE_DEV_TOKEN>`, and that identity
has no platform `user_token`, so every call returns:

```
400 {"error": "ai_validation_failed",
     "msg": "AI validation failed: User token not found. Please create user_token"}
```

Same 400 with `ELITEA_API_TOKEN`. Only the Keycloak **session** identity gets a 200.

Consequences:

- Any publish-wizard spec run against `localhost:5173` fails with a *confirm-button locator
  timeout* (the wizard bounces back to Preparation), **not** the CI signature. A local green
  proves nothing and a local red is not evidence. Gate these specs against
  `https://dev.elitea.ai` (`APP_PREFIX=/app`).
- `usePublishVersion.hooks.js`'s `callWithAIRetry` (`MAX_AI_RETRIES = 2`) fires **three**
  sequential POSTs on ONE Continue click when the answer is `400 ai_validation_failed`.
  `page.expect_response` resolves on the FIRST, so retries never extend that wait.

Origin: board #2082 / ELITEA-1892 repair triage, 2026-09-09.

Related: [[project_briefing]]
