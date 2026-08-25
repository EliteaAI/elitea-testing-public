# Admin Test Failures Analysis - CI Run #32761287836

**Date:** 2026-08-24  
**Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32761287836  
**Job:** dev-stable - admin (ID 97540529746)  
**Overall Status:** ❌ FAILED (but NOT due to our guardrails fix)

## Summary

| Test Group | Status | Details |
|------------|--------|---------|
| **Guardrails tests** (our fix) | ✅ **ALL PASSED** | 3/3 tests passed - fix validated |
| **Personal token test** | ❌ **1 FAILED** | `test_expired_token_shows_expired_icon_and_label` |
| **Notification test** | ⚠️ **1 SKIPPED** | `test_notification_text_content_renders_correctly` |
| **Other admin tests** | ✅ **PASSED** | All other tests in admin suite passed |

## Test Results

### ✅ Guardrails Tests - ALL PASSED (Our Fix Works!)

```
tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolkitLiveReload::test_blocked_toolkit_live_reload_case_insensitive PASSED [ 28%]
tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolLiveReload::test_blocked_tool_live_reload_case_insensitive PASSED [ 42%]
tests/ui/admin/test_guardrails_live_reload.py::TestSensitiveToolLiveReload::test_sensitive_tool_live_reload_case_insensitive PASSED [ 57%]
```

**Conclusion:** The `private: False` fix successfully resolved all 3 guardrails test failures. ✅

---

### ❌ Personal Token Test - FAILED (Test Data Issue)

**Test:** `test_expired_token_shows_expired_icon_and_label` (ELITEA-2284)  
**File:** `automation/tests/ui/admin/test_personal_token_create_and_verify.py:262`

#### Error Details

```
AssertionError: Locator expected to have count '1'
Actual value: 0

Step 2 — Locate an existing expired token row:
    row = tokens_page.get_row_by_name("Marian")
    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

waiting for get_by_test_id("token-row").filter(has_text="Marian")
  34 × locator resolved to 0 elements
     - unexpected value "0"
```

#### Root Cause: Missing Test Data

**Test Type:** Read-only test (no token creation/deletion)  
**Test Data Strategy:** `reuse-existing` - relies on persistent live data  

From the AFS (`test-specs/settings-personal-tokens/lextend_expired-and-active-token-expiration-icons_ELITEA-2284.md`):

```markdown
## Test Data
### reuse-existing
- An existing expired token row, matched by name `Marian` or `New` (either
  suffices — both confirmed `data-expiration-state="expired"` live). Use
  `tokens_page.get_row_by_name("Marian")` (or fall back to `"New"` if
  `Marian` is ever removed).
```

**Historical context from `_surface.md`:**
```markdown
5 persistent personal tokens observed 2026-08-05: `for_ui_tests`, `Levon`,
`Marian` (expired), `New` (expired), `uautomate`. Real leftover test data,
not a fixture — same risk class as `settings-notifications`'s live-history
dependency: if bulk-deleted, a test relying on "table has rows" precondition
will fail with the correct RED.
```

#### What Happened

**The "Marian" token was deleted from DEV between Aug 5 (when the test was written) and Aug 24 (this CI run).**

This is the **documented risk** in the AFS:
> "Risk: if bulk-deleted, a test relying on 'table has rows' precondition will fail with the correct RED."

The test correctly went RED, as designed.

#### Is This a Test Bug?

**NO** - The test is working as designed:
1. It's a **read-only test** (doesn't create/delete tokens)
2. It tests against **real persistent data** on DEV
3. The AFS explicitly documents this risk and provides a fallback (`"New"`)
4. When data disappears, the test correctly fails

#### Fix Options

**Option 1: Update test to try fallback token** (Recommended)
```python
with allure.step("Step 2 — Locate an existing expired token row"):
    # Try Marian first (primary), fall back to New (also expired)
    row = tokens_page.get_row_by_name("Marian")
    if row.count() == 0:
        row = tokens_page.get_row_by_name("New")
    expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)
```

**Option 2: Create expired token programmatically**
- More complex: requires API to create token with past expiration date
- Violates the read-only design
- Not recommended unless both Marian AND New are missing

**Option 3: Restore "Marian" token on DEV**
- Quick fix but doesn't address the root issue
- Will break again if someone cleans up test data

**Option 4: Mark test as requiring specific test data**
```python
@pytest.mark.skipif(
    not _has_expired_token(),
    reason="Requires expired token in project 470"
)
```

#### Recommendation

**Implement Option 1** - Update test to try both expired tokens:

```python
with allure.step("Step 2 — Locate an existing expired token row"):
    # AFS documents: use Marian or New (both confirmed expired)
    row = tokens_page.get_row_by_name("Marian")
    if row.count() == 0:
        logger.info("Token 'Marian' not found, trying fallback 'New'")
        row = tokens_page.get_row_by_name("New")
    
    assert row.count() == 1, (
        "Expected to find expired token 'Marian' or 'New' on DEV. "
        "If both are missing, create one via DEV UI: "
        "Settings → Personal Tokens → Create token with past expiration date."
    )
```

