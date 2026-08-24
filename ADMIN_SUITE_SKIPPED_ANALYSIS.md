# Admin Suite Tests Skipped - Root Cause Analysis

**GitHub Actions Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32736976833  
**Date:** 2026-08-24  
**Environment:** dev-stable  
**Suites:** admin, chat  

## Issue Summary

All 7 admin suite tests were **SKIPPED** due to authentication failure, while the chat suite tests passed successfully.

```
Admin suite:  7 skipped, 19 deselected in 2.28s
Chat suite:   19 passed, 2 skipped, 48 deselected in 584.84s (9:44)
```

## Root Cause

The admin suite executor received **empty credentials**, while the chat suite executor received proper credentials.

### Evidence from Logs

**Admin executor (user_idx="admin"):**
```
TEST_USER_EMAIL: 
TEST_USER_PASSWORD: 
ELITEA_PROJECT_ID: 
ELITEA_API_TOKEN: 
```

**Chat executor (user_idx="1"):**
```
TEST_USER_EMAIL: ***  (masked, but present)
TEST_USER_PASSWORD: ***  (masked, but present)
ELITEA_PROJECT_ID: ***
ELITEA_API_TOKEN: ***
```

## Technical Details

### Workflow Configuration Issue

In `.github/workflows/test-ui-custom.yml` lines 532-533, credentials are resolved using:

```yaml
TEST_USER_EMAIL: ${{ secrets[format('TEST_USER_NAME_{0}', matrix.user_idx)] || secrets.TEST_USER_EMAIL }}
TEST_USER_PASSWORD: ${{ secrets[format('TEST_USER_PASSWORD_{0}', matrix.user_idx)] || secrets.TEST_USER_PASSWORD }}
```

### The Problem

When `matrix.user_idx="admin"` (the special admin executor):

1. The workflow tries to resolve: `secrets['TEST_USER_NAME_admin']` → **does not exist**
2. Falls back to: `secrets.TEST_USER_EMAIL` → **empty in workflow_call context**
3. Result: **empty string** for credentials

When `matrix.user_idx="1"` (regular numeric executor):

1. The workflow tries to resolve: `secrets['TEST_USER_NAME_1']` → **exists**
2. No fallback needed → **credentials set correctly**

### Why This Happens

The admin suite has a special handler in the matrix preparation (line 440):
```bash
JSON="$JSON{\"user_idx\":\"admin\",\"suites\":\"admin\"}"
```

This uses the **string** `"admin"` as `user_idx` instead of a **number** like `"1"`, which means:
- `TEST_USER_NAME_admin` secret doesn't exist in GitHub repository secrets
- The fallback `secrets.TEST_USER_EMAIL` is empty because this workflow was called via `workflow_call` (not `workflow_dispatch`), and in `workflow_call` mode, those base secrets are not automatically passed

## Impact on Tests

When the `auth_state` fixture (defined in `automation/fixtures/session_fixtures.py`) runs:

1. It calls `get_playwright_storage_state()` from `api_auth.py`
2. The API authentication fails because credentials are empty
3. `pytest.skip()` is called with message:
   ```
   "Authentication failed — check TEST_USER_EMAIL and TEST_USER_PASSWORD: {error}"
   ```
4. All tests in the admin suite are skipped

## Why It Works Locally

In your local configuration (`.env.test`), you have admin user credentials configured directly:

```bash
# From your local config (profile.md mentions "another user is used")
TEST_USER_EMAIL=admin@example.com  # or similar admin user
TEST_USER_PASSWORD=admin_password
```

The local tests don't use indexed credentials (`TEST_USER_NAME_1`, etc.) - they use the base `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` directly.

## Solution Options

### Option 1: Add Admin-Specific Secret (Recommended)

Add a new GitHub repository secret:
- **Secret name:** `TEST_USER_NAME_admin`
- **Secret value:** The admin user's email/username
- **Secret name:** `TEST_USER_PASSWORD_admin`  
- **Secret value:** The admin user's password

This follows the existing pattern and requires no code changes.

### Option 2: Use a Numeric Index for Admin

Change the matrix preparation to assign admin to a specific numeric user (e.g., user 10):

```bash
# Instead of:
JSON="$JSON{\"user_idx\":\"admin\",\"suites\":\"admin\"}"

# Use:
JSON="$JSON{\"user_idx\":\"10\",\"suites\":\"admin\"}"
```

Then create secrets:
- `TEST_USER_NAME_10` = admin user email
- `TEST_USER_PASSWORD_10` = admin user password

### Option 3: Special Handling for Admin Executor

Modify the workflow to check if `user_idx == "admin"` and use different secret names:

```yaml
TEST_USER_EMAIL: ${{ matrix.user_idx == 'admin' && secrets.ADMIN_USER_EMAIL || secrets[format('TEST_USER_NAME_{0}', matrix.user_idx)] || secrets.TEST_USER_EMAIL }}
```

However, this is more complex and error-prone.

## Recommended Action

**Use Option 1**: Add the `TEST_USER_NAME_admin` and `TEST_USER_PASSWORD_admin` secrets to the repository with the admin user credentials that work in your local setup.

This:
- ✅ Follows the existing credential resolution pattern
- ✅ Requires no code changes
- ✅ Makes the intent explicit (admin suite needs admin credentials)
- ✅ Keeps the special "admin" executor logic intact

## Verification Steps

After adding the secrets:

1. Re-run the workflow: https://github.com/EliteaAI/elitea-testing-public/actions/workflows/test-ui-custom.yml
2. Select `dev-stable` environment
3. Enter custom suites: `admin,chat`
4. Check that admin suite shows credentials as `***` (masked but present) in logs
5. Verify tests authenticate and run (not skip)

## Related Files

- Workflow: `.github/workflows/test-ui-custom.yml` (lines 440, 532-533)
- Auth fixture: `automation/fixtures/session_fixtures.py` (lines 82-130)
- API auth: `automation/api_auth.py` (Keycloak authentication logic)
- Local config: `automation/.env.test` (working credentials for local runs)
