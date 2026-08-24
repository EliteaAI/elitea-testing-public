# Workflow Credentials Refactoring Summary

**Date:** 2026-08-24  
**Files Modified:** `.github/workflows/test-ui-custom.yml`

## Changes Made

### 1. Renamed `user_idx` to `suffix` (More Meaningful)

**Before:**
```yaml
matrix.user_idx: "1", "2", "3", ..., "admin"
```

**After:**
```yaml
matrix.suffix: "1", "2", "3", ..., "ADMIN"
```

**Rationale:** The term "suffix" more accurately describes its purpose - it's appended to secret names and usernames, not an array index.

### 2. Standardized Username Pattern

**Before:**
- Usernames came from secrets: `TEST_USER_NAME_1`, `TEST_USER_NAME_2`, etc.
- Different usernames across environments
- Admin user required separate secret

**After:**
- Usernames follow a **fixed pattern**: `autotest_user_[suffix_lowercase]`
  - `autotest_user_1`
  - `autotest_user_2`
  - `autotest_user_3`
  - ...
  - `autotest_user_admin` (lowercase for username)
- Secrets use UPPERCASE suffix: `TEST_USER_PASSWORD_ADMIN`
- No username secrets needed anymore

**Benefits:**
- ✅ Consistent naming across all environments
- ✅ Easier to set up test users in Keycloak
- ✅ Fewer secrets to manage
- ✅ Self-documenting (username tells you which executor)

### 3. Simplified Secret Structure

**Before:**
```yaml
Secrets required per user:
- TEST_USER_NAME_1
- TEST_USER_PASSWORD_1
- TEST_USER_PROJECT_1
- TEST_USER_TOKEN_1
(Repeated for 1-10, plus special handling for admin)
```

**After:**
```yaml
Secrets required per user:
- TEST_USER_PASSWORD_1
- TEST_USER_PROJECT_1
- TEST_USER_TOKEN_1
(Repeated for 1-9, plus _ADMIN)
```

**Admin credentials now explicit:**
```yaml
TEST_USER_PASSWORD_ADMIN
TEST_USER_PROJECT_ADMIN
TEST_USER_TOKEN_ADMIN
```

**Reduction:** 40 secrets → 30 secrets (25% fewer)

### 4. Updated Matrix Generation

**Before:**
```bash
JSON="$JSON{\"user_idx\":\"admin\",\"suites\":\"admin\"}"
```

**After:**
```bash
JSON="$JSON{\"suffix\":\"ADMIN\",\"suites\":\"admin\"}"
```

### 5. Updated Environment Variable Resolution

**Before:**
```yaml
TEST_USER_EMAIL: ${{ secrets[format('TEST_USER_NAME_{0}', matrix.user_idx)] || secrets.TEST_USER_EMAIL }}
TEST_USER_PASSWORD: ${{ secrets[format('TEST_USER_PASSWORD_{0}', matrix.user_idx)] || secrets.TEST_USER_PASSWORD }}
ELITEA_PROJECT_ID: ${{ secrets[format('TEST_USER_PROJECT_{0}', matrix.user_idx)] || secrets.ELITEA_PROJECT_ID }}
ELITEA_API_TOKEN: ${{ secrets[format('TEST_USER_TOKEN_{0}', matrix.user_idx)] || secrets.ELITEA_API_TOKEN }}
```

**After:**
```yaml
TEST_USER_EMAIL: autotest_user_${{ matrix.suffix == 'ADMIN' && 'admin' || matrix.suffix }}
TEST_USER_PASSWORD: ${{ secrets[format('TEST_USER_PASSWORD_{0}', matrix.suffix)] }}
ELITEA_PROJECT_ID: ${{ secrets[format('TEST_USER_PROJECT_{0}', matrix.suffix)] }}
ELITEA_API_TOKEN: ${{ secrets[format('TEST_USER_TOKEN_{0}', matrix.suffix)] }}
```

**Key changes:**
- Username is now **hardcoded pattern** with lowercase conversion for ADMIN (no secret lookup)
- Secrets always use UPPERCASE suffix (e.g., `TEST_USER_PASSWORD_ADMIN`)
- Username uses lowercase (e.g., `autotest_user_admin`)
- Removed fallback to `secrets.TEST_USER_EMAIL` (was causing the admin skip issue)
- Direct secret resolution without fallbacks

### 6. Updated Artifact Names

**Before:**
```yaml
name: test-results-${{ steps.env.outputs.name }}-user${{ matrix.user_idx }}-${{ github.run_number }}
```

**After:**
```yaml
name: test-results-${{ steps.env.outputs.name }}-user${{ matrix.suffix }}-${{ github.run_number }}
```

All artifact names now use `suffix` consistently.

## Required Keycloak Setup

Create the following users in Keycloak for each environment (dev, stage2, next):

