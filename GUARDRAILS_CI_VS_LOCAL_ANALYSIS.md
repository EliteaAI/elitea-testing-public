# Guardrails Tests: CI vs Local Analysis

**Date:** 2026-08-24  
**Question:** "It seems it works locally but not on CI? What is the issue?"  
**Answer:** ❌ **It does NOT work locally** - Same error in both environments

## Key Finding

**The guardrails tests fail with the EXACT same error in both CI and local execution:**

```
400 Client Error: Bad Request
Error: private_credential_not_found
credential_id: "guardrails_test_credential"
```

## Evidence

### Local Execution (2026-08-24 19:14)
```
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolkitLiveReload::test_blocked_toolkit_live_reload_case_insensitive
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolLiveReload::test_blocked_tool_live_reload_case_insensitive
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestSensitiveToolLiveReload::test_sensitive_tool_live_reload_case_insensitive

All 3 tests: 400 Bad Request - private_credential_not_found
```

### CI Execution (Run #32745668848, 2026-08-24 15:35)
```
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolkitLiveReload::test_blocked_toolkit_live_reload_case_insensitive
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolLiveReload::test_blocked_tool_live_reload_case_insensitive
ERROR tests/ui/admin/test_guardrails_live_reload.py::TestSensitiveToolLiveReload::test_sensitive_tool_live_reload_case_insensitive

All 3 tests: 400 Bad Request - private_credential_not_found
```

## Timeline & History

### August 21, 2026 - Tests Modified

**Commit `3cdb21f00` (13:01):** Added JIRA credential creation
- Added `create_jira_credential()` method to API client
- Updated guardrails tests to use JIRA toolkit instead of GitHub

**Commit `8f378972e` (14:04):** Removed blocked markers
- Removed `@pytest.mark.blocked` from all 3 tests
- Commit message claims: "2 of 3 tests passing locally"
- Switched from GitHub toolkit to JIRA toolkit to reduce parallel conflicts

### Current State (August 24, 2026)

**All 3 tests fail in both environments** with the credential issue.

## The Actual Problem

The tests fail **during fixture setup**, not during test execution:

```python
@pytest.fixture(scope="module")
def guardrails_test_credential(module_credential_api):
    # Step 1: Create JIRA credential
    cred = module_credential_api.create_jira_credential(
        display_name="guardrails_test_credential",
        ...
    )
    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

@pytest.fixture(scope="module")
def guardrails_test_toolkit(guardrails_test_credential, module_toolkit_api):
    # Step 2: Create toolkit using that credential
    toolkit_settings = {
        "jira_configuration": {
            "elitea_title": guardrails_test_credential["elitea_title"],
            "private": True,  # ← This is the problem
        },
        ...
    }
    toolkit = module_toolkit_api.create_toolkit(...)  # ← Fails here
```

**The issue:**
1. Credential is created successfully (no error from Step 1)
2. Toolkit creation immediately fails saying credential doesn't exist
3. This happens because `private: True` is set

## Why the Confusion?

The commit message from August 21 says "2 of 3 tests passing locally", but:

1. **That was 3 days ago** - Something changed in the environment or backend
2. **Project ID changed** - Tests originally ran against project 399 (testbot user), now running against project 470 (autotest_user_admin)
3. **Private credentials might behave differently** in project 470

## Root Cause: Private Credential Timing Issue

**Hypothesis:** When a private credential is created, it's not immediately available for toolkit creation in the same API session.

**Evidence:**
- ✅ Credential creation succeeds (fixture doesn't fail at Step 1)
- ❌ Toolkit creation immediately after fails (can't find credential)
- ⚠️ Error specifically mentions "private_credential_not_found"

**Possible causes:**
1. **Database propagation delay** - Private credentials need time to become available
2. **Session scope issue** - Private credentials might not be visible in the same transaction
3. **Project-specific behavior** - Project 470 might have different private credential rules than 399
4. **Backend change** - Something changed in dev.elitea.ai between August 21 and August 24

## Solutions to Try

### Option 1: Add Propagation Delay (Quick Fix)
```python
@pytest.fixture(scope="module")
def guardrails_test_toolkit(guardrails_test_credential, module_toolkit_api):
    import time
    time.sleep(3)  # Wait for credential to propagate
    # ... rest of fixture
```

### Option 2: Use Non-Private Credentials (Recommended)
```python
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": False,  # ← Change this
    },
    ...
}
```

**Rationale:** The tests are checking guardrails behavior (blocking/sensitive tools), not credential privacy. Using non-private credentials doesn't affect test validity.

### Option 3: Verify Credential After Creation
```python
@pytest.fixture(scope="module")
def guardrails_test_credential(module_credential_api):
    cred = module_credential_api.create_jira_credential(...)
    
    # Verify credential is retrievable
    max_retries = 5
    for attempt in range(max_retries):
        try:
            retrieved = module_credential_api.get_credential(cred["id"])
            if retrieved:
                break
        except:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise
    
    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}
```

### Option 4: Use Session-Scoped Credentials Instead of Module-Scoped
```python
@pytest.fixture(scope="session")  # ← Change from module
def guardrails_test_credential(...):
    # Created once at session start, should be available by the time tests run
```

## What Changed Between "Working" and "Not Working"?

**When it "worked" (Aug 21):**
- User: testbot@elitea.ai (or different user)
- Project: 399 (or different project)
- Possibly tested with non-private credentials initially

**Now (Aug 24):**
- User: autotest_user_admin
- Project: 470
- Using private credentials
- Same error in CI and local

## Recommendation

**Priority 1:** Try Option 2 (use `private: False`)
- Fastest fix
- Doesn't affect test validity
- Low risk

**Priority 2:** If private credentials are required for the test scenario, try Option 1 (add delay)
- Simple change
- May fix timing issue
- Can refine delay based on testing

**Priority 3:** Investigate backend behavior
- Check if dev.elitea.ai changed between Aug 21-24
- Verify private credential creation API behavior
- Check project 470 configuration

## Impact Assessment

**Current State:**
- ✅ Basic admin tests work (analytics, personal tokens)
- ❌ Guardrails tests fail in setup
- ⚠️ Tests are active (not marked as blocked) so they fail CI runs

**Impact:**
- **Severity:** Medium - Important guardrails functionality untested
- **Scope:** 3 tests affected, all in same fixture dependency chain
- **Urgency:** Medium - Not blocking other work, but should be fixed

## Next Steps

1. **Try Option 2** (private: False) first - 1-line change
2. **Test locally** to verify fix
3. **Push to CI** to verify in CI environment
4. **If that works:** Document the solution and close
5. **If that doesn't work:** Try Option 1 (add delay)

## Conclusion

**The question was based on a misconception:**  
The tests do NOT work locally - they fail with the exact same error in both environments.

**The real issue:**  
A private credential creation/visibility timing issue that affects both CI and local execution since August 24, 2026 (or possibly earlier).

**Best path forward:**  
Use non-private credentials unless the test specifically needs to verify private credential behavior.
