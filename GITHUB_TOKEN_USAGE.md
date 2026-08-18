# GitHub Token Usage Analysis

**Date:** 2026-08-17  
**Variable:** `GIT_HUB_TOKEN` (in `.env.test`)  
**Config:** `settings.git_hub_token` (in `automation/config.py`)

---

## Summary

**Total tests using GitHub fixtures:** 11+ tests across 8 files  
**Tests that are BLOCKED:** 2  
**Tests that are NOT BLOCKED:** 9+

---

## The Variable

### Environment Variable:
```bash
# In .env.test (symlink to ../../.env.test)
GIT_HUB_TOKEN=ghp_xxxxxxxxxxxxx
```

### Config Mapping:
```python
# automation/config.py line 97
git_hub_token: str = ""  # Loaded from GIT_HUB_TOKEN env var
```

### Usage in Fixtures:
```python
# automation/fixtures/data_fixtures.py lines 1378-1411
@pytest.fixture
def github_credential(credential_api: CredentialAPI, request):
    """Create a GitHub API credential and yield its metadata.
    
    Skips the test if GITHUB_TOKEN is not set in the environment.
    """
    if not settings.git_hub_token:
        pytest.skip("GIT_HUB_TOKEN not set in .env.test")
    
    # Creates credential in Elitea using the token
    cred = credential_api.create_github_credential(
        display_name=name,
        base_url=settings.github_base_url,
        token=settings.git_hub_token,  # ← The token goes here
    )
    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}
```

---

## Tests Using GitHub Fixtures

### Blocked Tests (2)

#### 1. test_agent_with_toolkit_executes_in_chat ❌
**File:** `tests/ui/chat/test_agent_with_toolkit_chat.py`  
**Fixture:** `github_toolkit` → `github_credential`  
**Status:** BLOCKED - 401 Bad credentials  
**Why blocked:** Token is invalid/expired

#### 2. test_github_toolkit_test_settings ❌
**File:** `tests/ui/toolkits/test_github_toolkit.py`  
**Fixture:** `github_toolkit` → `github_credential`  
**Status:** BLOCKED (reason unverified in this investigation)

---

### Non-Blocked Tests (9+)

#### Tests in test_agent_with_github_toolkit.py ✅
**File:** `tests/ui/agents/test_agent_with_github_toolkit.py`  
**Tests:**
1. `test_add_toolkit_to_agent`
2. `test_remove_toolkit_from_agent`
3. `test_agent_chat_with_github_toolkit`

**Fixture:** `github_toolkit` → `github_credential`  
**Status:** NOT BLOCKED (may skip if token missing)

#### Tests in test_github_toolkit.py ✅
**File:** `tests/ui/toolkits/test_github_toolkit.py`  
**Tests:**
1. `test_create_github_credential` - Creates credential via UI
2. `test_create_github_toolkit` - Creates toolkit via UI
3. `test_chat_with_github_toolkit` - Tests chat with toolkit

**Fixture:** Some use fixtures, some create via UI  
**Status:** NOT BLOCKED

#### Pipeline Tests ✅
**Files:**
- `tests/ui/pipelines/test_pipeline_create_full_details_persist.py`
- `tests/ui/pipelines/test_pipeline_toolkit_node_config_and_input_mapping.py`
- `tests/ui/pipelines/test_pipeline_custom_node_configuration.py`

**Tests:**
1. `test_create_pipeline_full_details_persist_after_reload`
2. `test_toolkit_node_config_and_input_mapping`
3. `test_custom_node_configuration`

**Fixture:** `github_toolkit` / `github_toolkit_with_selected_tools`  
**Status:** NOT BLOCKED

#### Other Tests ✅
**Files:**
- `tests/ui/toolkits/test_credential_create.py`
  - `test_create_github_credential_via_sidebar_button`
- `tests/ui/agents/test_agent_build_with_ai.py`
  - `test_selected_suggested_resources_attached_and_non_selected_absent`

**Status:** NOT BLOCKED

---

## Why Some Tests Are Blocked and Others Are Not

### Hypothesis:

The **non-blocked tests either:**

1. **Skip gracefully when token is missing:**
   ```python
   if not settings.git_hub_token:
       pytest.skip("GIT_HUB_TOKEN not set in .env.test")
   ```
   These tests show as SKIPPED, not FAILED.

2. **Don't actually call the GitHub API:**
   - Tests that create credential/toolkit via UI only
   - Tests that don't execute toolkit actions
   - Tests that use mocked/invalid credentials intentionally

3. **Have valid credentials in CI environment:**
   - CI may have a different `.env.test` with valid token
   - Local environment token is invalid/expired

### The Blocked Tests:

