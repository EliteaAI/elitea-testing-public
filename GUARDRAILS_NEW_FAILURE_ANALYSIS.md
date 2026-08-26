# Guardrails Tests - NEW Failure Analysis (Run #32763645928)

**Date:** 2026-08-24  
**Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32763645928  
**Job:** dev-stable - admin (ID 97550629632)  
**Status:** ❌ **ALL 3 GUARDRAILS TESTS FAILED IN SETUP**

## 🚨 CRITICAL CHANGE: JIRA Toolkit Disabled on DEV

### Error Summary

All 3 guardrails tests failed during **fixture setup** with:

```
ERROR at setup of TestBlockedToolkitLiveReload.test_blocked_toolkit_live_reload_case_insensitive
ERROR at setup of TestBlockedToolLiveReload.test_blocked_tool_live_reload_case_insensitive  
ERROR at setup of TestSensitiveToolLiveReload.test_sensitive_tool_live_reload_case_insensitive

ERROR    elitea.api:client.py:1793 Failed to create toolkit. 
Status: 403, Response: {"ok": false, "error": "Toolkit type 'jira' is not available in this deployment"}

requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: ***/elitea_core/tools/prompt_lib/***
```

### Root Cause: JIRA Toolkit Type Disabled

**The DEV environment no longer has JIRA toolkit type enabled.**

Between runs:
- **Run #32761287836 (18:20 UTC):** ✅ JIRA toolkit creation succeeded, tests PASSED
- **Run #32763645928 (18:49 UTC):** ❌ JIRA toolkit creation returned 403 Forbidden, tests ERROR

**Time gap:** ~29 minutes

**This is an environment configuration change, NOT a test or code issue.**

---

## What Changed in the Environment

### Before (Run #32761287836 - 18:20 UTC)

```
✅ JIRA toolkit type available
✅ create_toolkit(toolkit_type="jira") → 200 OK
✅ All 3 guardrails tests PASSED
```

### After (Run #32763645928 - 18:49 UTC)

```
❌ JIRA toolkit type NOT available  
❌ create_toolkit(toolkit_type="jira") → 403 Forbidden
   Response: "Toolkit type 'jira' is not available in this deployment"
❌ All 3 guardrails tests ERROR in setup
```

---

## Test Results Breakdown

