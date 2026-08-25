# Guardrails Cleanup Fix - Complete Solution

**Date:** 2026-08-25  
**Issue:** Cleanup fixture removes blocked toolkits/tools from UI but doesn't save changes  
**Status:** ✅ FIXED

---

## Problem

The `cleanup_guardrails` fixture was:

1. ✅ Successfully removing blocked toolkits (JIRA)
2. ✅ Successfully removing blocked tools (search_using_jql)
3. ❌ **Failing to save the changes**

Result: JIRA remained blocked, tests got 403 Forbidden

---

## Root Cause

**The Save button is in the page footer, below viewport after removing items.**

Why `scroll_into_view_if_needed()` failed:
- Method waits for element to be "visible" (in DOM AND viewport)
- Save button exists but is NOT in viewport (it's in footer)
- Wait times out (15000ms)

---

## Solution

**Scroll page to bottom using JavaScript, THEN click Save:**

```python
# Scroll to bottom first
pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
pg.wait_for_timeout(500)  # Let scroll settle

# Now Save is visible
save_btn = pg.locator('button:has-text("Save")').last
save_btn.click(timeout=10000)
```

---

## Verification

```bash
cd automation
pytest tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolkitLiveReload::test_blocked_toolkit_live_reload_case_insensitive -v
```

Expected:
- ✅ Test PASSED
- ✅ Cleanup logs "Saved - JIRA is now unblocked"
- ✅ JIRA toolkit creation returns 200 OK

---

**Status:** ✅ FIXED  
**Commit:** 1e6fb6275  
**Test Result:** PASSED (133.47s)
