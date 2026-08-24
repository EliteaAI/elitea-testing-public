# Admin Suite Auth Failure - Reproduction Guide
**Issue:** CI Run #32736976833 - All 7 admin tests skipped due to authentication failure  
**Date:** 2026-08-24  
**Status:** Investigation Required

---

## TL;DR - Quick Diagnosis

**Symptom:** All admin tests skipped with `Login failed: 200 https://auth.elitea.ai/realms/dev/login-actions/authenticate`

**Root Cause:** API-based login succeeded (HTTP 200) but stayed on Keycloak auth page instead of redirecting back to Elitea app.

**Why:** Likely one of:
1. Session cookie not being set properly by Keycloak
2. Redirect chain broken between Keycloak → forward-auth → Elitea
3. CI environment missing required cookie domain configuration
4. Keycloak session timeout during multi-step auth flow

---

## The Auth Flow (What Should Happen)

### Normal Flow (6 Steps)

```
1. GET https://dev.elitea.ai
   → Redirects to /forward-auth/ (Traefik middleware)

2. POST forward-auth auto-submit form
   → Redirects to Keycloak login page

3. POST credentials to Keycloak
   → Keycloak validates and sets session cookie

4. Keycloak redirects back to /forward-auth/auth_oidc/login_callback
   → Forward-auth validates token

5. Forward-auth redirects to https://dev.elitea.ai
   → Sets elitea-staging_auth_session cookie

6. Final GET https://dev.elitea.ai
   → User is authenticated ✅
```

### What Happened in CI (Failure at Step 4)

```
1-3. ✅ Steps 1-3 succeeded (credentials accepted)

4. ❌ Stayed on: https://auth.elitea.ai/realms/dev/login-actions/authenticate
   - HTTP 200 (success status)
   - But URL still contains "login-actions/authenticate"
   - Should have redirected to /forward-auth/auth_oidc/login_callback

5. ✅ Code correctly detected failure:
   if "auth" in resp.url.lower() or "login" in resp.url.lower():
       raise RuntimeError(f"Login failed: {resp.status_code} {resp.url}")

6. ⏭️ pytest.skip() called → All tests skipped
```

---

## Why This Happens

### Theory 1: Cookie Domain Mismatch (Most Likely)
**Keycloak cookie:** `domain=.elitea.ai` (wildcard subdomain)  
**Elitea app cookie:** `domain=dev.elitea.ai` (specific subdomain)  
**CI requests:** Using `requests.Session()` which may not handle cross-subdomain cookies properly

**Evidence:**
- CI log shows: `"Missing elitea-staging_auth_session cookie"` warning
- Status 200 means Keycloak accepted credentials
- But redirect didn't complete → cookie not propagated

### Theory 2: Session Timeout During Setup
**Timing:**
- Auth fixture runs at session scope (once at start)
- CI has ~3-5 second delay between fixture setup and first test
- Keycloak dev realm may have very short session timeout
- By the time test runs, session already expired

**Evidence:**
- Chat suite uses same auth fixture and passed
- Admin suite ran ~1 second after chat started
- But admin session setup logged separately → new auth attempt

### Theory 3: Redirect Chain Broken in CI
**CI network environment differences:**
- Different DNS resolution
- Different SSL cert validation
- HTTP redirect handling differences between `requests` library and real browser
- Traefik forward-auth may behave differently with API requests vs browser

---

## Manual Reproduction Steps

### Option 1: Reproduce the Exact CI Failure (Recommended)

**Environment:** Any machine with Python 3.11+ and the test repo

**Steps:**

1. **Set up environment variables:**
   ```bash
   cd elitea-testing-public/automation
   
   # Ensure .env.test has:
   # ELITEA_URL=https://dev.elitea.ai
   # ELITEA_API_BASE=https://dev.elitea.ai/api/v2
   # TEST_USER_EMAIL=<your-test-user>
   # TEST_USER_PASSWORD=<password>
   # ELITEA_PROJECT_ID=<project-id>
   ```

2. **Test the API auth module directly:**
   ```bash
   # This will run the same auth flow the fixture uses
   ../.venv/bin/python api_auth.py
   ```

   **Expected output if working:**
   ```
   [OK] Login successful! Got 5 cookies:
     - elitea-staging_auth_session
     - elitea-staging_sid
     - KEYCLOAK_SESSION
     - KEYCLOAK_IDENTITY
     - AUTH_SESSION_ID
   ```

   **Expected output if failing (CI scenario):**
   ```
   ERROR: Login failed - still on auth page: https://auth.elitea.ai/realms/dev/login-actions/authenticate?session_code=...
   RuntimeError: Login failed: 200 https://auth.elitea.ai/...
   ```