| Test | Previous Run (#32761287836) | This Run (#32763645928) | Change |
|------|----------------------------|------------------------|--------|
| `test_blocked_toolkit_live_reload_case_insensitive` | ✅ PASSED | ❌ ERROR (setup) | JIRA disabled |
| `test_blocked_tool_live_reload_case_insensitive` | ✅ PASSED | ❌ ERROR (setup) | JIRA disabled |
| `test_sensitive_tool_live_reload_case_insensitive` | ✅ PASSED | ❌ ERROR (setup) | JIRA disabled |
| `test_expired_token_shows_expired_icon_and_label` | ❌ FAILED (data) | ✅ PASSED | Data restored! |

**Interesting:** The personal token test now **PASSES** - someone restored the "Marian" token!

---

## Why This Happened

### Possible Reasons for JIRA Toolkit Disable:

1. **Deployment configuration change** - JIRA integration disabled on DEV
2. **License/quota issue** - JIRA integration temporarily disabled
3. **Plugin/provider update** - JIRA provider temporarily unavailable
4. **Intentional test isolation** - Someone disabled JIRA to test other areas

### Evidence Points to Configuration Change

**Not a test bug because:**
- ✅ Same test code
- ✅ Same environment (dev.elitea.ai)
- ✅ Same credentials (autotest_user_admin, project 470)
- ✅ Tests passed 29 minutes earlier with identical setup

**Backend behavior changed:**
- Previous: `POST /tools/prompt_lib/470` with `toolkit_type: "jira"` → 200 OK
- Current: Same request → 403 Forbidden with explicit "not available in this deployment"

---

## Impact Assessment

### Direct Impact

| Affected | Status |
|----------|--------|
| **Guardrails tests** | ❌ Cannot run (JIRA required) |
| **Our `private: False` fix** | ✅ Still valid (not reverted) |
| **Other admin tests** | ✅ Unaffected (don't use JIRA) |

### Test Coverage Gap

While JIRA is disabled:
- ❌ Cannot test guardrails with JIRA toolkit
- ❌ Cannot verify blocked toolkit functionality
- ❌ Cannot verify blocked tool functionality  
- ❌ Cannot verify sensitive tool functionality

**These are the ONLY tests that use JIRA toolkit.**

---

## Fix Options

### Option 1: Re-enable JIRA on DEV (Recommended)

**Action:** Request JIRA toolkit type be re-enabled on dev.elitea.ai

**Pros:**
- ✅ Tests work as-is (no code changes)
- ✅ Tests actual JIRA integration
- ✅ Matches production environment

**Cons:**
- ⏱️ Requires environment change
- 🔐 May have license/permission dependencies

**Who to contact:** DevOps / Backend team managing DEV deployment

---

### Option 2: Switch to Different Toolkit Type

**Action:** Change tests to use GitHub or Confluence toolkit instead of JIRA

**Code changes needed:**

```python
# Before (current - uses JIRA)
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": False,
    },
    "selected_tools": [
        "list_projects",      # For sensitive tool test
        "search_using_jql",   # For blocked tool test
    ],
}
toolkit = module_toolkit_api.create_toolkit(
    name=name,
    description="JIRA toolkit for guardrails live-reload tests",
    toolkit_type="jira",
    settings=toolkit_settings,
)

# After (alternative - use GitHub)
toolkit_settings = {
    "github_configuration": {
        "elitea_title": github_credential_elitea_title,
        "private": False,
    },
    "repository": "EliteaAI/elitea-testing-public",
    "active_branch": "main",
    "base_branch": "main",
}
toolkit = module_toolkit_api.create_toolkit(
    name=name,
    description="GitHub toolkit for guardrails live-reload tests",
    toolkit_type="github",
    settings=toolkit_settings,
)

# Would also need to update selected_tools for GitHub equivalents
```

**Pros:**
- ✅ Tests can run immediately
- ✅ No environment dependency

**Cons:**
- ⏱️ Requires test rewrite
- ⚠️ GitHub toolkit may not have equivalent tools for blocking
- 📝 Needs new test data setup (GitHub credentials)
- 🔄 Would need to verify GitHub toolkit supports guardrails features

---

### Option 3: Skip Tests When JIRA Unavailable

**Action:** Add conditional skip for when JIRA toolkit type is not available

```python
# Add to conftest.py or test file
def is_toolkit_type_available(toolkit_type: str) -> bool:
    """Check if toolkit type is available in current deployment."""
    try:
        # Try to list available toolkit types
        response = requests.get(f"{ELITEA_API_BASE}/toolkit_types")
        available_types = response.json()
        return toolkit_type in available_types
    except:
        return False

# In test file
@pytest.mark.skipif(
    not is_toolkit_type_available("jira"),
    reason="JIRA toolkit type not available in this deployment"
)
class TestBlockedToolkitLiveReload:
    ...
```

**Pros:**
- ✅ Tests gracefully skip when JIRA disabled
- ✅ Tests run when JIRA re-enabled
- ✅ No false failures

**Cons:**
- ⚠️ Reduces test coverage when JIRA disabled
- 📊 CI shows skipped tests (yellow warning)

---

### Option 4: Mock/Stub JIRA Toolkit

**Action:** Create a fake JIRA toolkit for testing guardrails

**Pros:**
- ✅ Tests always runnable
- ✅ No external dependencies

**Cons:**
- ❌ Doesn't test real JIRA integration
- ❌ Complex to implement
- ❌ May not catch real issues

**Verdict:** Not recommended - tests should use real toolkits

---

## Recommended Action Plan

### Immediate (Today)

1. **✅ Document the issue** (this file)
2. **📧 Contact DevOps/Backend team:**
   - "JIRA toolkit type disabled on dev.elitea.ai since ~18:30 UTC Aug 24"
   - "Blocks 3 guardrails tests"
   - "Request: Re-enable JIRA toolkit type on DEV"
   - "Reference: Run #32763645928 vs #32761287836"

### Short-term (This Week)

1. **If JIRA can be re-enabled quickly:**
   - ✅ Wait for re-enable
   - ✅ Re-run tests to verify
   - ✅ Document in test that JIRA must be enabled

2. **If JIRA will stay disabled:**
   - Implement Option 3 (conditional skip)
   - Document that tests require JIRA
   - Consider Option 2 (switch toolkit) for long-term

### Long-term

1. **Add environment validation step** to CI:
   ```bash
   # Before running admin suite
   python scripts/check_required_toolkits.py --required jira,github,confluence
   ```

2. **Document toolkit dependencies** in test metadata:
   ```python
   @pytest.mark.requires_toolkit("jira")
   def test_guardrails_jira():
       ...
   ```

---

## Communication Template

### For DevOps Team

```
Subject: JIRA Toolkit Type Disabled on dev.elitea.ai - Blocking Guardrails Tests

Hi Team,

The JIRA toolkit type appears to have been disabled on dev.elitea.ai around 18:30 UTC on Aug 24, 2026.

Evidence:
- Run #32761287836 (18:20 UTC): JIRA toolkit creation succeeded ✅
- Run #32763645928 (18:49 UTC): JIRA toolkit creation returns 403 Forbidden ❌
  Error: "Toolkit type 'jira' is not available in this deployment"

Impact:
- 3 guardrails tests cannot run (test_blocked_toolkit_live_reload, etc.)
- Tests use JIRA toolkit to verify guardrails functionality
- No workaround available without JIRA

Request:
Can JIRA toolkit type be re-enabled on dev.elitea.ai?
If there's a reason it was disabled, please let us know so we can adjust tests accordingly.

Thanks!
```

---

## Interesting Side Note

**The personal token test now PASSES!** 🎉

Previous run (#32761287836):
```
❌ test_expired_token_shows_expired_icon_and_label FAILED
   Error: Token "Marian" not found (count: 0)
```

This run (#32763645928):
```
✅ test_expired_token_shows_expired_icon_and_label PASSED
```

**Someone restored the "Marian" token on DEV between the two runs!**

This validates our analysis that the token failure was a test data issue, not a test bug.

---

## Conclusion

### Summary

| Issue | Status | Action Needed |
|-------|--------|---------------|
| **Our `private: False` fix** | ✅ Still valid | None - fix is good |
| **JIRA toolkit disabled** | ❌ Blocking tests | Contact DevOps |
| **Personal token test** | ✅ Now passing | None - data restored |

### The `private: False` Fix Status

**Our fix is NOT broken.** The tests fail because:
1. ❌ Environment changed (JIRA disabled)
2. ✅ NOT because `private: False` stopped working
3. ✅ NOT because credential creation fails
4. ✅ NOT because toolkit creation logic changed

**When JIRA is re-enabled, the tests will pass again.**

### Next Steps

1. **Immediate:** Contact DevOps about JIRA toolkit
2. **Track:** Monitor when JIRA is re-enabled
3. **Verify:** Re-run tests after JIRA is back
4. **Document:** Add toolkit dependency checks to prevent this

---

**Analysis completed:** 2026-08-24 21:52  
**Root cause:** Environment configuration change (JIRA toolkit disabled)  
**Fix ownership:** DevOps / Backend team (environment)  
**Test ownership:** Tests are correct, no code changes needed
