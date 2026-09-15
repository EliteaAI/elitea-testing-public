# Back Button Fix Summary - ELITEA-1869

**Date:** 2026-09-11  
**Branch:** aqa_main_release_2.0.6  
**Fix:** Cherry-picked breadcrumb navigation repair from automation/base

---

## Problem

The back button test (`test_agent_back_navigation.py`) was failing on stage2 with a **15-second timeout** because:

1. **Old version on aqa_main_release_2.0.6** (July 2026):
   - Used `data-testid="back-button"` (arrow button)
   - Test was passing when created

2. **UI changed** (September 1, 2026):
   - EliteaUI commit `f1d4ea47` (EL-6460) replaced back arrow with **breadcrumb navigation**
   - `data-testid="back-button"` no longer rendered on agent detail page
   - Test now times out looking for non-existent element

---

## Root Cause (from PR #2178)

**EliteaAI/EliteaUI@f1d4ea47** introduced breadcrumb navigation:

```jsx
{hasBreadcrumbTrail ? <Breadcrumbs /> : <><BackButton /><Typography …/></>}
```

On `/agents/:tab/:agentId`, `useHasBreadcrumbTrail()` returns **true**, so:
- `<Breadcrumbs/>` branch is taken
- `<BackButton/>` with `data-testid="back-button"` **never mounts**
- Test times out waiting for non-existent element

**This is intentional UI drift, not a product defect.**

---

## Solution Applied

### 1. Cherry-picked Fix from automation/base

**Commit:** `0ac4d4a50` (PR #2178)  
**Author:** Alexander Bychinskiy  
**Date:** Sept 10, 2026

**Changes:**
```
automation/pages/agent_detail_page.py                    +65 lines
automation/tests/ui/agents/test_agent_back_navigation.py +147 lines
test-specs/agents/l1_agent-detail-...ELITEA-1869.md      +681 lines (AFS updated)
```

**Key changes:**
- Added breadcrumb locators to `agent_detail_page.py`:
  - `breadcrumbs = LocatorDescriptor(testid="breadcrumbs")`
  - `breadcrumb_item = LocatorDescriptor(testid="breadcrumb-item")`
  - `agent_detail_title = LocatorDescriptor(testid="agent-detail-title")`
- Added `click_breadcrumb_parent()` method
- Updated test to click breadcrumb "Agents" link instead of back button
- Added **absence assertion** for back button (proves it's not rendered)

### 2. Adapted for aqa Branch

**Issue:** `open_first_agent()` method doesn't exist on aqa branch  
**Fix:** Changed to use existing `select_agent(target_agent_name)` method

```python
# Original (automation/base):
list_page.open_first_agent(timeout=NAVIGATION_TIMEOUT)

# Adapted (aqa_main_release_2.0.6):
list_page.select_agent(target_agent_name, timeout=NAVIGATION_TIMEOUT)
```

---

## Verification

### Local Test: ✅ PASSED

```bash
cd automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/agents/test_agent_back_navigation.py::test_back_button_from_agent_detail_returns_to_intact_agents_list \
  -v --tb=short
```

**Result:**
```
============================== 1 passed in 12.43s ==============================
```

### Commit Details

**Branch:** aqa_main_release_2.0.6  
**Commit:** `443c9a653`  
**Pushed:** Yes (to origin)

---

## What Changed in the Test

### Old Test (July 2026)
```python
with allure.step("Step 3 — Click the Back button in the agent detail page header"):
    with page.expect_response(...):
        agent.click_back_button(timeout=NAVIGATION_TIMEOUT)  # ❌ Times out
```

### New Test (September 2026)
```python
with allure.step("Step 3a — Verify back-arrow control is NOT rendered"):
    # Breadcrumb present
    expect(detail_page.breadcrumbs).to_be_visible()
    
    # Legacy back button absent (intentional)
    expect(detail_page.back_button).to_have_count(0)  # ✅ Proves drift is expected

with allure.step("Step 3b — Click breadcrumb parent to navigate back"):
    with page.expect_response(...):
        detail_page.click_breadcrumb_parent(timeout=NAVIGATION_TIMEOUT)  # ✅ Works
```

---

## Files Changed

| File | Change |
|------|--------|
| `automation/pages/agent_detail_page.py` | +65 lines - Added breadcrumb locators and methods |
| `automation/tests/ui/agents/test_agent_back_navigation.py` | +147 lines - Updated to use breadcrumbs, adapted method call |
| `test-specs/agents/l1_agent-detail-...ELITEA-1869.md` | +681 lines - AFS updated for breadcrumb UI |
| `.agents/memory/qa-engineer/breadcrumb_replaced_back_button_on_detail_routes.md` | NEW - Documents UI change |
| `.agents/memory/test-automation-engineer/dev_page_goto_flake_is_a_precondition.md` | NEW - Documents known flake |
| `.agents/memory/test-automation-engineer/env_test_is_a_symlink_dev_swap_recipe.md` | NEW - Documents env swap pattern |

---

## Expected Impact on Stage2

### Before Fix
- ❌ Test times out after 15s waiting for `data-testid="back-button"`
- ❌ No navigation happens
- ❌ Test fails

### After Fix
- ✅ Test finds breadcrumbs immediately
- ✅ Clicks "Agents" breadcrumb link
- ✅ Navigation completes within 2-3 seconds (if backend is healthy)
- ✅ Test passes

**Note:** If stage2 backend is still slow (15s+ API response), the test may still fail, but it will be a **legitimate backend performance issue**, not a test code problem.

---

## Related Product Issues

Found in elitea_issues repo:

| Issue | Status | Description |
|-------|--------|-------------|
| #5397 | CLOSED | Skill Editor back button navigated to Chats instead of Skills list |
| #6134 | CLOSED | History view missing close button |
| #6039 | OPEN | Artifact Toolkit Cancel doesn't navigate back to list |

**Pattern:** Back/Cancel navigation is a recurring fragility across entity detail pages.

---

## TMS Case vs Reality

### TMS Case ELITEA-1869

**What it specified:**
- Generic "Back button in the agent detail page header"
- No testid, no position detail
- No performance expectation
- Pass/fail: "Returns to Agents dashboard" OR "Redirected to wrong page"

**What reality revealed:**
- Specific testid: `data-testid="back-button"`
- Position: Top-left of header
- **UI changed:** Back button replaced with breadcrumbs
- **Performance issue:** 15s timeout on stage2 (backend latency)

### Recommendations for TMS Case

Consider adding:
1. Expected navigation timing: "< 5 seconds"
2. Button identification: "Top-left back arrow OR breadcrumb navigation"
3. Cross-entity verification: "Same behavior for Skills, Pipelines"

---

## Next Steps

1. ✅ **Fix pushed to aqa_main_release_2.0.6**
2. ⏭️ **Run stage2 tests** to verify fix works on deployed environment
3. ⏭️ **Monitor stage2 backend performance** - if test still times out, it's a backend issue
4. ⏭️ **Consider updating TMS case** to reflect breadcrumb UI change

---

## Summary

**Problem:** Test looking for removed UI element (back button → breadcrumbs)  
**Solution:** Cherry-picked breadcrumb fix from automation/base + adapted method call  
**Status:** ✅ Fixed and pushed  
**Local verification:** ✅ PASSED  
**Ready for stage2 testing:** Yes

---

**Created:** 2026-09-11  
**Session:** LEAD_1  
**Automation Lead:** Tal (test-automation-lead agent)