| Username | Purpose | Required Secrets |
|----------|---------|------------------|
| `autotest_user_1` | Parallel executor 1 | `TEST_USER_PASSWORD_1`, `TEST_USER_PROJECT_1`, `TEST_USER_TOKEN_1` |
| `autotest_user_2` | Parallel executor 2 | `TEST_USER_PASSWORD_2`, `TEST_USER_PROJECT_2`, `TEST_USER_TOKEN_2` |
| `autotest_user_3` | Parallel executor 3 | `TEST_USER_PASSWORD_3`, `TEST_USER_PROJECT_3`, `TEST_USER_TOKEN_3` |
| `autotest_user_4` | Parallel executor 4 | `TEST_USER_PASSWORD_4`, `TEST_USER_PROJECT_4`, `TEST_USER_TOKEN_4` |
| `autotest_user_5` | Parallel executor 5 | `TEST_USER_PASSWORD_5`, `TEST_USER_PROJECT_5`, `TEST_USER_TOKEN_5` |
| `autotest_user_6` | Parallel executor 6 | `TEST_USER_PASSWORD_6`, `TEST_USER_PROJECT_6`, `TEST_USER_TOKEN_6` |
| `autotest_user_7` | Parallel executor 7 | `TEST_USER_PASSWORD_7`, `TEST_USER_PROJECT_7`, `TEST_USER_TOKEN_7` |
| `autotest_user_8` | Parallel executor 8 | `TEST_USER_PASSWORD_8`, `TEST_USER_PROJECT_8`, `TEST_USER_TOKEN_8` |
| `autotest_user_9` | Parallel executor 9 + User B | `TEST_USER_PASSWORD_9`, `TEST_USER_PROJECT_9`, `TEST_USER_TOKEN_9` |
| `autotest_user_admin` | **Admin suite only** (lowercase) | `TEST_USER_PASSWORD_ADMIN`, `TEST_USER_PROJECT_ADMIN`, `TEST_USER_TOKEN_ADMIN` (UPPERCASE) |

## Required GitHub Secrets

### New Secrets to Add

```
TEST_USER_PASSWORD_ADMIN
TEST_USER_PROJECT_ADMIN
TEST_USER_TOKEN_ADMIN
```

### Secrets to Remove (No Longer Needed)

```
TEST_USER_NAME_1 through TEST_USER_NAME_10
TEST_USER_EMAIL (base fallback)
TEST_USER_PASSWORD (base fallback)
```

## Migration Steps

### 1. Create Keycloak Users

For each environment (dev-stable, stage2, next):

```bash
# Create users with pattern autotest_user_[1-9, admin]
# Note: Username is LOWERCASE, but secrets are UPPERCASE
# Example for dev-stable:
Username: autotest_user_1
Email: autotest_user_1@elitea.ai (or your domain)
Password: (secure password)
Roles: standard user roles

Username: autotest_user_admin  # lowercase "admin"
Email: autotest_user_admin@elitea.ai
Password: (secure password)
Roles: admin roles + standard roles
```

### 2. Update GitHub Secrets

```bash
# Add new ADMIN secrets
gh secret set TEST_USER_PASSWORD_ADMIN --body "..."
gh secret set TEST_USER_PROJECT_ADMIN --body "..."
gh secret set TEST_USER_TOKEN_ADMIN --body "..."

# Optional: Remove deprecated secrets
gh secret remove TEST_USER_NAME_1
gh secret remove TEST_USER_NAME_2
# ... (continue for 3-10)
gh secret remove TEST_USER_EMAIL
```

### 3. Update Existing Password Secrets

Ensure passwords match the new Keycloak users:
```bash
gh secret set TEST_USER_PASSWORD_1 --body "[password for autotest_user_1]"
gh secret set TEST_USER_PASSWORD_2 --body "[password for autotest_user_2]"
# ... (continue for 3-9)
```

### 4. Test the Changes

Run a test workflow with admin suite:

```bash
# Via GitHub Actions UI:
# 1. Go to Actions → UI Tests CUSTOM
# 2. Click "Run workflow"
# 3. Select environment: dev-stable
# 4. Enter custom suites: admin,chat
# 5. Click "Run workflow"

# Expected result:
# - Admin suite: autotest_user_ADMIN authenticates successfully
# - Chat suite: autotest_user_1 authenticates successfully
# - Both show credentials as *** (masked but present)
```

## Verification Checklist

After deployment, verify:

- [ ] Admin suite runs with `autotest_user_ADMIN` (not skipped)
- [ ] Other suites run with `autotest_user_1` through `autotest_user_9`
- [ ] All credentials show as `***` in logs (masked but present, not empty)
- [ ] Tests authenticate successfully (no "Login failed: 200")
- [ ] Artifact names include correct suffix (e.g., `allure-results-dev-stable-userADMIN-123`)
- [ ] Log messages show: "Running suites 'admin' with user suffix ADMIN (autotest_user_ADMIN)"

## Benefits Summary

1. **Fixes the admin suite skip issue** - No more empty credentials for admin executor
2. **Simpler setup** - Username pattern is self-documenting
3. **Fewer secrets** - 25% reduction in secret count
4. **More maintainable** - Consistent naming across environments
5. **Clearer logs** - Usernames reveal which executor is running
6. **Easier troubleshooting** - Can identify user from test logs alone

## Backward Compatibility Notes

⚠️ **Breaking Change:** This refactoring requires:
1. New Keycloak users with the `autotest_user_*` naming pattern
2. Updated GitHub secrets (new `_ADMIN` secrets)
3. Existing `TEST_USER_NAME_*` secrets are no longer used

**Migration window:** Coordinate with team to ensure Keycloak users and secrets are ready before merging this change.

## Related Files

- Workflow: `.github/workflows/test-ui-custom.yml`
- Analysis: `ADMIN_SUITE_SKIPPED_ANALYSIS.md`
- Original issue: GitHub Actions run #32736976833
