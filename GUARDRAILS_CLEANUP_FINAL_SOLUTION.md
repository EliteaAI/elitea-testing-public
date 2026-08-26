# Guardrails Cleanup - Complete Solution

**Date:** 2026-08-25  
**Status:** ✅ FIXED

---

## Problem Summary

The `cleanup_guardrails` fixture had THREE related problems:

### Problem 1: Save Button Not Found (commit 1e6fb6275)
- ✅ Removed blocked items
- ❌ Save button timed out (not in viewport)
- **Fix:** Scroll to bottom BEFORE clicking Save

### Problem 2: Save Button Disabled (commit cb33592e2)
- ✅ Scroll found the button
- ❌ Button was disabled (clicking X doesn't mark form dirty)
- **Fix:** Add dummy item + remove it → triggers dirty state

### Problem 3: Dummy Input Not Found (commit f929f72fc — THIS COMMIT)
- ✅ Scroll works
- ✅ Dummy add/remove logic added
- ❌ **Input field doesn't exist** (accordion collapsed after reload)
- **Fix:** Expand blocked section BEFORE adding dummy item

---

## Root Cause Analysis

### The Three-Layer Problem

```
User action → Side effect → Our solution → New problem
═══════════════════════════════════════════════════════
Remove items  →  Save disabled  →  Add dummy  →  Input missing
(click X)        (not dirty)       (triggers dirty)   (accordion closed)
```

#### Layer 1: Save Button Not in Viewport
```python
# ❌ WRONG — button exists but is off-screen
save_btn = pg.locator('button:has-text("Save")').last
save_btn.click()  # Timeout: not in viewport
```

**Why:** After removing items from sections near top of page, the Save button
(in footer) is below the fold.

**Fix 1 (commit 1e6fb6275):**
```python
# Scroll to bottom first
pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
pg.wait_for_timeout(500)
save_btn.click()
```

#### Layer 2: Save Button Disabled
```python
# ❌ WRONG — button is visible but disabled
pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
save_btn = pg.locator('button:has-text("Save")').last
save_btn.click()  # Still times out: button is disabled!
```

**Why:** MUI form only detects ADD operations as dirty. Clicking X to remove
items doesn't mark form dirty, so Save stays disabled.

**Fix 2 (commit cb33592e2):**
```python
# Add dummy item → remove it = form is dirty now
if save_btn.count() == 0 or not save_btn.is_enabled():
    dummy_input = pg.locator('input[placeholder*="search and filter"]').first
    dummy_input.click()
    dummy_input.fill("dummy_cleanup_toolkit")
    dummy_input.press("Enter")
    
    # Remove dummy
    dummy_chip.locator('.MuiChip-deleteIcon').click()
    
    # Now Save is enabled!
    save_btn.click()
```

#### Layer 3: Dummy Input Not Found
```python
# ❌ WRONG — trying to access input that doesn't exist
if save_btn.count() == 0 or not save_btn.is_enabled():
    dummy_input = pg.locator('input[placeholder*="search and filter"]').first
    dummy_input.click()  # Timeout: input doesn't exist!
```

**Why:** After removing items, we reload the page for stable state. After
reload, the Blocked Toolkits accordion is COLLAPSED by default. The search
input only exists when the accordion is EXPANDED.

**Fix 3 (commit f929f72fc — THIS COMMIT):**
```python
if save_btn.count() == 0 or not save_btn.is_enabled():
    # CRITICAL: Expand blocked section first!
    _expand_blocked_section()
    
    # NOW the input exists
    dummy_input = pg.locator('input[placeholder*="search and filter"]').first
    dummy_input.click()
    dummy_input.fill("dummy_cleanup_toolkit")
    # ...rest of dummy add/remove
```

---

## Complete Solution

### The Full Working Flow

```python
# 1. Remove blocked items
remove_blocked_toolkit("jira")
remove_blocked_tool("search_using_jql")

# 2. Reload page (for stable state)
pg.reload()

# 3. Save changes (if anything was removed)
if removed_anything:
    # Check if Save is already enabled
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    save_btn = pg.locator('button:has-text("Save")').last
    
    if save_btn.count() == 0 or not save_btn.is_enabled():
        # Save is disabled → trigger dirty state
        
        # CRITICAL: Expand section first (after reload it's collapsed)
        _expand_blocked_section()
        
        # Add dummy item
        dummy_input = pg.locator('input[placeholder*="search and filter"]').first
        dummy_input.click()
        dummy_input.fill("dummy_cleanup_toolkit")
        dummy_input.press("Enter")
        pg.wait_for_timeout(500)
        
        # Remove dummy (form is now dirty)
        dummy_chip = pg.locator('.MuiChip-deletable:has(.MuiChip-label:text-is("dummy_cleanup_toolkit"))')
        dummy_chip.first.locator('.MuiChip-deleteIcon').click()
        pg.wait_for_timeout(300)
        
        # Save is now enabled!
    
    # Click Save (scroll again in case section expansion moved it)
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(500)
    save_btn = pg.locator('button:has-text("Save")').last
    save_btn.click(force=True, timeout=5000)
    pg.wait_for_load_state("networkidle", timeout=20000)
```

---

## Key Learnings

### 1. UI State Coupling
**Problem:** Multiple UI states interact in non-obvious ways:
- Save button visibility (scroll position)
- Save button enabled state (form dirty flag)
- Input field existence (accordion open/closed)

**Lesson:** When debugging UI automation, trace the ENTIRE state chain, not
just the immediate failure.

### 2. Workarounds Create Dependencies
**Problem:** Our workaround (dummy add/remove) created a NEW dependency
(section must be expanded).

**Lesson:** Workarounds add complexity. Document why each step exists, and
check prerequisites before executing.

### 3. Reload Resets More Than You Think
**Problem:** We added `pg.reload()` for "stable state" without considering
that accordions default to collapsed.

**Lesson:** After any navigation/reload, re-verify element accessibility
before interaction.

### 4. Framework Quirks Are Load-Bearing
**MUI form dirty state detection:**
- ADD item → dirty ✅
- REMOVE item → NOT dirty ❌

This isn't a bug — it's MUI's design. Our automation MUST account for it.

---

## Verification

### Test Command
```bash
cd automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/admin/test_guardrails_live_reload.py::TestBlockedToolLiveReload::test_blocked_tool_live_reload_case_insensitive \
  -v
```

### Expected Output
```
[CLEANUP] Running guardrails cleanup BEFORE tests
[CLEANUP] Removed blocked tool: search_using_jql
[CLEANUP] Saving blocked section to persist removal
[CLEANUP] Save not enabled, adding dummy item to trigger dirty state
[CLEANUP] Form now dirty, Save should be enabled
[CLEANUP] Saved - changes persisted
✅ PASSED
```

### Expected Behavior
1. ✅ Cleanup removes blocked items from UI
2. ✅ Dummy add/remove triggers dirty state
3. ✅ Save button becomes enabled
4. ✅ Click Save persists changes
5. ✅ Tests can create JIRA toolkit (no more 403 Forbidden)

---

## Commits

| Commit | Problem Fixed | Status |
|--------|---------------|--------|
| 1e6fb6275 | Save button not in viewport | ✅ Partial fix |
| cb33592e2 | Save button disabled (not dirty) | ✅ Partial fix |
| **f929f72fc** | **Dummy input not found (accordion closed)** | **✅ COMPLETE** |

---

## Related Files

### Modified
- `automation/tests/ui/admin/test_guardrails_live_reload.py:316-365`
  - cleanup_guardrails fixture
  - Added `_expand_blocked_section()` before dummy input access

- `automation/pages/guardrails_admin_page.py:670-716`
  - save_configuration() method
  - Already had `self._expand_blocked_section()` (line 691)

### Documentation
- `GUARDRAILS_CLEANUP_FIX.md` — Updated with complete solution
- `GUARDRAILS_REFACTORING_PROPOSAL.md` — Proposes extracting common chip-removal logic

---

## Status

✅ **COMPLETE** — All layers fixed  
⚠️ **Gotcha:** Initially called `_expand_blocked_section()` as standalone function → **`NameError`**  
✅ **Fixed:** Use page object method: `guardrails._expand_blocked_section()`  
⚠️ **Gotcha 2:** React re-renders after removals → DOM in transitional state → expand timeout  
✅ **Fixed:** Add 1000ms stabilization wait + 10s timeout + reload retry  
🧪 **Test:** ✅ **PASSED** (150s, 0 reruns)  
📝 **Documentation:** Complete  
📤 **Ready to push**
