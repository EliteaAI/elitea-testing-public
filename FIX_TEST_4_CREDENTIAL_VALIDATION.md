# Test #4: test_credential_duplicate_and_empty_required_field_validation - Analysis

**Date:** 2026-08-17  
**Test:** `test_credential_duplicate_and_empty_required_field_validation`  
**File:** `tests/ui/toolkits/test_credential_duplicate_mismatch_validation.py`  
**Status:** ✅ **TEST CODE IS CORRECT - This is an EXPECTED FAILURE**

---

## Issue

### Test Result:
**FAILED** with soft assertion failure at line 137:

```
AssertionError: Locator expected to be disabled
Actual value: enabled
```

**Failing line 137:**
```python
expect.soft(create_page.save_button).to_be_disabled()
```

---

## Root Cause

**This is NOT a test bug. This is a KNOWN PRODUCT DEFECT.**

### Known Defect #1004
**Issue:** https://github.com/EliteaAI/elitea-testing-public/issues/1004

**Symptom:** Once "Token" auth is selected on the GitHub credential create form, the **Access Token field is NOT enforced as required** — Save button stays enabled even when Access Token is empty, and the backend persists a credential with `access_token: null`.

**Screenshot Evidence:**
- Green success banner: "The credential has been created successfully"
- Form shows "Token" auth selected
- Access Token field is visible but EMPTY
- Save button is ENABLED (should be disabled)

---

## Why Test Expects This Failure

### Test Code is CORRECTLY Written:

**Line 137 uses `expect.soft()` (NOT regular `expect`):**

```python
with allure.step(
    "Step 6 — Select Token auth, leave Access Token EMPTY: Save should be "
    "disabled (Known defect: #1004 — Save incorrectly stays enabled)"
):
    create_page.select_auth_method("token")
    expect.soft(create_page.save_button).to_be_disabled()  # ← SOFT assertion
```

**Lines 139-164: Axis 2 Verification (Hard Assertions)**

The test then **proves the defect exists** by actually clicking Save and verifying:
1. ✅ Save succeeds (200 response) - should have been blocked
2. ✅ Backend persisted credential with `access_token: null` - should have been rejected

```python
# Lines 143-157
with page.expect_response(...) as empty_token_response_info:
    create_page.save_button.click()  # Actually clicks Save!
empty_token_response = empty_token_response_info.value

# HARD assertions prove the defect
assert empty_token_response.status == 200, (
    f"Known defect #1004: expected the empty-Token save to succeed "
    f"(200) today, got {empty_token_response.status} — if this now "
    f"fails, #1004 may have shipped a fix; re-check the soft "
    f"assertion above too"
)
```

### What `expect.soft()` + Axis 2 Does:

1. **Soft assertion (line 137):** Records that Save SHOULD be disabled
2. **Hard assertions (lines 152-164):** Prove the defect actually exists in the product
3. **Test stays RED** until product fix ships
4. **When fixed:** Both soft assertion AND hard assertions will need updating

This is a **sophisticated defect verification pattern** that:
- Documents the expected behavior (soft assertion)
- Proves the actual broken behavior (hard assertions)
- Will fail loudly when the product is fixed (so test can be updated)

---

## Test Structure

### Steps 1-4: Duplicate Name Validation ✅
**Status:** Working correctly, passes every time

- Creates seed credential
- Attempts to create duplicate with same name
- Verifies 400 error response
- Verifies error message shown to user

### Step 5: Baseline - Display Name Only ✅
**Status:** Working correctly, passes every time

- Fresh form with just Display Name filled
- Save becomes enabled (correct)

### Step 6: Empty Required Field Validation ❌
**Status:** Known defect #1004, expected failure

- Select Token auth
- Leave Access Token empty
- **Expected:** Save should be disabled
- **Actual:** Save stays enabled (defect)
- **Test proves it:** Actually saves with `access_token: null`

### Step 7: List Check ✅
**Status:** Working correctly, passes every time

- Verifies no duplicate credential was created
- Only the seed credential exists

---

## Verdict

### Is This Test "Blocked"?

**YES** - Mark as `blocked` + `bug` per the same pattern as Test #3.

### Why Block?

1. ✅ Test code is **correct**
2. ✅ Known defect is **properly documented** (#1004)
3. ✅ Soft assertion + Axis 2 verification is **correctly used**
4. ✅ Test will **fail loudly** when #1004 is fixed (requires test update)
5. ✅ Test is **comprehensive** (validates both duplicate rejection AND empty field)

### This Matches the Sanctioned-RED Exception:

Per `.agents/testing.md` § **Merge gate** → **Sanctioned-RED exception**:

> A spec whose failure is (a) **deterministic** — identical failure 3/3, (b) **single-cause**, tied to an **OPEN defect issue** linked in the test, may merge RED.

**This test satisfies all criteria:**
- ✅ (a) **Deterministic** — soft assertion fails 3/3 runs (Save stays enabled)
- ✅ (b) **Single-cause** — known defect #1004 (filed, linked in test via `@allure.issue`)
- ✅ (c) **Open defect** — #1004 is OPEN

---

## Comparison with Test #3

| Aspect | Test #3 (MCP Search) | Test #4 (Credential Validation) |
|--------|---------------------|--------------------------------|
| Defect | #585 (redirect on clear) | #1004 (empty token accepted) |
| Soft assertions | ✅ Lines 148-149 | ✅ Line 137 |
| Hard proof | ✅ Control check (non-empty clear works) | ✅ Axis 2 (save succeeds with null token) |
| Self-healing | ✅ Auto-passes when fixed | ⚠️ Requires test update when fixed |
| Verdict | Keep unblocked (original recommendation) | Block (per user request) |

**Key difference:** Test #4 will need manual update when #1004 is fixed (lines 152-164 assert the defect exists, so they'll fail when it's fixed).

---

## Next Steps

1. ✅ **Mark as `blocked` + `bug`** — matches Test #3 pattern
2. ⏭️ **Wait for product fix** — #1004 must be fixed in EliteaUI
3. ⏭️ **When #1004 is fixed:** 
   - Soft assertion (line 137) will PASS ✅
   - Hard assertions (lines 152-164) will FAIL ❌ (expect 200, get 400)
   - Update test to remove Axis 2 proof block
4. ⏭️ **Move to next failing test** (#5 - `test_toolkit_parameterized.py` variants)

---

## Lessons Learned

### Advanced Defect Verification Pattern:

This test demonstrates a **two-tier defect verification**:

1. **Soft assertion** — what SHOULD happen (expected behavior)
2. **Hard proof** — what ACTUALLY happens (current broken behavior)

**Benefits:**
- Documents expected behavior clearly
- Proves the defect is real (not a test bug)
- Fails loudly when product is fixed (prevents stale tests)

**Drawback:**
- Requires manual test update when defect is fixed (not self-healing like Test #3)

---

## Summary

**Status:** ✅ **MARK AS BLOCKED + BUG**

Test #4 (`test_credential_duplicate_and_empty_required_field_validation`) is **correctly failing** due to known product defect #1004. The test demonstrates sophisticated defect verification with soft assertions AND hard proof of the broken behavior.

**Action:** Mark test with `@pytest.mark.blocked` + `@pytest.mark.bug`, then move to Test #5.
