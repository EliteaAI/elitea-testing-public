# ✅ Solution: Forward-Auth Login Bypasses Keycloak Issues

## Date: 2026-08-27

## Problem Summary

**CI tests failing with 100% skip rate** due to Keycloak authentication failures:
- All test users (`autotest_user_1` through `autotest_user_admin`) unable to authenticate
- Keycloak returns 200 but doesn't redirect, staying on `/login-actions/authenticate`
- Tests skip instead of run → CI pipeline completely blocked

## Solution Discovered

Admin provided alternative login URL: **`https://dev.elitea.ai/forward-auth/auth_form/login`**

This URL **bypasses Keycloak** and uses a direct authentication form, successfully working where Keycloak fails.

---

## How Forward-Auth Works

### Authentication Flow Comparison

**❌ Broken Keycloak Flow:**
```
1. GET https://dev.elitea.ai
2. → Redirect to Keycloak: https://ai-auth.elitea.ai/auth/realms/dev/...
3. → POST credentials to /login-actions/authenticate
4. → Keycloak returns 200 but DOESN'T redirect ❌
5. → Tests skip
```

**✅ Working Forward-Auth Flow:**
```
1. GET https://dev.elitea.ai/forward-auth/auth_form/login
2. → POST credentials to /forward-auth/auth_form/authorize
   - Field names: 'login' (not 'username'), 'password', 'target'
3. → Redirects to https://dev.elitea.ai/app/ ✅
4. → Sets centry_auth_session cookie
5. → Tests can run!
```

### Key Differences

| Aspect | Keycloak | Forward-Auth |
|--------|----------|--------------|
| **Endpoint** | `/auth/realms/dev/...` | `/forward-auth/auth_form/authorize` |
| **Username field** | `username` | `login` |
| **Success indicator** | Redirect away from `/auth/` | Redirect to `/app/` |
| **Cookie name** | `elitea-staging_auth_session` | `centry_auth_session` |
| **Current status** | ❌ Broken (200 but no redirect) | ✅ Working |

---

## Implementation

### New Module Created: `api_auth_forward.py`

```python
from api_auth_forward import get_playwright_storage_state_forward

# Use in fixtures
storage_state = get_playwright_storage_state_forward(
    base_url="https://dev.elitea.ai",
    username="autotest_user_admin",
    password="<password>"
)

context = browser.new_context(storage_state=storage_state)
# Now authenticated!
```

### Test Results

```bash
$ python api_auth_forward.py

Testing forward-auth based authentication...
INFO: Starting forward-auth login for autotest_user_admin
INFO: Login successful - redirected to https://dev.elitea.ai/app/

[OK] Login successful! Got 1 cookies:
  - centry_auth_session

Testing with Playwright...
[OK] Playwright test passed - already authenticated!
```

---

## Integration Options

### Option 1: Replace Keycloak Auth in Fixtures (RECOMMENDED)

**File**: `automation/fixtures/session_fixtures.py`

**Change in `auth_state` fixture:**
```python
# OLD (broken Keycloak):
from api_auth import get_playwright_storage_state

storage_state = get_playwright_storage_state(
    base_url=settings.elitea_auth_url,
    username=TEST_USER_EMAIL,
    password=TEST_USER_PASSWORD,
)

# NEW (working forward-auth):
from api_auth_forward import get_playwright_storage_state_forward

storage_state = get_playwright_storage_state_forward(
    base_url=settings.elitea_url,  # Note: use elitea_url not elitea_auth_url
    username=TEST_USER_EMAIL,
    password=TEST_USER_PASSWORD,
)
```

### Option 2: Environment-Based Fallback

Add logic to try forward-auth if Keycloak fails:

```python
try:
    # Try Keycloak first
    from api_auth import get_playwright_storage_state
    storage_state = get_playwright_storage_state(...)
except RuntimeError as e:
    # Fall back to forward-auth
    logger.warning("Keycloak auth failed, trying forward-auth: %s", e)
    from api_auth_forward import get_playwright_storage_state_forward
    storage_state = get_playwright_storage_state_forward(...)
```

---

## Impact Assessment

### What This Fixes

✅ **Unblocks CI pipeline** - Tests can authenticate and run
✅ **100% test skip rate → normal execution**
✅ **No changes needed to test code** - only auth fixture
✅ **Same authentication result** - valid session cookies
✅ **Works with existing test users** - `autotest_user_admin` confirmed working

