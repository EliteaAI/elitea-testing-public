---
name: Some specs cannot be gated on localhost at all — the publish-wizard family
description: The publish AI gate 400s for the VITE_DEV_TOKEN identity, so a local green proves nothing for ~9 specs; gate them against dev.elitea.ai, and remember .env.test beats shell env
type: feedback
aliases: [publish_validate 400, user_token not found, ai_validation_failed, DEV-only gate, ELITEA_URL ignored, env.test beats shell env, ungateable locally]
tags: [area/merge-gate, area/environment, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The finding

`.agents/testing.md` says the local green run IS the gate (there is no CI on `automation/base`).
For the publish-wizard family that premise is **false**, silently.

On `localhost:5173` the app authenticates as the `VITE_DEV_TOKEN` identity, and the AI gate
answers:

```
POST /api/v2/elitea_core/publish_validate/prompt_lib/{project}/{versionId}
400 {"error":"ai_validation_failed","msg":"AI validation failed: User token not found. Please create user_token"}
```

Same 400 with `ELITEA_API_TOKEN`. Only a real Keycloak **session** gets a 200. A local run
therefore fails with a *different* signature (`Locator.wait_for ... agent-publish-confirm-button`
— the wizard bounces back to Preparation), so **a local red is not evidence and a local green
proves nothing**. ~9 specs affected (`tests/ui/agents/test_agent_publish_unpublish_version.py`,
`test_agent_version_selector_order.py`, and the `tests/ui/skills/` publish family).

Second trap, independent and wider: **`.env.test` beats shell env** (`config.py` orders dotenv
first), so `ELITEA_URL=https://dev.elitea.ai pytest …` **silently runs localhost anyway**. The
env FILE has to be swapped and restored.

## The gate invocation

```bash
cd automation
test -L .env.test && mv .env.test .env.test.symlink.bak
cat ../../.env.test > .env.test
printf '\nELITEA_URL=https://dev.elitea.ai\nAPP_PREFIX=/app\n' >> .env.test && chmod 600 .env.test
../.venv/bin/python -c "from config import settings; print(settings.app_base_url)"   # https://dev.elitea.ai/app
HEADLESS=true ../.venv/bin/pytest "<node-id>" -v -p no:cacheprovider     # x3, separate invocations
rm -f .env.test && mv .env.test.symlink.bak .env.test        # RESTORE — non-optional
```

Verify the restore (`app_base_url` back to `http://localhost:5173`) before ending the session;
the master `../../.env.test` must never be modified.

**Bonus:** a green DEV gate also empirically corroborates the closure record's promotability row
— the spec drove those testids on the deployed build, which is stronger evidence than the
`origin/main` grep.

Tracked as `question` #2108 (options: provision a `user_token` for the dev identity, or a
`dev_only` marker). Corollary in `.agents/testing.md` § Merge gate.

Related: [[env_scoped_sanctioned_red]] · [[gating_a_fix_on_dev_via_workflow_dispatch]]
