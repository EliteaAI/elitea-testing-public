# Username Case Fix - Lowercase for Keycloak, Uppercase for Secrets

**Commit:** `01fcfba20`  
**Date:** 2026-08-24

## Issue

The initial implementation used uppercase for both usernames and secrets:
- Username: `autotest_user_ADMIN` ❌
- Secret: `TEST_USER_PASSWORD_ADMIN` ✅

However, Keycloak usernames should follow lowercase convention:
- Username: `autotest_user_admin` ✅
- Secret: `TEST_USER_PASSWORD_ADMIN` ✅

## Solution

Added conditional logic to convert suffix to lowercase for usernames while keeping it uppercase for secret resolution:

```yaml
# Matrix suffix stays uppercase: "ADMIN"
matrix.suffix: "ADMIN"

# Username converted to lowercase
TEST_USER_EMAIL: autotest_user_${{ matrix.suffix == 'ADMIN' && 'admin' || matrix.suffix }}
# Result: autotest_user_admin

# Secrets use uppercase suffix
TEST_USER_PASSWORD: ${{ secrets[format('TEST_USER_PASSWORD_{0}', matrix.suffix)] }}
# Result: secrets['TEST_USER_PASSWORD_ADMIN']
```

## Implementation Details

### Username Pattern

| Suffix in Matrix | Username Generated | Secret Used |
|------------------|-------------------|-------------|
| `"1"` | `autotest_user_1` | `TEST_USER_PASSWORD_1` |
| `"2"` | `autotest_user_2` | `TEST_USER_PASSWORD_2` |
| `"ADMIN"` | `autotest_user_admin` | `TEST_USER_PASSWORD_ADMIN` |

### Code Changes

**Line 509 (TEST_USER_EMAIL):**
```yaml
# Before:
TEST_USER_EMAIL: autotest_user_${{ matrix.suffix }}

# After:
TEST_USER_EMAIL: autotest_user_${{ matrix.suffix == 'ADMIN' && 'admin' || matrix.suffix }}
```

**Lines 557, 566 (Log messages):**
```yaml
# Before:
echo "... (autotest_user_${{ matrix.suffix }})"

# After:
USERNAME="autotest_user_${{ matrix.suffix == 'ADMIN' && 'admin' || matrix.suffix }}"
echo "... ($USERNAME)"
```

## Why This Matters

### 1. Naming Convention Consistency
- **Standard users:** `autotest_user_1`, `autotest_user_2` (already lowercase digits)
- **Admin user:** `autotest_user_admin` (now also lowercase)
- Follows typical username conventions (lowercase, no capitals)

### 2. Keycloak Best Practices
- Usernames are typically lowercase
- Avoids case-sensitivity issues
- Cleaner, more professional appearance

### 3. Secret Naming Stays Clear
- Secrets remain UPPERCASE: `TEST_USER_PASSWORD_ADMIN`
- Follows GitHub secrets naming convention
- Easy to distinguish from usernames

## Keycloak Setup (Updated)

Create these users:

```bash
# Standard users (already lowercase)
autotest_user_1
autotest_user_2
autotest_user_3
...
autotest_user_9

# Admin user (now lowercase)
autotest_user_admin  # ← Changed from autotest_user_ADMIN
```

## GitHub Secrets (Unchanged)

These remain UPPERCASE as before:

```bash
TEST_USER_PASSWORD_1
TEST_USER_PASSWORD_2
...
TEST_USER_PASSWORD_9
TEST_USER_PASSWORD_ADMIN  # ← Still uppercase

TEST_USER_PROJECT_ADMIN
TEST_USER_TOKEN_ADMIN
```

## Verification

When the workflow runs, logs will show:

```
Running suites 'admin' with user suffix ADMIN (autotest_user_admin)
                                     ↑                    ↑
                                uppercase            lowercase
                                (for secrets)        (for Keycloak)
```

## Commit History

1. **`c149aa70d`** - Main refactoring (user_idx → suffix, standardize credentials)
2. **`6d68a83f2`** - Fix workflow startup (remove deprecated secrets)
3. **`01fcfba20`** - **This fix** (lowercase usernames, uppercase secrets)

## Impact

- ✅ No breaking changes to secret names
- ✅ Username now follows lowercase convention
- ✅ Works with standard Keycloak username rules
- ✅ Clearer separation: lowercase = username, UPPERCASE = secret
