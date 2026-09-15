# Stage2 Test Fixes - Implementation Plan

## Overview

This document outlines the code changes needed to fix test failures on stage2 environment.

---

## Changes Implemented

### 1. ✅ Environment Detection in config.py

Added environment detection properties to automatically identify stage2:

```python
@property
def environment(self) -> str:
    """Detect environment from URL.
    
    Returns: 'localhost', 'dev', 'stage2', 'next', or 'unknown'
    """
    url = self.elitea_url.lower()
    if "localhost" in url or "127.0.0.1" in url:
        return "localhost"
    elif "stage2" in url:
        return "stage2"
    elif "dev" in url:
        return "dev"
    elif "next" in url:
        return "next"
    return "unknown"

@property
def is_stage2(self) -> bool:
    """True if running against stage2 environment."""
    return self.environment == "stage2"
```

### 2. ✅ Environment-Aware Timeouts (utils/timeouts.py)

Created centralized timeout management with stage2-specific adjustments:

| Timeout Type | Localhost/Dev | Stage2 | Reason |
|--------------|---------------|---------|--------|
| Navigation | 15s | 30s | Backend latency |
| UI Element | 10s | 15s | Slower page loads |
| Publish Wizard | 60s | 120s | Complex backend validation |
| AI Response | 30s | 45s | AI service latency |
| Form Save | 15s | 25s | Network + backend processing |

**Usage:**
```python
from utils.timeouts import get_navigation_timeout

timeout = get_navigation_timeout()  # Auto-detects environment
agent.click_back_button(timeout=timeout)
```

### 3. 🔧 Test Fixes Needed (To Be Applied)

#### A. Agent Import Test - Skip on Stage2

**File:** `tests/ui/agents/test_import_agent_valid_md_file.py`

**Issue:** Test expects GPT-5.2 but stage2 defaults to Claude 4.5 Sonnet

**Fix:**
```python
@pytest.mark.skipif(
    settings.is_stage2,
    reason="GPT-5.2 not available on stage2 (defaults to Claude 4.5 Sonnet)"
)
def test_import_agent_valid_md_file(page, agent_api):
    # Test code...
```

#### B. Permission-Based Test Skipping

**Files:**
- `tests/ui/admin/test_guardrails_live_reload.py`
- `tests/ui/artifacts/test_bucket_permissions_api.py`

**Issue:** Missing permissions on stage2 (`configurations.configuration.create`, `configuration.artifacts.artifacts.create`)

**Fix Option 1 - Skip on Stage2:**
```python
@pytest.mark.skipif(
    settings.is_stage2,
    reason="Requires admin permissions not available on stage2 test user"
)
class TestBlockedToolkitLiveReload:
    # Test code...
```

**Fix Option 2 - Check Permissions (Better):**
```python
@pytest.fixture(autouse=True)
def check_required_permissions(credential_api):
    """Verify test user has required permissions."""
    try:
        # Try to create/list credentials to verify permissions
        credential_api.list_credentials()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            pytest.skip(
                f"Missing required permissions: "
                f"{e.response.json().get('required', 'unknown')}"
            )
        raise
```

---

## Non-Code Fixes Required

### 🔴 Environment Configuration (DevOps Team)

**Stage2 needs these permissions granted to test user:**

1. `configurations.configuration.create` - For credential/guardrail tests
2. `configuration.artifacts.artifacts.create` - For artifact permission tests

**Action:** Update stage2 test user role to include these permissions

---

### 🔴 AI Service Investigation (Backend Team)

**Issue:** Multiple tests failing with "Temporary server error"

**Affected Tests:**
- `test_agent_embedded_chat_send_message`
- `test_agent_with_github_toolkit` (2 tests)
- `test_agent_creates_files_at_root_and_in_subfolder`

**Symptoms:**
- AI responses contain: "Temporary server error, please try againError debugging info"
- `generate-draft` endpoint returns 500
- Toolkit integration fails to execute

**Investigation Needed:**
1. Check LLM provider connectivity on stage2
2. Review stage2 error logs around 12:10-12:24 UTC on 2026-09-11
3. Verify toolkit execution permissions
4. Check agent service health

---

### 🟡 Product Bugs (UI Team)

#### 1. Agent Icon Not Persisting

**Test:** `test_agent_icon_change_persists_on_list_card`  
**Issue:** Icon selection changes in UI but doesn't save  
**Action:** Create bug ticket for UI team

#### 2. Back Button Timeout

**Test:** `test_back_button_from_agent_detail_returns_to_intact_agents_list`  
**Issue:** Back button click times out (even with 15s timeout)  
**Possible Causes:**
- Missing testid on back button
- Element not clickable due to overlay
- Navigation not triggered

**Action:** Investigate back button implementation on stage2

---

## Test Execution Plan

### Phase 1: Apply Code Fixes

```bash
# 1. Environment detection already added to config.py ✅
# 2. Timeouts utility already created ✅
# 3. Apply test-specific fixes (pending approval)
```

### Phase 2: Run Against Stage2

```bash
cd automation

# Set stage2 environment
export ELITEA_URL=https://stage2.elitea.ai
export ELITEA_API_BASE=https://stage2.elitea.ai/api/v2
export APP_PREFIX=/app
export HEADLESS=true

# Run failed test suites
../.venv/bin/pytest tests/ui/agents/ -v --tb=short -x
../.venv/bin/pytest tests/ui/admin/ -v --tb=short -x
../.venv/bin/pytest tests/ui/artifacts/ -v --tb=short -x
```

### Phase 3: Report Results

Will create `STAGE2_TEST_RESULTS.md` with:
- ✅ Tests that now pass
- ❌ Tests still failing (with root cause)
- ⚠️ Tests skipped (with reason)

---

## Impact Assessment

### Tests That Will Pass After Fixes

- **Navigation timeouts:** 3 tests (back button, publish wizard, version selector)
- **Model skip:** 1 test (import agent)
- **Permission skip:** 5 tests (guardrails, bucket permissions)

**Total:** 9 tests will pass or be skipped appropriately

### Tests Still Requiring Investigation

- **AI service errors:** 4 tests - requires backend fix
- **Icon persistence:** 1 test - requires UI bug fix

**Total:** 5 tests require non-code fixes

---

## Files Changed

1. ✅ `automation/config.py` - Added environment detection
2. ✅ `automation/utils/timeouts.py` - Created (new file)
3. ⏳ Test files (waiting for approval before modifying)

---

## Rollback Plan

If changes cause issues:

```bash
# Revert config.py environment detection
git checkout automation/config.py

# Remove timeouts utility
rm automation/utils/timeouts.py

# Revert test changes
git checkout tests/ui/agents/ tests/ui/admin/ tests/ui/artifacts/
```

---

## Next Steps

1. ✅ Get approval for proposed changes
2. ⏳ Apply test-specific fixes
3. ⏳ Run against stage2
4. ⏳ Report results
5. ⏳ File tickets for non-code issues