Both blocked tests **actually execute GitHub API calls:**

1. **test_agent_with_toolkit_executes_in_chat:**
   - Creates agent with toolkit
   - Sends chat message that triggers `list_branches_in_repo`
   - **GitHub API is called** → 401 Bad credentials

2. **test_github_toolkit_test_settings:**
   - Tests the "Test Settings" feature in toolkit UI
   - Likely clicks "Run Tool" which calls GitHub API
   - Would fail with 401 if token invalid

---

## Investigation: Why Aren't Other Tests Failing?

Let me check if they're being skipped:

### Check Test Results in CI

From workflow run logs, we'd expect to see:

```
# Tests that skip gracefully:
tests/ui/agents/test_agent_with_github_toolkit.py::test_add_toolkit_to_agent SKIPPED
tests/ui/agents/test_agent_with_github_toolkit.py::test_agent_chat_with_github_toolkit SKIPPED

# Tests that are blocked:
tests/ui/chat/test_agent_with_toolkit_chat.py::test_agent_with_toolkit_executes_in_chat DESELECTED [blocked]
tests/ui/toolkits/test_github_toolkit.py::test_github_toolkit_test_settings DESELECTED [blocked]
```

**Key Difference:**
- **SKIPPED** = Test ran but skipped due to missing precondition (token)
- **DESELECTED** = Test marked as blocked, never attempted

---

## Token Requirements

### What the token needs:

**Scopes:**
- `repo` (full control of private repositories)
  - Required for: `list_branches_in_repo`, `get_repository_info`, etc.

**Repository Access:**
- Must have access to: `EliteaAI/elitea-testing-public`
- Configured in: `settings.git_repo = "EliteaAI/elitea-testing"`

### Where it's used:

```python
# 1. Create credential in Elitea
credential_api.create_github_credential(
    token=settings.git_hub_token
)

# 2. Credential is linked to toolkit
toolkit_api.create_github_toolkit(
    credential_elitea_title=github_credential["elitea_title"],
    repository=settings.git_repo,
)

# 3. Toolkit executes GitHub API calls
# (via Elitea backend → GitHub API)
```

---

## How to Fix

### Option 1: Update Token (Recommended)

```bash
# 1. Generate new GitHub PAT
# https://github.com/settings/tokens/new
# Scopes: repo (full)
# Expiration: 90 days recommended

# 2. Update .env.test
cd /Users/Aliaksei_Breilian/PycharmProjects/elitea_local
echo "GIT_HUB_TOKEN=ghp_xxxxxxxxxxxxx" >> .env.test

# 3. Verify
grep GIT_HUB_TOKEN .env.test

# 4. Test locally
cd elitea-testing-public/automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/chat/test_agent_with_toolkit_chat.py::TestAgentWithToolkitInChat::test_agent_with_toolkit_executes_in_chat \
  -v
```

### Option 2: Keep Tests Blocked (Current State)

If GitHub token management is too complex:
- Keep 2 tests marked as blocked
- They'll be skipped in CI
- Update documentation noting token requirement

---

## Impact Assessment

### If Token Is Fixed:

**Unblocked:** 2 tests
- test_agent_with_toolkit_executes_in_chat (P0)
- test_github_toolkit_test_settings

**Still Skipped:** 0 (all GitHub tests would run)

**Blocked count:** 17 → 15

### If Token Stays Invalid:

**Current State:**
- 2 tests blocked
- Other tests either skip or don't call API
- No false failures in CI

**Risk:**
- Reduced coverage of GitHub toolkit functionality
- P0 test not running (agent with toolkit execution)

---

## Recommendation

**Fix the token** ✅

**Reasons:**
1. `test_agent_with_toolkit_executes_in_chat` is **P0** (critical priority)
2. Only 2 tests blocked by this issue
3. Easy fix (just update environment variable)
4. Improves coverage of important toolkit functionality

**How:**
1. Generate new GitHub PAT with `repo` scope
2. Update `.env.test` 
3. Unmark the 2 tests as blocked
4. Verify they pass locally
5. Commit changes

---

## Related Files

**Fixtures:**
- `automation/fixtures/data_fixtures.py` - github_credential, github_toolkit fixtures
- `automation/conftest.py` - fixture registration

**Config:**
- `automation/config.py` - git_hub_token setting
- `automation/.env.test` - GIT_HUB_TOKEN value (symlink to ../../.env.test)

**Tests:**
- 8 test files use GitHub fixtures
- 11+ individual test functions
- 2 currently blocked

**Documentation:**
- `BLOCKED_TESTS_INVESTIGATION.md` - Investigation of the 2 blocked tests
- `automation/CLAUDE.md` - Documents toolkit tokens as optional
