# Guardrails Page Object - Refactoring Proposal

## Problem: Duplicate Code

The `remove_blocked_toolkit()` and `remove_blocked_tool()` methods have almost identical implementations:

### Current Code (Duplicated):

```python
# Method 1 - Remove blocked toolkit (lines 175-197)
def remove_blocked_toolkit(self, toolkit_name: str, timeout: int = 5000):
    logger.info("Removing blocked toolkit: %s", toolkit_name)
    self._expand_blocked_section(timeout)
    
    chip = self.page.locator(f'.MuiChip-deletable:has(.MuiChip-label:text-is("{toolkit_name}"))').first
    chip.wait_for(state="visible", timeout=timeout)
    
    delete_icon = chip.locator('.MuiChip-deleteIcon')
    delete_icon.click()
    self.page.wait_for_timeout(500)
    
    logger.info("Removed blocked toolkit: %s", toolkit_name)

# Method 2 - Remove blocked tool (lines 257-278)
def remove_blocked_tool(self, tool_name: str, timeout: int = 5000):
    logger.info("Removing blocked tool: %s", tool_name)
    self._expand_blocked_section(timeout)
    
    chip = self.page.locator(f'.MuiChip-root:has-text("{tool_name}")').first
    chip.wait_for(state="visible", timeout=timeout)
    
    delete_icon = chip.locator('svg')
    delete_icon.click()
    self.page.wait_for_timeout(500)
    
    logger.info("Removed blocked tool: %s", tool_name)
```

**Code similarity: ~85%**

---

## Proposed Solution: Extract Common Method

Create a private helper method that both public methods can use:

```python
def _remove_chip(
    self, 
    item_name: str, 
    chip_selector: str,
    delete_icon_selector: str = '.MuiChip-deleteIcon',
    timeout: int = 5000
):
    """Remove a chip by clicking its delete icon.
    
    Common helper for removing toolkit/tool chips.
    
    Args:
        item_name: Name to search for (toolkit or tool name)
        chip_selector: CSS selector to find the chip
        delete_icon_selector: Selector for delete icon within chip
        timeout: Maximum wait time in milliseconds
    """
    chip = self.page.locator(chip_selector.format(name=item_name)).first
    chip.wait_for(state="visible", timeout=timeout)
    
    delete_icon = chip.locator(delete_icon_selector)
    delete_icon.click()
    self.page.wait_for_timeout(500)

@action("Remove blocked toolkit")
def remove_blocked_toolkit(self, toolkit_name: str, timeout: int = 5000):
    """Remove a toolkit from the blocked toolkits list."""
    logger.info("Removing blocked toolkit: %s", toolkit_name)
    self._expand_blocked_section(timeout)
    
    self._remove_chip(
        toolkit_name,
        chip_selector='.MuiChip-deletable:has(.MuiChip-label:text-is("{name}"))',
        delete_icon_selector='.MuiChip-deleteIcon',
        timeout=timeout
    )
    
    logger.info("Removed blocked toolkit: %s", toolkit_name)

@action("Remove blocked tool")
def remove_blocked_tool(self, tool_name: str, timeout: int = 5000):
    """Remove a tool from the blocked tools list."""
    logger.info("Removing blocked tool: %s", tool_name)
    self._expand_blocked_section(timeout)
    
    self._remove_chip(
        tool_name,
        chip_selector='.MuiChip-root:has-text("{name}")',
        delete_icon_selector='svg',
        timeout=timeout
    )
    
    logger.info("Removed blocked tool: %s", tool_name)
```

---

## Benefits

### 1. DRY (Don't Repeat Yourself)
- ✅ Core logic exists in ONE place
- ✅ Bug fixes apply to both toolkit and tool removal
- ✅ Changes (like adding retry logic) benefit both

### 2. Easier Maintenance
- ✅ If chip structure changes, update once
- ✅ If wait strategy changes, update once
- ✅ Less code to review and test

### 3. Consistent Behavior
- ✅ Both methods use identical wait/click patterns
- ✅ Same error handling
- ✅ Same timeout behavior

### 4. Better Testability
- ✅ Can test core chip-removal logic independently
- ✅ Public methods become thin wrappers (easier to test)

### 5. Extensibility
- ✅ Easy to add `remove_sensitive_tool()` using same helper
- ✅ Can add optional retry logic to helper
- ✅ Can add screenshot-on-failure to helper

---

## Potential Concerns

### ❓ "The selectors are different"
**Answer:** That's exactly why we parameterize them! The helper accepts different selectors.

### ❓ "What if we need different logic later?"
**Answer:** Keep the helper focused on chip removal. If logic diverges significantly, we can always split it back. But for now, 85% similarity suggests they should be unified.

### ❓ "Is it worth the complexity?"
**Answer:** The helper is SIMPLER than duplicate code:
- Duplicated: 2 × 12 lines = **24 lines**
- Refactored: 1 helper (8 lines) + 2 wrappers (2 × 6 lines) = **20 lines**
- Plus benefits of maintainability

---

## Alternative: Even Simpler (Inline the selector)

If we want to keep it VERY simple, just pass the full selector:

```python
def _remove_chip(self, chip_locator: str, delete_icon_selector: str = 'svg', timeout: int = 5000):
    """Remove a chip by clicking its delete icon."""
    chip = self.page.locator(chip_locator).first
    chip.wait_for(state="visible", timeout=timeout)
    
    delete_icon = chip.locator(delete_icon_selector)
    delete_icon.click()
    self.page.wait_for_timeout(500)

def remove_blocked_toolkit(self, toolkit_name: str, timeout: int = 5000):
    logger.info("Removing blocked toolkit: %s", toolkit_name)
    self._expand_blocked_section(timeout)
    
    self._remove_chip(
        chip_locator=f'.MuiChip-deletable:has(.MuiChip-label:text-is("{toolkit_name}"))',
        delete_icon_selector='.MuiChip-deleteIcon',
        timeout=timeout
    )
    
    logger.info("Removed blocked toolkit: %s", toolkit_name)
```

**Even simpler!** Just 5 lines for the helper.

---

## Recommendation

**Proceed with refactoring:**
1. ✅ Extract `_remove_chip()` helper (simple inline selector version)
2. ✅ Update `remove_blocked_toolkit()` to use it
3. ✅ Update `remove_blocked_tool()` to use it
4. ✅ Run existing tests to verify no regression
5. ✅ Commit with message: "refactor(guardrails): extract common chip removal logic"

**Impact:**
- Lines saved: ~8 lines
- Maintainability: significantly improved
- Risk: very low (tests will catch any issues)

---

## Status

📋 **Proposal ready for implementation**

The refactoring is straightforward, low-risk, and provides clear benefits.
