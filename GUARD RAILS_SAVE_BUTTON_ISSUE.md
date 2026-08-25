# Guardrails Save Button Issue - Root Cause Found

**Date:** 2026-08-25 10:45 UTC  
**Test:** `test_guardrails_live_reload.py`  
**Status:** ❌ Save button doesn't appear after removing blocked items

---

## Test Results

```
[CLEANUP] Removed blocked toolkit: jira          ← Removed from UI ✅
[CLEANUP] Removed blocked tool: search_using_jql ← Removed from UI ✅
[CLEANUP] Saving blocked section to unblock JIRA
[CLEANUP] Failed to save: Locator.wait_for: Timeout 20000ms exceeded.
  - waiting for locator("button:has-text(\"Save\")").last to be visible
```

**Result:** JIRA is still blocked after cleanup (verified in browser).

---

## Root Cause

**Removing a blocked item by clicking the X button does NOT make the Save button visible.**

Possible reasons:
1. The form doesn't detect removal as a "change" (not marking form dirty)
2. The Save button only appears for additions, not removals
3. The removal is client-side only until page reload

---

## Investigation Needed

Need to check:
1. Does clicking X on a chip mark the form as dirty?
2. Is the Save button disabled or hidden after removal?
3. Does the Save button exist but is just not visible?
4. Do we need to manually trigger something to enable Save?

---

## Proposed Fix Options

### Option 1: Check if Save button exists but is disabled
```python
save_btn = pg.locator('button:has-text("Save")').last
if save_btn.count() > 0:
    # Button exists - check if enabled
    if not save_btn.is_enabled():
        # Force enable by making a dummy change?
        pass
else:
    # Button doesn't exist - need different approach
    pass
```

### Option 2: Make a dummy change to trigger Save button
```python
# After removing items, add and remove a dummy item to trigger form dirty
guardrails.add_blocked_toolkit("dummy")
guardrails.remove_blocked_toolkit("dummy")
# Now Save should appear
guardrails.save_configuration()
```

### Option 3: Use API to unblock instead of UI
```python
# If UI save doesn't work, use API directly
# POST /api/v2/admin/guardrails with updated config
```

### Option 4: Don't save - just reload and let removal be temporary
```python
# Remove items (client-side only)
# Reload page (items disappear temporarily)
# Create toolkit (works because guardrails check is also client-side?)
```

---

## Next Steps

1. ✅ Verified JIRA is still blocked after test ran
2. ⏳ Need to investigate Save button state after removal
3. ⏳ Test if dummy add+remove triggers Save
4. ⏳ Check if API endpoint exists for guardrails config

---

**Status:** Blocked - need to understand how to trigger Save after removal
