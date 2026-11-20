---
name: Sandbox has no .env.test — workflow gate goes red with 404s unless APP_PREFIX=/app inline
description: ELITEA-4759 (2026-11-20): batch-build gate red at Step 1 "Page Not Found"; cause was missing APP_PREFIX, not the test. Also haiku 403s for merge/report slots.
type: feedback
---
When `automation/.env.test` is absent (factory sandbox), the workflow gate's run 404s on every `/mcps|/toolkits` page. Check for "Page Not Found" in the gate signature before classifying red; re-run the lead's own 3× with `APP_PREFIX=/app HEADLESS=true` inline. Env already exports ELITEA_URL/creds.
Also: this team's key 403s on haiku — pass `mergeModel/reporterModel/triageModel: "sonnet"` to batch-build up front. Resume with changed args re-ran everything (cache miss), so set them on the first call.
