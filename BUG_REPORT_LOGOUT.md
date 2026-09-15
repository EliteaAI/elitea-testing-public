# [BUG] Logout functionality fails with "Invalid parameter: id_token_hint" error - user remains logged in

## Environment
- **Platform**: DEV (https://dev.elitea.ai)
- **Browser**: Chromium (Playwright automated)
- **User**: Test user (automated test account)
- **Date**: 2026-08-27

## Steps to Reproduce

1. Login to DEV environment (https://dev.elitea.ai)
2. Navigate to **Settings** (sidebar menu)
3. Go to **Profile** section
4. Click the **Logout** button

## Actual Results

- ❌ Browser is redirected to error page with message:
  ```
  We are sorry...
  Invalid parameter: id_token_hint
  ```
- ❌ URL shows Keycloak error: `https://ai-auth.elitea.ai/auth/realms/dev/...`
- ❌ When navigating back to `https://dev.elitea.ai`, **user is still logged in** (session not terminated)
- ❌ Logout functionality is completely broken - session persists after logout attempt

**Screenshots**: 
- Error page after clicking Logout: `07_ERROR_PAGE.png`
- Still logged in after attempting logout: `09_STILL_LOGGED_IN.png`

## Expected Results

- ✅ User should be logged out successfully
- ✅ Browser should redirect to login page
- ✅ Session should be terminated (cookies cleared)
- ✅ When navigating back to DEV, user should see the login page

## Technical Details

### Error Message
```
Invalid parameter: id_token_hint
```

### Root Cause Analysis
The error "Invalid parameter: id_token_hint" indicates that:

1. **Frontend Issue**: The EliteaUI logout handler is passing an invalid or missing `id_token_hint` parameter to Keycloak during the OIDC logout flow
2. **Keycloak Requirement**: OpenID Connect (OIDC) logout requires a valid `id_token_hint` parameter to identify the session being terminated
3. **Session Persistence**: Because Keycloak rejects the logout request, the session cookies remain valid and the user stays logged in

### Affected Flow
```
EliteaUI Logout Button Click
  ↓
Redirect to Keycloak /logout endpoint
  ↓
Missing/Invalid id_token_hint parameter
  ↓
Keycloak returns error page
  ↓
User still logged in (session not terminated)
```

### Network Logs
See attached `network_logs.json` for full request/response details showing:
- Logout request parameters
- Keycloak error response
- Session cookies still present after failed logout

## Impact

- **Severity**: HIGH - Users cannot log out of the application
- **Security Risk**: Users on shared computers cannot terminate their sessions
- **User Experience**: Confusing error page instead of clean logout
- **Workaround**: None - logout functionality is completely broken

## Additional Context

This issue was discovered during CI test run investigation where all tests were skipped due to authentication failures. The logout bug may be related to broader authentication/session management issues on the DEV environment.

**Related**: 
- CI Run with authentication failures: https://github.com/EliteaAI/elitea-testing-public/actions/runs/33039314963

## Suggested Fix

The EliteaUI logout handler needs to:
1. Extract the `id_token` from the OIDC authentication state
2. Pass it as the `id_token_hint` parameter to Keycloak logout endpoint
3. Ensure proper URL encoding of the parameter

**Example correct OIDC logout URL**:
```
https://ai-auth.elitea.ai/auth/realms/dev/protocol/openid-connect/logout
  ?id_token_hint=<valid_id_token>
  &post_logout_redirect_uri=https://dev.elitea.ai
```

---
**Evidence Files**:
- Screenshots: `logout_bug_evidence/` directory
- Network logs: `logout_bug_evidence/network_logs.json`
- Console logs: `logout_bug_evidence/console_logs.txt`
- Error message: `logout_bug_evidence/error_message.txt`
