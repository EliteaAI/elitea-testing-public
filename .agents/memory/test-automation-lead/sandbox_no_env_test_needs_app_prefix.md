---
name: sandbox without automation/.env.test needs APP_PREFIX=/app
description: Factory sandbox may lack .env.test; every DEV page 404s unless APP_PREFIX=/app is exported for pytest runs
type: feedback
---
When `automation/.env.test` is missing, `settings.app_prefix` defaults to "" and every page is a 404 (all tests red at detail-page load - looks like mass drift but is env). Run with `APP_PREFIX=/app HEADLESS=true pytest ... --reruns 0` (the `-p no:rerunfailures` flag breaks addopts). Seen on #2834 (ELITEA-0858). Also: gate-runs.jsonl lines need a `verdict` key or work-scope close reports GATE DRIFT.