### What This Doesn't Fix

❌ **Logout bug still exists** - "Invalid parameter: id_token_hint" error
- This is a separate EliteaUI issue (see `BUG_REPORT_LOGOUT.md`)
- Can be reproduced and fixed independently

❌ **Keycloak auth still broken** - underlying issue remains
- Forward-auth is a **workaround**, not a fix
- Keycloak integration should still be investigated by platform team

---

## Testing Plan

### 1. Local Verification
```bash
cd automation

# Test forward-auth module
python api_auth_forward.py
# Expected: "[OK] Login successful!"

# Run a single UI test with forward-auth
# (after updating fixtures)
pytest tests/ui/smoke/test_ui_smoke.py -v
# Expected: Test runs (not skipped)
```

### 2. CI Integration

**Update workflow secrets** (if needed):
- Verify `TEST_USER_PASSWORD_1` through `TEST_USER_PASSWORD_ADMIN` are correct
- No new secrets needed - same users work with forward-auth

**Update fixture** (one line change):
- Change import in `session_fixtures.py` from `api_auth` to `api_auth_forward`

**Test in CI**:
- Push to feature branch
- Trigger workflow manually
- Verify tests run (not skip)

---

## Rollout Strategy

### Phase 1: Immediate (This Session) ✅
- [x] Discover forward-auth endpoint
- [x] Create `api_auth_forward.py` module
- [x] Verify it works locally
- [x] Document solution

### Phase 2: Integration (Next - Awaiting Approval)
- [ ] Update `session_fixtures.py` to use forward-auth
- [ ] Test locally with multiple test suites
- [ ] Commit changes
- [ ] Create PR

### Phase 3: CI Validation
- [ ] Merge PR to main
- [ ] Trigger CI workflow
- [ ] Monitor test execution rate (should drop from 100% skip to 0%)
- [ ] Verify all test suites run

### Phase 4: Document & Communicate
- [ ] Update `.agents/testing.md` with forward-auth notes
- [ ] Document Keycloak issue for platform team
- [ ] Close related tickets

---

## Risk Assessment

### Low Risk
- ✅ **Backward compatible** - if forward-auth fails, tests skip (same as now)
- ✅ **Isolated change** - only affects auth fixture, not test logic
- ✅ **Proven working** - tested with real credentials
- ✅ **Reversible** - can revert to Keycloak if needed

### Potential Issues
- ⚠️ **Production differences** - forward-auth may not exist on STAGE/NEXT
  - **Mitigation**: Use environment-specific logic or keep Keycloak for prod envs
- ⚠️ **Cookie expiration** - `centry_auth_session` vs `elitea-staging_auth_session`
  - **Mitigation**: Session-scoped fixture re-authenticates each test run

---

## Files Modified (Pending Approval)

**New files:**
- ✅ `automation/api_auth_forward.py` - Forward-auth authentication module
- ✅ `automation/test_forward_auth_login.py` - Verification script
- ✅ `FORWARD_AUTH_SOLUTION.md` - This document

**Files to modify (awaiting approval):**
- `automation/fixtures/session_fixtures.py` - Use forward-auth in `auth_state` fixture

**No commits made yet** - awaiting your approval.

---

## Next Steps

1. **Review this solution** - Is forward-auth acceptable for DEV environment?
2. **Approve fixture change** - Should we update `session_fixtures.py`?
3. **Test in CI** - Want to run a test workflow to verify?
4. **Parallel Keycloak fix** - Platform team should investigate why Keycloak auth broke

---

## Questions?

- **Why did Keycloak break?** Unknown - could be user configuration, realm settings, or service issue
- **Is forward-auth secure?** It's an existing Elitea endpoint, appears to be intentional fallback
- **Will this work on other envs?** Unknown - needs testing on STAGE/NEXT
- **Should we fix Keycloak anyway?** Yes - forward-auth is a workaround, not root cause fix

---

## Summary

**The admin-provided forward-auth URL successfully bypasses the Keycloak authentication failure** and provides a working alternative for test authentication. 

**Recommendation**: Update the auth fixture to use forward-auth on DEV environment to immediately unblock CI, while platform team investigates the Keycloak issue.

**Status**: ✅ Solution implemented and tested - **awaiting approval to commit changes**.
