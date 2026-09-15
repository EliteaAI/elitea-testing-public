# Stage2 Test Failure Analysis - Run #34597349245

**Date:** 2026-09-11  
**Branch:** aqa_main_release_2.0.6  
**Environment:** stage2.elitea.ai  
**Overall Status:** ❌ FAILED (3/3 test jobs failed)

---

## Executive Summary

**Root Causes Identified:**

1. **Permission Issues (Critical)** - 403 Forbidden errors for credentials/artifacts API operations
2. **AI Service Errors** - "Temporary server error" affecting agent chat tests  
3. **Timeout Issues** - UI navigation timeouts (back button, publish wizard)
4. **Model Mismatch** - Agent import test expects GPT-5.2 but gets Claude 4.5 Sonnet
5. **Icon Change Bug** - Agent icon selection not persisting

---

## Failure Breakdown by Job

### 1. Agents Job (30 tests / 9 failed)

| Test | Failure Type | Root Cause |
|------|-------------|------------|
| `test_agent_embedded_chat_send_message` | Assertion | AI returns "Temporary server error" instead of "PONG" |
| `test_agent_icon_management` | Assertion | Icon selection doesn't persist (UI bug) |
| `test_agent_publish_unpublish_version` | Timeout | Publish wizard "Preparation" step times out (30s) |
| `test_agent_version_selector_order` | Timeout | Version selector timeout (60s) |
| `test_agent_with_github_toolkit` (2 tests) | Assertion | AI returns "Temporary server error" or just "Error debugging info" |
| `test_build_with_ai_skill_from_agent` | Assertion | `generate-draft` API returns 500 error |
| `test_import_agent_valid_md_file` | Assertion | Model mismatch - expects GPT-5.2, gets Claude 4.5 Sonnet |
| `test_back_button_from_agent_detail` | Timeout | Back button click times out (10s) |

**Pattern:** 
- **3 tests** - AI service failures ("Temporary server error")
- **3 tests** - UI timeouts (back button, publish wizard)
- **2 tests** - Data/config mismatches (model, icon)
- **1 test** - Backend API error (500)

### 2. Admin Job (7 tests / 4 failed)

| Test | Failure Type | Root Cause |
|------|-------------|------------|
| `test_blocked_toolkit_live_reload` | ERROR (403) | Permission denied: `configurations.configuration.create` |
| `test_blocked_tool_live_reload` | ERROR (403) | Permission denied: `configurations.configuration.create` |
| `test_sensitive_tool_live_reload` | ERROR (403) | Permission denied: `configurations.configuration.create` |
| `test_personal_token_create_and_verify` | Assertion | Expected count '1' (expired token not showing) |

**Pattern:**  
- **3 tests** - Permission errors (missing `configurations.configuration.create` permission)
- **1 test** - UI assertion failure

### 3. Artifacts Job (20 tests / 3 failed)

| Test | Failure Type | Root Cause |
|------|-------------|------------|
| `test_agent_creates_files_at_root_and_in_subfolder` | Assertion | 0 file cards found (expected 6) - Agent didn't create files |
| `test_no_access_permission_blocks_all_api_operations` | ERROR (403) | Permission denied: `configuration.artifacts.artifacts.create` |
| `test_read_only_permission_allows_get_blocks_write_operations` | ERROR (403) | Permission denied: `configuration.artifacts.artifacts.create` |

**Pattern:**  
- **2 tests** - Permission errors (missing `configuration.artifacts.artifacts.create`)
- **1 test** - Agent execution failure (files not created)

---

## Root Cause Analysis

### 🔴 **Critical Issue #1: Missing Permissions on Stage2**

**Affected Tests:** 5 tests (3 admin, 2 artifacts)

**Error Message:**
```json
{
  "ok": false,
  "error": "access_denied",
  "required": ["configurations.configuration.create"],
  "mode": "default",
  "project_id": null,
  "current_permissions": []
}
```

**Missing Permissions:**
- `configurations.configuration.create` (for credentials/guardrails tests)
- `configuration.artifacts.artifacts.create` (for artifact permission tests)

**Impact:** Tests that work on DEV fail on STAGE2 due to stricter permissions

**Fix Required:** Environment configuration update (not test code)

---

### 🔴 **Critical Issue #2: AI Service Instability**

**Affected Tests:** 4 tests (agents)

**Symptoms:**
- "Temporary server error, please try againError debugging info"
- Agent responses empty or contain only error messages
- `generate-draft` API returns 500

**Impact:** Agent chat functionality unreliable on STAGE2

**Fix Required:** Backend investigation needed

---

### 🟡 **Issue #3: UI Timeouts**

**Affected Tests:** 3 tests

**Symptoms:**
- Back button click: 10s timeout
- Publish wizard preparation step: 30-60s timeout

**Possible Causes:**
- Network latency to STAGE2
- Backend processing delays
- Missing/slow-loading UI elements

**Fix Required:** Investigate backend performance + increase timeouts for STAGE2

---

### 🟡 **Issue #4: Configuration Mismatches**

**Affected Tests:** 2 tests

**Problems:**
1. **Model mismatch:** Agent import fixture uses GPT-5.2, but STAGE2 defaults to Claude 4.5 Sonnet
2. **Icon persistence:** Icon selection doesn't save/persist (UI bug)

**Fix Required:**  
- Model: Update fixture or skip test on STAGE2
- Icon: UI bug - needs product fix

---

## Recommended Actions

### Immediate (Block STAGE2 deployment)

1. ✅ **Grant missing permissions** to test user on STAGE2:
   - `configurations.configuration.create`
   - `configuration.artifacts.artifacts.create`

2. ✅ **Investigate AI service errors** on STAGE2:
   - Check LLM provider connectivity
   - Review error logs for "Temporary server error"
   - Verify `generate-draft` endpoint

### Short-term (Fix before next test run)

3. **Increase timeouts for STAGE2 environment:**
   ```python
   # In conftest.py or stage2-specific config
   if settings.env == "stage2":
       NAVIGATION_TIMEOUT = 30_000  # was 10_000
       PUBLISH_WIZARD_TIMEOUT = 90_000  # was 60_000
   ```

4. **Fix agent icon persistence bug** (UI team)

5. **Update agent import fixture** to use stage2-available model OR skip on stage2:
   ```python
   @pytest.mark.skipif(
       settings.env == "stage2",
       reason="GPT-5.2 not available on stage2"
   )
   ```

### Long-term

6. **Environment parity:** Ensure STAGE2 permissions match DEV for test users
7. **Test stability:** Add retries for AI-dependent tests
8. **Monitoring:** Add health checks for AI service before test runs

---

## Test Run Against Stage2

Will execute after fixes are confirmed ready.

**Test Command:**
```bash
cd automation
ELITEA_URL=https://stage2.elitea.ai \
ELITEA_API_BASE=https://stage2.elitea.ai/api/v2 \
APP_PREFIX=/app \
HEADLESS=true \
../.venv/bin/pytest tests/ui/agents/ tests/ui/admin/ tests/ui/artifacts/ \
  -v --tb=short -x
```

---

## Files Changed

None yet - waiting for approval before applying fixes.

---

## Next Steps

1. ✅ Review this analysis
2. ⏳ Get approval for proposed fixes
3. ⏳ Apply fixes (code changes + env config)
4. ⏳ Test against stage2
5. ⏳ Report results