3. **If step 2 succeeds, test with pytest:**
   ```bash
   # Run one admin test
   HEADLESS=true ../.venv/bin/pytest tests/ui/admin/test_analytics_default_load.py -v
   ```

   **If auth fixture fails:**
   - You'll see: `SKIPPED - Authentication failed`
   - This reproduces the exact CI issue

4. **Enable debug logging to see the full flow:**
   ```bash
   # Edit api_auth.py temporarily, add at top:
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Run again
   ../.venv/bin/python api_auth.py
   ```

   **Look for:**
   - Which step fails (1-6 in the flow above)
   - Final URL after POST credentials
   - Cookie names and domains
   - Any 302/303 redirects not being followed

### Option 2: Reproduce with Curl (Lower Level)

**Test each auth step manually:**

```bash
# Step 1: Initial request (should redirect to forward-auth)
curl -v -L -c cookies.txt 'https://dev.elitea.ai' 2>&1 | grep -E 'Location:|Set-Cookie:'

# Step 2: You'll see redirect to forward-auth, then Keycloak
# Extract the login form action URL from the HTML

# Step 3: POST credentials (replace <ACTION_URL> with form action from step 2)
curl -v -L -b cookies.txt -c cookies.txt \
  -d "username=${TEST_USER_EMAIL}" \
  -d "password=${TEST_USER_PASSWORD}" \
  -d "credentialId=" \
  '<ACTION_URL>' \
  2>&1 | grep -E 'Location:|Set-Cookie:|<title>'

# Check final URL
# ✅ Success: Should end at https://dev.elitea.ai (no /auth/ or /login in URL)
# ❌ Failure: Stuck at https://auth.elitea.ai/realms/dev/login-actions/...

# Step 4: Check cookies
cat cookies.txt | grep elitea-staging_auth_session
# ✅ Success: Cookie present
# ❌ Failure: Cookie missing → auth didn't complete
```

### Option 3: Reproduce in CI Environment (Exact Match)

**Run GitHub Actions workflow manually:**

```bash
# Trigger admin suite only
gh workflow run test-ui-dev.yml \
  --repo EliteaAI/elitea-testing-public \
  -f suites=admin \
  -f environment=dev

# Watch the run
gh run watch --repo EliteaAI/elitea-testing-public

# Once complete, check logs
gh run view --repo EliteaAI/elitea-testing-public --log | grep -B 5 "Login failed"
```

**Expected:** Admin tests should skip with same error if issue persists

---

## Debug Checklist

When reproducing, check these specific items:

### 1. Cookie Domain Validation
```python
# In api_auth.py, add after login():
cookies = self.session.cookies
for cookie in cookies:
    print(f"Cookie: {cookie.name}")
    print(f"  Domain: {cookie.domain}")
    print(f"  Path: {cookie.path}")
    print(f"  Secure: {cookie.secure}")
```

**Expected:** `elitea-staging_auth_session` with `domain=.elitea.ai` or `dev.elitea.ai`  
**Problem:** Cookie domain mismatch or missing cookie entirely

### 2. Redirect Chain Validation
```python
# In api_auth.py login(), add after each request:
logger.info(f"Response URL: {resp.url}")
logger.info(f"Status: {resp.status_code}")
logger.info(f"Redirects: {[r.url for r in resp.history]}")
```

**Expected:** Should see 3-4 redirects ending at `https://dev.elitea.ai`  
**Problem:** Redirect stops at Keycloak auth page

### 3. Response Content Check
```python
# If stuck on auth page, inspect HTML:
if "auth" in resp.url.lower():
    print("Response HTML:")
    print(resp.text[:1000])  # First 1KB
```

**Look for:**
- Error messages in HTML
- JavaScript redirects that `requests` library doesn't execute
- Hidden forms that need to be submitted

### 4. Session State
```python
# Check session state throughout flow:
print("Session cookies:", list(self.session.cookies))
print("Session headers:", dict(self.session.headers))
```

**Problem indicators:**
- Session loses cookies between steps
- Missing required headers (`Referer`, `Origin`)

---

## Quick Fixes to Try

### Fix 1: Increase Session Timeout (If Theory 2)
```python
# In fixtures/session_fixtures.py, after auth_state fixture creates storage:
# Force immediate context creation instead of lazy
ctx = browser.new_context(storage_state=storage_state)
ctx.close()  # Just to verify it works
return storage_state
```

### Fix 2: Retry Auth on 200-but-stuck (If Theory 1)
```python
# In api_auth.py login(), after credential POST:
if "auth" in resp.url.lower() and resp.status_code == 200:
    # Maybe need to re-submit or wait
    logger.warning("Got 200 but still on auth page, retrying...")
    time.sleep(2)
    resp = self.session.get(self.base_url, allow_redirects=True, timeout=30)
```

