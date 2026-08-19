# Fix #1: test_credential_usage_and_deletion_mismatch

**Date:** 2026-08-17  
**Branch:** automation/fixes (commit 690cf662)  
**Test:** `test_credential_usage_and_deletion_mismatch`  
**File:** `tests/ui/toolkits/test_credential_usage_in_toolkit_flows.py`

---

## Issue

### Symptom:
Test failed 3 times with error:
```
Failed to list branches: 404 
{"message": "Not Found", "documentation_url": "https://docs.github.com/rest/branches/branches#list-branches", "status": "404"}
```

### Screenshot Evidence:
`test_credential_usage_and_deletion_mismatch_FAIL_20260817_172123.png`

Shows toolkit attempting to run `list_branches_in_repo` tool, which returns 404 from GitHub API.

---

## Root Cause

**Configuration error in `automation/config.py`:**

```python
# WRONG - Repository doesn't exist
git_repo: str = "EliteaAI/elitea-testing"
github_repo: str = "EliteaAI/elitea-testing"
```

The repository `EliteaAI/elitea-testing` **does not exist** on GitHub (returns 404).

**Test Flow:**
1. Test creates GitHub credential with token from `.env.test` ✅
2. Test creates GitHub toolkit pointing to `settings.git_repo` ✅
3. Test runs `list_branches_in_repo` tool via Test Settings panel
4. Backend makes GitHub API call: `GET /repos/EliteaAI/elitea-testing/branches`
5. GitHub returns **404 Not Found** ❌
6. Test fails ❌

---

## Fix

### Change Applied:

```python
# CORRECT - Repository exists and is accessible
git_repo: str = "EliteaAI/elitea-testing-public"
github_repo: str = "EliteaAI/elitea-testing-public"
```

**Verification:**
```bash
curl -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/EliteaAI/elitea-testing-public/branches
# Returns: 200 OK, 30 branches found ✅
```

---

## Test Result After Fix

**Status:** ✅ **PASSED**  
**Duration:** 46.85s  
**Attempts:** 1 (no reruns needed)

```
test_credential_usage_and_deletion_mismatch PASSED [100%]
============================== 1 passed in 46.85s ==============================
```

### Test Flow (Successful):
1. ✅ Created GitHub credential with valid token
2. ✅ Created GitHub toolkit pointing to `EliteaAI/elitea-testing-public`
3. ✅ Opened Test Settings panel
4. ✅ Selected `list_branches_in_repo` tool
5. ✅ Ran tool - GitHub API returned branches successfully
6. ✅ Verified result contains branch data with `"name":` key
7. ✅ Deleted credential via API
8. ✅ Verified toolkit Configuration field shows mismatch state (red/invalid)

---

## Impact

### Tests Fixed by This Change:

This configuration fix affects **ALL tests** that:
1. Create GitHub toolkits using `settings.git_repo` or `settings.github_repo`
2. Run toolkit operations that call the GitHub API
3. Test GitHub authentication/credential flows

**Potentially affected tests:**
- ✅ `test_credential_usage_and_deletion_mismatch` - **CONFIRMED FIXED**
- `test_github_toolkit_test_settings` (non-parameterized)
- `test_toolkit_test_settings[github]` (parameterized)
- `test_agent_with_toolkit_executes_in_chat`
- `test_create_toolkit[github]` (parameterized)
- `test_chat_with_toolkit[github]` (parameterized)
- Any other test creating GitHub toolkits

---

## Files Modified

### automation/config.py

```diff
-    git_repo: str = "EliteaAI/elitea-testing"
-    github_repo: str = "EliteaAI/elitea-testing"
+    git_repo: str = "EliteaAI/elitea-testing-public"
+    github_repo: str = "EliteaAI/elitea-testing-public"
```

---

## Next Steps

1. ✅ Test #1 fixed and verified locally
2. ⏭️ Re-run remaining 6 blocked tests to see if this fix helps them too
3. ⏭️ Commit changes and update test status
4. ⏭️ Move to next failing test

---

## Lesson Learned

**Configuration errors can masquerade as test failures.**

When a test fails with external API errors (404, 401, etc.), always:
1. Check configuration first (repository names, URLs, tokens)
2. Verify the configured resource exists and is accessible
3. Test the API call independently before debugging test code

In this case, the test code was correct - the configuration was wrong.