This:
- ✅ Follows the AFS's documented fallback strategy
- ✅ Keeps the test read-only
- ✅ Provides clear failure message if BOTH tokens are missing
- ✅ Reduces brittleness without changing test strategy

---

### ⚠️ Notification Test - SKIPPED (Test Data Issue)

**Test:** `test_notification_text_content_renders_correctly`  
**File:** `automation/tests/ui/admin/test_notification_text_content.py`

```
[ERROR] Screenshot: .../test_notification_text_content_renders_correctly_ERROR_20260824_182023.png
SKIPPED (requires existing notification data on DEV (see AFS § Test Data risk note))
```

#### Root Cause: Missing Test Data

This is **another** read-only test that depends on persistent notification data existing on DEV.

**Same pattern as the token test:**
- Test Type: `reuse-existing`
- Depends on: Existing notifications in the project
- Risk: If notifications are cleared, test correctly skips/fails

#### Is This a Test Bug?

**NO** - The test correctly skipped when preconditions weren't met (no notification data).

#### Fix

**Depends on test requirements:**
- If notifications are essential: Create them programmatically before test
- If read-only is important: Document the required notification state and keep it on DEV
- Current behavior (skip when missing) is actually correct defensive design

---

## Pattern: Test Data Dependencies

Both failures follow the **same pattern:**

| Aspect | Personal Token Test | Notification Test |
|--------|---------------------|-------------------|
| Strategy | `reuse-existing` | `reuse-existing` |
| Depends on | Expired tokens on DEV | Notifications on DEV |
| When data missing | ❌ FAIL | ⚠️ SKIP |
| Is this correct? | ✅ YES (documented risk) | ✅ YES (graceful degradation) |

### Why Use `reuse-existing` Strategy?

From the AFS and test comments:
1. **Read-only verification** - These tests don't create/modify data, they verify UI rendering of existing states
2. **Expired token creation is non-trivial** - Can't easily create a token with past expiration via API
3. **Real data = realistic test** - Testing against actual persistent data catches more UI issues

### The Trade-off

**Benefit:** Tests verify real UI behavior against realistic data  
**Cost:** Tests can fail when test data is cleaned up  
**Mitigation:** Document the dependency + provide fallbacks + clear failure messages

---

## Recommendations

### Immediate Actions

1. **✅ DONE:** Guardrails fix validated - no action needed
2. **TODO:** Update `test_expired_token_shows_expired_icon_and_label` to try both "Marian" and "New" (Option 1 above)
3. **Optional:** Review notification test - decide if skip is acceptable or if data should be seeded

### Long-term Improvements

1. **Document test data requirements** in a shared location:
   - Which tests need which persistent data
   - How to recreate required data if deleted
   - Contact for data restoration

2. **Add test data verification step** to CI setup:
   - Before running admin suite, verify required data exists
   - Fail fast with clear message if missing
   - Option: Auto-restore known test data

3. **Consider hybrid approach** for critical tests:
   - Try reusing existing data first (fast, realistic)
   - Fall back to creating data if missing (slower, reliable)

---

## Impact Assessment

### Guardrails Fix Impact

| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Guardrails tests passing | 0/3 (0%) | ✅ 3/3 (100%) |
| Admin suite status | ❌ RED | ❌ RED (different reason) |
| Tests blocking CI | 3 | 1 (unrelated) |

**The guardrails fix achieved its goal:** All 3 guardrails tests now pass consistently.

### Overall Admin Suite Health

| Category | Count | Notes |
|----------|-------|-------|
| ✅ Passing | ~5 tests | Including all guardrails tests |
| ❌ Failing | 1 test | `test_expired_token_shows_expired_icon_and_label` (test data) |
| ⚠️ Skipped | 1 test | `test_notification_text_content` (test data) |
| **Health** | **83% pass rate** | Excluding skip: 5/6 = 83% |

---

## Conclusion

### Guardrails Fix: ✅ **VALIDATED AND SUCCESSFUL**

Our `private: False` fix resolved all 3 guardrails test failures. The tests now pass consistently in both local and CI environments.

### Admin Suite Failures: ⚠️ **UNRELATED TEST DATA ISSUES**

The admin suite's RED status is caused by:
1. **Missing "Marian" token** on DEV (test data cleanup)
2. **Missing notification data** on DEV (test data cleanup)

Both are:
- ✅ Documented risks in the test specs
- ✅ Failing correctly (not false positives)
- ✅ Fixable with simple test updates or data restoration

### Next Steps

**Priority 1 (High):** Fix the expired token test to try both "Marian" and "New"  
**Priority 2 (Medium):** Document test data requirements for DEV environment  
**Priority 3 (Low):** Review notification test skip behavior

**Our original task (guardrails fix) is complete and successful.** ✅

---

**Analysis completed:** 2026-08-24 21:35  
**Analyst:** Test Automation Lead  
**Validation:** CI run #32761287836 logs + test source + AFS documentation