### Fix 3: Explicit Cookie Forwarding (If Theory 1)
```python
# In api_auth.py, modify get_playwright_cookies():
def get_playwright_cookies(self) -> list[dict]:
    cookies = []
    for cookie in self.session.cookies:
        # Force domain to be more permissive
        domain = cookie.domain
        if domain.startswith('.'):
            domain = domain[1:]  # Remove leading dot
        
        cookies.append({
            "name": cookie.name,
            "value": cookie.value,
            "domain": domain,  # Modified domain
            "path": cookie.path,
            "secure": cookie.secure,
            "httpOnly": cookie.has_nonstandard_attr("HttpOnly"),
            "sameSite": "Lax",  # More permissive
        })
    return cookies
```

### Fix 4: Use Browser-Based Auth Instead (Nuclear Option)
```python
# Replace API auth with actual browser login (slower but more reliable)
def auth_state(browser: Browser):
    context = browser.new_context()
    page = context.new_page()
    
    page.goto(f"{ELITEA_URL}")
    # Wait for redirect to Keycloak
    page.wait_for_url("**/auth**")
    
    # Fill login form
    page.fill('input[name="username"]', TEST_USER_EMAIL)
    page.fill('input[name="password"]', TEST_USER_PASSWORD)
    page.click('input[type="submit"]')
    
    # Wait for redirect back to app
    page.wait_for_url(f"{ELITEA_URL}/**", timeout=30000)
    
    # Save storage state
    storage = context.storage_state()
    context.close()
    return storage
```

---

## Expected vs Actual Behavior

### Expected (Working Locally)
```
✅ api_auth.py runs successfully
✅ Got 5+ cookies including elitea-staging_auth_session
✅ Final URL: https://dev.elitea.ai (no auth in path)
✅ Tests run normally
```

### Actual (CI Failure)
```
❌ Login returns 200 but stays on auth page
❌ URL: https://auth.elitea.ai/realms/dev/login-actions/authenticate
❌ Missing elitea-staging_auth_session cookie
❌ pytest.skip() → All admin tests skipped
```

---

## Why Chat Passed but Admin Failed

**Hypothesis:** Timing-based race condition

```
Chat Suite (started 14:09:50):
├─ auth_state fixture runs → SUCCESS (cookies fresh)
├─ Tests start immediately (14:10:16)
└─ 19/19 PASSED

Admin Suite (started 14:09:49):
├─ auth_state fixture runs → ??? (1 second before chat)
├─ Tests delayed until 14:10:11 (21-second gap!)
└─ 7/7 SKIPPED
```

**The 21-second gap between auth setup and test start could explain:**
- Session expired if Keycloak timeout < 21 seconds
- Different auth instance if they don't share session fixture
- Race condition if parallel setup interfered

**Test this theory:**
```bash
# Run both suites sequentially instead of parallel
gh workflow run test-ui-dev.yml \
  --repo EliteaAI/elitea-testing-public \
  -f suites=chat \
  -f environment=dev

# Wait for completion, then run admin
gh workflow run test-ui-dev.yml \
  --repo EliteaAI/elitea-testing-public \
  -f suites=admin \
  -f environment=dev
```

---

## Files to Check

1. **`automation/api_auth.py`** - The login implementation (lines 50-130)
2. **`automation/fixtures/session_fixtures.py`** - auth_state fixture (lines 85-125)
3. **`automation/conftest.py`** - How auth_state is used
4. **`.github/workflows/test-ui-dev.yml`** - CI workflow configuration
5. **`automation/.env.test`** - Environment variables (check symlink target `../../.env.test`)

---

## Next Steps

1. **Run Option 1 reproduction** locally to see if you can reproduce the 200-but-stuck scenario
2. **If reproduced:** Add debug logging and capture the exact URL/cookies at failure point
3. **If NOT reproduced locally:** Run Option 3 (CI workflow) to isolate as CI-environment issue
4. **Once root cause identified:** Apply appropriate fix from Quick Fixes section
5. **Verify fix:** Re-run admin suite and confirm tests execute (pass or fail, but not skip)

---

## Success Criteria

Auth issue is **resolved** when:
- ✅ `python api_auth.py` completes with "Login successful"
- ✅ Final URL is `https://dev.elitea.ai` (no /auth/ in path)
- ✅ `elitea-staging_auth_session` cookie is present
- ✅ Admin tests **run** (even if they fail on assertions, they must not skip on auth)

---

**Document Created:** 2026-08-24  
**Status:** Reproduction guide ready  
**Priority:** High - Blocking 3 of 4 newly verified tests from CI validation
