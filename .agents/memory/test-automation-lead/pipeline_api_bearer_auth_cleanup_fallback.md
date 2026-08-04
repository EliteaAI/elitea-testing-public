---
name: PipelineAPI Bearer-auth fallback for post-close DEV cleanup
description: when an analyst's browser-cookie DELETE fails (CORS/auth-header gap), the orchestrator can clean up leftover DEV test data via PipelineAPI(browser_cookies=[], project_id=...) — empty cookie list triggers Bearer auth from ELITEA_API_TOKEN, works from a plain shell/script
type: feedback
---

## What happened

ELITEA-2034 (issue #471) analyst session created a test pipeline
(`autotest_decision_2034`, id 7452, project 399/Private) during live
exploration and could not delete it before the session ended: `PipelineAPI`
was constructed with `browser_cookies` from the Playwright-MCP browser
context, and an in-page `fetch()` DELETE attempt failed
(`TypeError: Failed to fetch`, consistent with a CORS/auth-header gap on
that browser-driven path). This has recurred across "several other
analyst-session" instances per the finding note — a known, not-yet-fixed
gap in the analyst's cleanup tooling.

## What worked

`automation/api/client.py`'s `PipelineAPI.__init__` only sets cookies if
`browser_cookies` is non-empty; when it's empty **and** `settings.elitea_api_token`
is set (it is, from `.env.test`), it falls back to
`Authorization: Bearer <ELITEA_API_TOKEN>` on the requests session. That
path has no CORS exposure (plain Python `requests`, not a page-context
`fetch()`), so it works even where the browser-driven delete failed:

```python
from api.client import PipelineAPI
api = PipelineAPI(browser_cookies=[], project_id='399')
api.get_pipeline(7452)      # confirm it's the right object first
api.delete_pipeline(7452)
# GET afterward returns 400 (not a clean 404) — don't trust that as
# confirmation; cross-check via list_pipelines() and match on id/name instead
```

## Rule going forward

The orchestrator can run this as a **post-close cleanup step** whenever an
analyst/implementer finding flags an undeleted test artifact and names an
id + project — don't leave it as permanent DEV clutter just because the
in-session browser path failed. Applies to any entity `client.py` exposes a
`delete_*` for (pipelines confirmed; likely agents/toolkits too via the
same pattern — check the class's `__init__` for the same cookie-vs-token
branch before assuming it works).
