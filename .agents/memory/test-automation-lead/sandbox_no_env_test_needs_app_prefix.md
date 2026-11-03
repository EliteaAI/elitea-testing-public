---
name: sandbox without .env.test needs APP_PREFIX=/app
description: In the factory sandbox automation/.env.test is absent; APP_PREFIX defaults to "" so every DEV navigation 404s — prefix pytest with APP_PREFIX=/app. Also gate-runs.jsonl needs a "verdict" key.
type: feedback
---
- Local pytest runs fail with 404 / `agent-information-section` timeouts unless `APP_PREFIX=/app` is set (ELITEA_URL, creds come from shell env). Tell implementers in every dispatch.
- `work-scope.mjs close` reads `verdict` from the last line of `gate-runs.jsonl` (`{"verdict":"green",...}`); `{"run":1,"result":"pass"}` lines cause a GATE DRIFT warning.
- A page-object-only landing touches no `tests/ui/**`, so `build-test-index` does not fire; TMS case already correct → no back-write needed (#2865, adjust-2865, f534d941).
- #2866 (adjust-2866): publish_validate 422 in CI = AI content gate flaking on test-looking seed text (description mentioning "disposable"/ticket id). Probe the endpoint with body `{"version_name": ...}` (not `name`) on N fresh agents to measure rate; fix = realistic seed content, never accept 422. Reviewer-noted residual risk: gate is non-deterministic, recurrence → product ticket, not test change.
