---
name: Backend API investigation discipline
description: API call to platform backend fails or returns wrong data? Isolate, compare CI vs local, determine retriability
type: feedback
---

## When this applies

An API call to the Elitea platform backend (e.g. `/api/v2/elitea_core/...`, toolkit operations, MCP sync) either:
- Returns an error (4xx, 5xx)
- Returns unexpected/wrong data (structure correct but content wrong)
- Times out or hangs

## Investigation procedure

### 1. Isolate the API call

Run it in isolation outside the test — a standalone script, curl, or dedicated debug function. Example:

```python
# test_mcp_sync.py
from automation.api.client import ToolkitAPI

toolkit_api = ToolkitAPI(...)
result = toolkit_api.sync_mcp_tools("https://mcp.deepwiki.com/mcp")
print(f"Tools returned: {len(result)}")
print(f"First tool: {result[0] if result else 'NONE'}")
```

This removes test framework noise and shows the raw API behavior.

### 2. Compare CI vs local execution

If the test fails in CI but passes locally (or vice versa):

- Run the isolated call **locally** → capture request/response
- Check CI logs for the same call → capture request/response  
- Diff them: different request params? different response? timeout on one side?

**Common divergences:**
- CI runner network restrictions (can't reach external endpoints)
- Environment variables differ (`ELITEA_API_BASE`, credentials)
- Backend version differs (CI hits deployed env, local hits dev)
- Timing (CI slower, hits timeouts local doesn't)

### 3. Determine if the error is retriable

Check the error response:
- **503 with `"error": "temporarily_unavailable"`** → **YES, retriable** (pool/queue saturation, backend overloaded)
- **502/504 gateway timeout** → **YES, retriable** (transient infra issue)
- **429 rate limit** → **YES, retriable with backoff**
- **400/401/403/404** → **NO, not retriable** (request is wrong or forbidden)
- **500 with specific error message** → **MAYBE** (read the message; some are transient, some are bugs)

**If retriable:** Implement retry logic (exponential backoff, 3 attempts, respect `retry_after` header).  
**If not retriable:** This is either a product bug (file it) or a test bug (fix the request).

### 4. Identify backend vs runner issue

| Symptom | Likely cause |
|---|---|
| Fails in CI, passes locally with identical requests | CI runner environment (network, firewall, DNS) |
| Fails both places with same error | Backend issue (bug, config, missing data) |
| Passes in CI, fails locally | Local environment (wrong backend URL, stale dev DB, missing credentials) |
| Intermittent (flaky both places) | Backend load issue (pool saturation, race condition) |

## Should we rely on retry?

**YES, if:**
- Backend explicitly signals retriability (`retry_after`, 503 temporarily_unavailable)
- Error is documented as transient (pool saturation, rate limit)
- Retry logic is scoped to that specific error (not a blanket retry)

**NO, if:**
- Error indicates a permanent problem (401, 404, 400 bad request)
- Backend doesn't signal retriability
- We'd be masking a product bug

## Example: MCP pool saturation

**Symptom:** `toolkit_api.sync_mcp_tools()` returns 503  
**Isolated call:** Returns `{"error": "temporarily_unavailable", "retry_after": 5}`  
**CI vs local:** Fails on both (pool is globally saturated, not env-specific)  
**Retriable?** YES — backend explicitly says "retry after 5s"  
**Action:** Implement exponential backoff in fixture (3 retries, 5/10/20s delays)

## Evidence

MCP investigation — pool saturation was misdiagnosed as "endpoint down" until isolated investigation revealed it's a transient, retriable worker-pool issue.
