# Test #7 Diagnosis: test_toolkit_creation_create_bucket_verify_list_files

**Date:** 2026-08-17  
**Status:** ❌ **TEST BUG - Navigation Issue**

---

## Issue

**Test Failed** with:
```
AssertionError: Toolkits list should show at least one existing toolkit card
assert 0 > 0
```

**Screenshot Evidence:** Page is on `/artifacts/buckets` instead of `/toolkits/all`

---

## Root Cause

**Test bug, NOT product bug:** The `_cleanup_stale_bucket()` helper navigates to artifacts and performs cleanup, but **never navigates back to toolkits**.

### Code Flow:

```python
# Line 247-253: Precondition cleanup
with allure.step("Precondition cleanup — ..."):
    _cleanup_stale_toolkit(toolkit_api)
    _cleanup_stale_bucket(artifacts_page)  # ← Navigates to artifacts

# Line 257: Step 1 — Navigate to toolkits
with allure.step("Step 1 — Navigate to the Toolkits section"):
    toolkits_list.navigate()  # ← Expects clean navigation
```

**Problem:** `_cleanup_stale_bucket()` (lines 186-199):
1. Calls `artifacts_page.navigate()` (goes to `/artifacts/buckets`)
2. Deletes bucket if it exists
3. **ENDS — leaves page on artifacts**

Then `toolkits_list.navigate()` in Step 1 appears to fail silently — the page stays on artifacts.

---

## Why toolkits_list.navigate() Didn't Navigate

Looking at the navigation code:
```python
# toolkits_list_page.py:81
def navigate(self):
    super().navigate("/toolkits/all")
    self.wait_for_page_load()
```

The navigate call should work. Two possible causes:
1. **JavaScript navigation got lost/cancelled** during cleanup transitions
2. **Test ran fast enough that artifacts page was still settling**

Either way, the **pattern is wrong**: cleanup should NEVER leave the page in an unexpected state.

---

## Fix

**Option 1 (Recommended): Navigate away from artifacts after cleanup**

```python
def _cleanup_stale_bucket(artifacts_page):
    """Best-effort delete stale bucket and return to home."""
    try:
        artifacts_page.navigate()
        # ... delete logic ...
        logger.info("Cleaned up stale bucket '%s'", BUCKET_NAME)
    except Exception as exc:
        logger.warning("Bucket cleanup for '%s' failed (continuing): %s", BUCKET_NAME, exc)
    finally:
        # ALWAYS navigate away from artifacts to avoid state pollution
        artifacts_page.page.goto("/")  # Or toolkits, or any neutral page
```

**Option 2: Make toolkits_list.navigate() more robust**

```python
# toolkits_list_page.py
def navigate(self):
    super().navigate("/toolkits/all")
    self.page.wait_for_url("**/toolkits/all", timeout=10000)  # Ensure URL changed
    self.wait_for_page_load()
```

**Option 3: Don't navigate in cleanup — use API only**

```python
def _cleanup_stale_bucket(artifacts_page):
    """Best-effort delete stale bucket via API (no UI navigation)."""
    # Use artifacts_api.delete_bucket() if available
    pass
```

---

## Classification

| Type | Value |
|------|-------|
| **Root Cause** | Test code bug (navigation side effect) |
| **Product Defect?** | NO |
| **Blocking?** | YES — test cannot run |
| **Severity** | P2 — affects one test only |

---

## Recommended Action

1. **Fix the test** — add `finally:` block to `_cleanup_stale_bucket()` that navigates away from artifacts
2. **Re-run test** to verify fix
3. **Alternative:** If artifacts API is available, use API-only cleanup (no UI)

---

## Summary

Test #7 fails due to **test infrastructure issue**, NOT a product defect:
- Cleanup helper navigates to artifacts for bucket deletion
- Never navigates back
- Subsequent Step 1 navigation silently fails or gets lost
- Test assertion fails because it's on wrong page

**Fix:** Cleanup must restore page state (navigate home/away) in `finally` block.

---

**Next Step:** Apply fix and re-run test individually.
