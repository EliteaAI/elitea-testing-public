# DEV Environment Authentication Issues - Investigation Summary

## Date: 2026-08-27

## Overview
Multiple authentication-related issues discovered on DEV environment that are blocking automated tests and affecting user experience.

---

## Issue 1: API-Based Authentication Fails - All CI Tests Skipped

### Symptoms
- **GitHub Actions run 33039314963**: All 18 tests SKIPPED across all suites (skills, pipelines, etc.)
- Authentication via API returns 200 but stays on login page
- Error message: `Login failed: 200 https://ai-auth.elitea.ai/auth/realms/dev/login-actions/authenticate?...`

### Root Cause
The Keycloak authentication endpoint returns HTTP 200 but **does not redirect** back to the application after credentials submission. This indicates one of:

1. **Credentials are invalid** - Test user passwords in GitHub secrets may be wrong/expired
2. **Users don't exist** - `autotest_user_1` through `autotest_user_9` and `autotest_user_admin` may not exist in DEV Keycloak realm
3. **Users are locked** - Accounts may be disabled/locked after failed login attempts  
4. **Keycloak configuration issue** - Required actions (password reset) or realm settings preventing login

### Affected Users
```yaml
# GitHub Actions workflow uses these credentials:
TEST_USER_EMAIL: autotest_user_1  # (or 2-9, admin based on matrix)
TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD_1 }}  # (or 2-9, ADMIN)
```

### Evidence
- **CI Run**: https://github.com/EliteaAI/elitea-testing-public/actions/runs/33039314963
- **Log excerpt**:
  ```
  tests/ui/skills/test_agent_max_five_skills_limit.py::TestAgentMaxFiveSkillsLimit::test_max_five_skills_attach_limit SKIPPEDLogin failed:
  Login failed: 200 https://ai-auth.elitea.ai/auth/realms/dev/login-actions/authenticate?session_code=...
  ```

### Impact
- **Severity**: CRITICAL - All automated tests on DEV are blocked
- **CI Pipeline**: 100% test skip rate - no test validation possible
- **Developer Productivity**: Cannot verify PRs against DEV environment

### Immediate Actions Needed
1. **Verify Keycloak users exist**:
   - Login to Keycloak admin: `https://ai-auth.elitea.ai/auth/admin`
   - Check `dev` realm for users: `autotest_user_1` through `autotest_user_9`, `autotest_user_admin`
   - Verify accounts are **enabled** and have no **Required Actions** pending

2. **Validate GitHub secrets**:
   - Check that `TEST_USER_PASSWORD_1` through `TEST_USER_PASSWORD_9` and `TEST_USER_PASSWORD_ADMIN` match actual passwords
   - Test login manually with these credentials at `https://dev.elitea.ai`

3. **Reset locked accounts** (if needed):
   - In Keycloak admin, check for "Account locked" status
   - Clear failed login attempts counter
   - Unlock accounts if necessary

---

## Issue 2: Logout Fails with "Invalid parameter: id_token_hint" 

### Symptoms  
- User clicks **Settings → Profile → Logout**
- Redirected to error page: **"We are sorry... Invalid parameter: id_token_hint"**
- URL shows Keycloak error: `https://ai-auth.elitea.ai/auth/realms/dev/...`
- When navigating back to DEV, **user is still logged in** (session not terminated)

### Root Cause
EliteaUI logout handler is not providing the required `id_token_hint` parameter to Keycloak's OIDC logout endpoint.

**OpenID Connect logout requires:**
```
https://ai-auth.elitea.ai/auth/realms/dev/protocol/openid-connect/logout
  ?id_token_hint=<valid_id_token>
  &post_logout_redirect_uri=https://dev.elitea.ai
```

**Current behavior:**
- Frontend calls logout endpoint WITHOUT `id_token_hint` (or with invalid value)
- Keycloak rejects request → error page
- Session cookies remain valid → user stays logged in

### Impact
- **Severity**: HIGH - Users cannot log out
- **Security Risk**: Sessions cannot be terminated on shared computers
- **User Experience**: Confusing error instead of clean logout
- **Workaround**: None - logout completely broken

### Technical Flow
```
EliteaUI Logout Button Click
  ↓
Redirect to Keycloak /logout endpoint  
  ↓
❌ Missing/Invalid id_token_hint parameter
  ↓
Keycloak returns error page
  ↓  
User still logged in (session not terminated)
```

### Required Fix
The EliteaUI logout handler needs to:

1. **Extract `id_token`** from OIDC authentication state (stored in browser after login)
2. **Pass as `id_token_hint`** parameter to Keycloak logout endpoint
3. **Ensure proper URL encoding** of the token value

**Example implementation** (pseudocode):
```javascript
// In EliteaUI logout handler
const idToken = localStorage.getItem('oidc_id_token'); // or from auth context
const logoutUrl = new URL('https://ai-auth.elitea.ai/auth/realms/dev/protocol/openid-connect/logout');
logoutUrl.searchParams.set('id_token_hint', idToken);
logoutUrl.searchParams.set('post_logout_redirect_uri', 'https://dev.elitea.ai');
window.location.href = logoutUrl.toString();
```

### Reproduction Attempted
Created automated reproduction script `automation/reproduce_logout_bug.py` but **blocked by Issue #1** - cannot authenticate to test logout flow.

**Script would:**
1. Login via API (BLOCKED - auth fails)
2. Navigate to Settings → Profile
3. Click Logout button
4. Capture error page screenshot
5. Verify session persists after logout

---

## Relationship Between Issues

Both issues stem from authentication/session management problems:

1. **Issue #1** blocks initial authentication → prevents any testing
2. **Issue #2** blocks session termination → prevents clean logout

These may indicate broader problems with Keycloak integration on DEV environment.

---

## Recommended Investigation Order

### Priority 1: Fix Authentication (Issue #1)
**Block all other work until this is resolved** - nothing can be tested without authentication.

**Action items:**
1. Keycloak admin audit (users exist, enabled, no required actions)
2. Validate GitHub secrets match actual passwords
3. Manual login test with `autotest_user_1` credentials
4. Check Keycloak server logs for auth failures at 2026-08-27 04:25:04 UTC

### Priority 2: Fix Logout (Issue #2)  
Once authentication works, address the logout bug.

**Action items:**
1. Review EliteaUI logout handler code
2. Verify `id_token` is stored after successful OIDC login
3. Update logout URL construction to include `id_token_hint`
4. Test logout flow manually
5. Run automated reproduction script to validate fix

---

## Files Generated

- `DEV_AUTHENTICATION_AND_LOGOUT_ISSUES.md` - This summary (root directory)
- `BUG_REPORT_LOGOUT.md` - Logout bug template for elitea_issues (root directory)
- `automation/reproduce_logout_bug.py` - Automated reproduction script (blocked by auth)

---

## Next Steps

1. **Immediate**: Contact DevOps/Platform team about Keycloak user status on DEV
2. **Short-term**: Fix authentication → unblock CI pipeline
3. **Medium-term**: Fix logout → improve security/UX
4. **Long-term**: Add monitoring for auth failures in CI to catch this earlier

---

## Related References

- **CI Run**: https://github.com/EliteaAI/elitea-testing-public/actions/runs/33039314963
- **Similar Issue Example**: https://github.com/EliteaAI/elitea_issues/issues/6273
- **Keycloak Admin Console**: https://ai-auth.elitea.ai/auth/admin
- **DEV Environment**: https://dev.elitea.ai
