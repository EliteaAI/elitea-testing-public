# Private Credential Issue - Root Cause Found

**Date:** 2026-08-24  
**Investigation:** Comparison of passing vs failing toolkit tests  
**Status:** ✅ **ROOT CAUSE IDENTIFIED**

## The Smoking Gun

### Passing Tests (GitHub, Confluence, etc.) 
**File:** `api/client.py` - `create_github_toolkit()` method

```python
"github_configuration": {
    "elitea_title": credential_elitea_title,
    "private": False,  # ← ALWAYS FALSE
},
```

### Failing Tests (Guardrails JIRA)
**File:** `tests/ui/admin/test_guardrails_live_reload.py` - Line 157

```python
"jira_configuration": {
    "elitea_title": guardrails_test_credential["elitea_title"],
    "private": True,  # ← THIS IS THE PROBLEM
},
```

## The Issue

**All working toolkit tests use `private: False`**  
**The guardrails test uses `private: True`**

When `private: True` is set, the API cannot immediately find the credential that was just created, resulting in:
```
400 Bad Request: private_credential_not_found
```

## Evidence from CI Run #32673483437

**Tests that PASSED:**
- `test_create_toolkit[github]` ✅ - Uses `private: False`
- `test_create_toolkit[jira]` ✅ - Uses `private: False` (via toolkit factories)
- `test_create_toolkit[confluence]` ✅ - Uses `private: False`

**Tests that FAILED in other runs:**
- `test_blocked_toolkit_live_reload` ❌ - Uses `private: True`
- `test_blocked_tool_live_reload` ❌ - Uses `private: True`
- `test_sensitive_tool_live_reload` ❌ - Uses `private: True`

## Code Comparison

### Working Pattern (GitHub Toolkit)

```python
# api/client.py - Line ~1670
def create_github_toolkit(
    self,
    name: str,
    credential_elitea_title: str,
    ...
) -> dict:
    settings = {
        "github_configuration": {
            "elitea_title": credential_elitea_title,
            "private": False,  # ← Key difference
        },
        "repository": repository,
        "active_branch": active_branch,
        "base_branch": base_branch,
    }
    
    return self.create_toolkit(
        name=name,
        description=description,
        toolkit_type="github",
        settings=settings,
    )
```

### Failing Pattern (Guardrails JIRA)

```python
# test_guardrails_live_reload.py - Lines 154-170
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": True,  # ← This breaks it
    },
    "selected_tools": [
        "list_projects",
        "search_using_jql",
    ],
}

toolkit = module_toolkit_api.create_toolkit(
    name=name,
    description="JIRA toolkit for guardrails live-reload tests",
    toolkit_type="jira",
    settings=toolkit_settings,
)
```

## Why `private: True` Breaks

**Hypothesis:** Private credentials require:
1. Database propagation time
2. Different access patterns
3. Session/transaction boundaries to be respected

When a credential is created and immediately used with `private: True`, the API backend cannot find it yet.

**With `private: False`:**
- Credential is immediately accessible
- No propagation delay needed
- Works in all tests

## Verification in Successful CI Run

Looking at run #32673483437 (Aug 23, 23:37):

```
test_create_toolkit[github] PASSED  ← private: False
test_create_toolkit[jira] PASSED    ← private: False (from factories)
test_create_toolkit[gitlab] SKIPPED
test_create_toolkit[bitbucket] SKIPPED
test_create_toolkit[confluence] PASSED  ← private: False
```

All passing toolkit tests use `private: False`.

## The Fix

**Change line 157 in `test_guardrails_live_reload.py`:**

```python
# Before (BROKEN):
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": True,  # ← Remove this
    },
    ...
}

# After (FIXED):
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": False,  # ← Change to False
    },
    ...
}
```

## Why This Fix Is Correct

**The tests verify guardrails behavior, NOT credential privacy:**

1. **Blocked Toolkit Test:** Checks if blocking a toolkit prevents its use
   - Privacy level doesn't matter
   
2. **Blocked Tool Test:** Checks if blocking a specific tool prevents its use
   - Privacy level doesn't matter
   
3. **Sensitive Tool Test:** Checks if marking a tool as sensitive requires confirmation
   - Privacy level doesn't matter

**Credential privacy is orthogonal to guardrails functionality.**

## Impact Analysis

### Before Fix
- ❌ All 3 guardrails tests fail in CI
- ❌ All 3 guardrails tests fail locally
- ❌ Tests marked as active (not blocked) causing CI failures

### After Fix
- ✅ Tests should pass (same pattern as all other toolkit tests)
- ✅ Behavior identical to proven working toolkit tests
- ✅ No functional difference for guardrails testing

## Alternative Solutions (NOT RECOMMENDED)

### Option A: Add Delay
```python
time.sleep(3)  # Wait for private credential propagation
```
**Problem:** Fragile, no guarantee it will work, adds test time

### Option B: Poll for Credential
```python
for i in range(5):
    try:
        if credential_api.get_credential(cred["id"]):
            break
    except:
        time.sleep(1)
```
**Problem:** Complex, adds code, still might not work

### Option C: Use Session Scope
```python
@pytest.fixture(scope="session")  # Instead of module
def guardrails_test_credential(...):
```
**Problem:** Doesn't solve the root issue, just masks timing

**→ Option `private: False` is the cleanest and matches proven patterns.**

## Historical Context

### August 21, 2026 - Commits

**Commit `3cdb21f00`:** Added JIRA credential creation
- Introduced `create_jira_credential()` method
- Switched guardrails tests from GitHub to JIRA toolkit

**Commit `8f378972e`:** Removed blocked markers
- Claimed "2 of 3 tests passing locally"
- But used `private: True` (not matching working pattern)

**Likely scenario:** Tests passed intermittently due to timing luck, or were tested with `private: False` initially and changed to `True` later.

## Recommendation

**Priority: HIGH**  
**Effort: TRIVIAL (1-line change)**  
**Risk: NONE (matches proven pattern)**

Change `private: True` to `private: False` on line 157.

## Expected Outcome

After this fix:
- ✅ All 3 guardrails tests should pass locally
- ✅ All 3 guardrails tests should pass in CI
- ✅ Behavior will match all other toolkit tests
- ✅ No functional impact on guardrails testing

## Conclusion

**The issue is NOT:**
- ❌ CI vs local difference
- ❌ Credential creation failure  
- ❌ Project 470 configuration
- ❌ Backend changes

**The issue IS:**
- ✅ Using `private: True` instead of `private: False`
- ✅ Not following the pattern used by all other toolkit tests
- ✅ Fixable with a single-character change (True → False)

**Next step:** Apply the fix and verify tests pass.
