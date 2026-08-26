# Guardrails Live Reload Tests - Results

**Date:** 2026-08-24  
**Environment:** dev.elitea.ai  
**User:** autotest_user_admin  
**Project ID:** 470  

## Test Summary

| Test | Status | Issue |
|------|--------|-------|
| `test_blocked_toolkit_live_reload_case_insensitive` | ❌ ERROR | Setup failed - credential not found |
| `test_blocked_tool_live_reload_case_insensitive` | ❌ ERROR | Setup failed - credential not found |
| `test_sensitive_tool_live_reload_case_insensitive` | ❌ ERROR | Setup failed - credential not found |

**Overall:** 0/3 passed - All tests failed during fixture setup

## Root Cause

The tests require a JIRA credential to be created as a fixture before running. The credential creation failed with:

```
400 Client Error: Bad Request for url: https://dev.elitea.ai/api/v2/elitea_core/tools/prompt_lib/470

Error body: {
  "ok": false,
  "error": [{
    "type": "value_error",
    "loc": ["settings", "jira_configuration"],
    "msg": "Value error, {\"error_type\": \"private_credential_not_found\", \"credential_id\": \"guardrails_test_credential\"}"
  }]
}
```

## Analysis

### What These Tests Do

The guardrails live reload tests verify that guardrails configuration changes take effect immediately without requiring application restart:

1. **Blocked Toolkit Test:** Verifies that blocking an entire toolkit (JIRA) prevents its use
2. **Blocked Tool Test:** Verifies that blocking a specific tool (search_using_jql) prevents its use
3. **Sensitive Tool Test:** Verifies that marking a tool as sensitive requires confirmation before use

### Test Requirements

**Fixtures (module-scoped - created once for all tests):**
1. `guardrails_test_credential` - Creates a JIRA credential named "guardrails_test_credential"
2. `guardrails_test_toolkit` - Creates a JIRA toolkit using that credential with 2 tools:
   - `list_projects` (for sensitive tool test)
   - `search_using_jql` (for blocked tool test)

**Environment Requirements:**
```bash
JIRA_USERNAME=aliaksei_breilian@epam.com
JIRA_API_KEY=ATATT3xFfGF...
JIRA_BASE_URL=https://epamelitea.atlassian.net
```

✅ These are present in `.env.test`

### The Problem

The fixture sequence is:
1. ✅ `guardrails_test_credential` fixture creates JIRA credential
2. ❌ `guardrails_test_toolkit` fixture tries to create toolkit **referring to that credential**
3. ❌ API returns 400 saying `private_credential_not_found`

**Possible causes:**

1. **Credential not persisted:** The credential was created but not properly persisted in project 470
2. **Private credential scope issue:** Private credentials might not be accessible in the same API call
3. **Timing issue:** The credential needs time to propagate before toolkit creation
4. **Project 470 specific issue:** This project might have different credential visibility rules

## Credential Details

**From fixture code:**
```python
name = "guardrails_test_credential"
cred = module_credential_api.create_jira_credential(
    display_name=name,
    base_url=settings.jira_base_url,
    username=settings.jira_username,
    api_key=settings.jira_api_key,
    elitea_title=name,
)
```

**Toolkit creation:**
```python
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],  # "guardrails_test_credential"
        "private": True,
    },
    "selected_tools": ["list_projects", "search_using_jql"],
}
```

The toolkit references the credential by `elitea_title` and marks it as `private: True`.

## Cleanup Notes

The test attempted cleanup before running (good practice):
```
[CLEANUP] Running guardrails cleanup BEFORE tests
[CLEANUP] Starting guardrails cleanup...
[CLEANUP] Navigated to guardrails page
[CLEANUP] Cleaning up blocked toolkits
[CLEANUP] Currently blocked toolkits: []
[CLEANUP] Checking toolkit 'jira': blocked=False
[CLEANUP] Checking toolkit 'JIRA': blocked=False
[CLEANUP] Checking toolkit 'Jira': blocked=False
```

Cleanup found no existing blocked toolkits, which is good.

Some sensitive tool cleanup warnings (timeouts) but these are non-blocking:
```
[CLEANUP] Could not remove sensitive tool search_using_jql: Timeout 5000ms
[CLEANUP] Could not remove sensitive tool list_projects: Timeout 5000ms
```

These timeouts suggest the sensitive tools section might not exist yet, which is expected for a clean state.

## Recommendations

### Option 1: Debug Credential Creation
1. Run credential creation manually via API
2. Verify it shows up in the UI under Credentials
3. Check if it can be used by a toolkit creation API call
4. Investigate why `private: True` might be causing issues

### Option 2: Use Non-Private Credential
Try modifying the fixture to use `private: False`:
```python
toolkit_settings = {
    "jira_configuration": {
        "elitea_title": guardrails_test_credential["elitea_title"],
        "private": False,  # Changed from True
    },
    ...
}
```

### Option 3: Add Delay Between Fixture Steps
Some systems need time for credentials to propagate:
```python
@pytest.fixture(scope="module")
def guardrails_test_toolkit(guardrails_test_credential, module_toolkit_api):
    import time
    time.sleep(2)  # Wait for credential to propagate
    # ... rest of fixture
```

### Option 4: Check Project 470 Configuration
Verify that project 470 allows private credentials and JIRA integrations.

## Test Design Notes

**Good practices observed:**
- ✅ Module-scoped fixtures (shared across all 3 tests)
- ✅ Pre-test cleanup to ensure clean state
- ✅ Careful tool selection to avoid parallel execution conflicts
- ✅ Proper error handling and logging

**Potential improvements:**
- Consider checking if credential exists before creating
- Add explicit credential verification step after creation
- Add retry logic for credential/toolkit creation

## Comparison with Other Tests

**Other admin tests that PASSED:**
- `test_analytics_page_default_load` ✅
- `test_personal_tokens_page_layout_and_components` ✅

**Why those work but guardrails don't:**
- Analytics and Personal Tokens tests don't require external credentials
- They only need admin user authentication
- No JIRA integration involved

## Next Steps

1. **Investigate credential API behavior** in project 470
2. **Test credential creation manually** via Elitea UI or API
3. **Check if private credentials are supported** in this environment
4. **Consider using a simpler test fixture** that doesn't require external credentials
5. **Verify JIRA credentials are valid** and can connect to the configured instance

## Related Files

- Test file: `tests/ui/admin/test_guardrails_live_reload.py`
- API client: `api/client.py` (lines 1794: `create_toolkit`)
- Credential API: `api/client.py` (JIRA credential creation)

## Status

**Blocked:** These tests cannot run until the credential/toolkit fixture setup issue is resolved.

**Impact:** Medium - These tests verify important guardrails functionality, but other admin tests pass successfully.

**Priority:** P2 - Should be fixed but not blocking other test execution.
