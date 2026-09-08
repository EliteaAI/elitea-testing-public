---
name: Localhost cannot run any publish flow — publish_validate 400 "create user_token"
description: The dev-token identity has no user_token, so every Publish wizard test dies at Continue on localhost; gate on DEV
type: project
aliases: [ai_validation_failed, user token not found, publish_validate 400, agent-publish-confirm-button timeout, publish wizard stuck on Preparation]
tags: [area/environment, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## Symptom

`Locator.wait_for: Timeout 60000ms exceeded … waiting for
get_by_test_id("agent-publish-confirm-button")` inside
`AgentDetailPage.click_publish_continue()`. The failure screenshot shows the wizard still
on **Preparation** with Continue enabled — it never advanced to Validation.

## Cause (probed live 2026-09-09, localhost)

```
POST /api/v2/elitea_core/publish_validate/prompt_lib/399/{versionId}  ->  400
{"error": "ai_validation_failed",
 "msg": "AI validation failed: User token not found. Please create user_token"}
```

The localhost `VITE_DEV_TOKEN` identity has no `user_token`, so the AI content-quality
gate 400s. `PublishWizardModal.jsx` renders `agent-publish-confirm-button` only under
`step === VALIDATION && validationResult`, so on a 400 the button never exists and the
wait burns its full timeout.

**This is not drift and not a code defect** — it reproduces identically on pristine
`origin/main`. The nightly's Keycloak `TEST_USER` on DEV *does* have the token, which is
why the same specs get past this step there.

## What to do

Gate any publish-flow spec against **dev.elitea.ai** via the out-of-repo `-p devenv`
harness ([[dev_env_run_harness_and_goto_flake]]) instead of localhost. Never edit
`.env.test` (shared symlink).

Affected on sight: `test_agent_version_selector_order.py` (its `v2-published`
precondition), `test_agent_publish_unpublish_version.py`, and the skill/pipeline publish
wizards.

Side observation, unfiled: the wizard surfaces **no error to the user** on that 400 — it
just sits on Preparation with Continue still enabled.
