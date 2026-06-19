---
name: test-quality-checker
description: Analyzes pytest test files for weak assertions, incomplete verification, missing interactions, and other quality issues. Use when reviewing test code, checking test robustness, or when user asks to validate test quality or find weak tests. Critical for maintaining reliable test suites.
argument-hint: <test-file-or-directory>
allowed-tools:
  - Read
  - Edit
  - Grep
  - Glob
---

# Test Quality Checker

Analyzes test files against standards in `.claude/rules/api-tests.md` and `.claude/rules/ui-tests.md`.

## When to Use

- Reviewing test files for quality issues
- Before code review or merging test changes
- User asks to "check if tests are robust" or "validate test quality"

## What This Skill Detects

This skill enforces standards from:
- `.claude/rules/ui-tests.md` - UI testing standards
- `.claude/rules/api-tests.md` - API testing standards

**20 violation categories across 3 severity levels:**

### Critical (Must Fix Before Merge)
1. Trivial assertions (`assert True`)
2. Assertion-less tests
3. Wrong variable assertions
4. Incomplete API verification (status only)

### High Priority (Should Fix Soon)
5. Bare locators in test code (page.locator, page.get_by_* in tests)
6. UI tests without interaction (when test name implies interaction)
7. Overly broad assertions
8. Generic exception catching
9. Hard-coded sleeps
10. No negative test cases
11. Assertions with side effects
12. Race conditions

### Medium Priority (Consider Fixing)
13. UI visibility-only tests (when test name doesn't indicate visibility intent)
14. Duplicate assertions
15. Missing cleanup in fixtures
16. Brittle locators
17. Testing implementation details
18. No failure messages in loops
19. Incomplete state verification
20. Mock over-verification
21. Non-deterministic data assertions
22. No boundary testing

See rules files for detailed examples and explanations.

## Analysis Process

1. **Identify test type** - API (in `tests/api/`) or UI (in `tests/ui/`)
2. **Read relevant rules** - Load `.claude/rules/api-tests.md` or `ui-tests.md`
3. **Read test file** - Parse test functions, assertions, actions, waits
4. **Detect violations** - Apply detection patterns (see Implementation Guidelines)
5. **Categorize by severity** - Critical/High/Medium based on rules
6. **Generate report** - Format findings with rule references

## Report Format

```markdown
# Test Quality Report: `path/to/test_file.py`

## Summary
- Total tests: 24 | Critical: 3 | High: 5 | Medium: 2 | Clean: 14

---

## Critical Issues

### ❌ `test_send_message` (line 105)
**Issue:** UI test verifies button visibility but never clicks it  
**Violates:** `ui-tests.md` → Assertion Quality Standards → Forbidden Patterns #3

**Current:** Only checks `is_visible()` and `is_enabled()`  
**Fix:** Add `chat.send_message()`, wait for response, verify message count increased

---

### ❌ `test_create_agent_api` (line 230)
**Issue:** Only verifies status code, not response body  
**Violates:** `api-tests.md` → Response Verification Requirements

**Current:** `assert response.status_code == 200`  
**Fix:** Add `data = response.json()` and verify id, name, description fields

---

## High Priority Issues
[List with issue/rule/fix...]

## Medium Priority Issues
[List with issue/rule/fix...]

## Recommendations
1. Add waits: 3 tests use `time.sleep()` → use `wait_for_*()`
2. Verify API bodies: 5 tests only check status codes
3. Add negative tests: 8 features lack error cases

## Next Steps
Fix all critical? Show detailed fixes? Focus on specific tests?
```

**Key elements:**
- Reference violated rule for each issue
- Show line numbers
- Brief current/fix description (full examples in rules)
- Actionable recommendations

## Detection Patterns (Condensed)

**Trivial Assertions:** `assert True`, `assert x == x`, `len([]) == 0`  
**API Incomplete:** Has `status_code` assert, missing `.json()` access  
**Bare Locators in Tests (HIGH):**
- Test code contains `page.locator(`, `page.get_by_*`, or direct Playwright element access
- **Violates:** `.claude/rules/page-objects.md` → "Use Page Objects - Never Direct Locators"
- **Exception:** Acceptable if:
  - Comment explicitly documents why bare locator is needed (e.g., dynamic dialog, OR pattern)
  - Locator is for transient/dynamic element that page object can't reasonably own
- **Fix:** Move locator to page object method, or document exception with clear justification

**UI No Interaction (Nuanced):**
- Has `is_visible`/`is_enabled`, missing `.click()`/`.fill()` **AND**:
  - **HIGH priority** if test name suggests interaction: `test_delete_button`, `test_toggle_switch`, `test_send_message`
  - **MEDIUM priority** if test name indicates visibility check: `test_*_visible`, `test_*_renders`, `test_*_displays`, `test_*_exists`, `test_*_present`
  - **ACCEPTABLE** if explicitly named as visibility test and there's a separate interaction test

**Race Conditions:** Action → assertion in 2 lines, no wait keyword between  
**Coverage Gaps:** Only happy path tests, missing error/boundary/validation tests

Full detection algorithms in rules files.

## Nuanced Detection: UI Tests Without Interaction

**Core Principle:** Test names communicate intent. Visibility tests serve a valid purpose.

### When Visibility-Only Checks Are ACCEPTABLE

Test names containing these keywords indicate visibility/rendering intent:
- `*_visible` - e.g., `test_toolkits_section_visible`
- `*_renders` - e.g., `test_dialog_renders_correctly`
- `*_displays` - e.g., `test_error_message_displays`
- `*_exists` - e.g., `test_save_button_exists`
- `*_present` - e.g., `test_tabs_present`
- `*_loads` - e.g., `test_dashboard_loads` (checks elements loaded)

**Example - ACCEPTABLE:**
```python
@pytest.mark.p1
def test_agent_toolkits_section_visible(self, page, agent_id):
    """Toolkits section should be visible with tool switches."""
    detail_page = AgentDetailPage(page)
    detail_page.navigate(agent_id)
    
    available_tools = detail_page.get_available_tools()
    assert len(available_tools) > 0
    
    for tool in available_tools:
        assert tool_locator.is_visible()  # ✅ Name indicates visibility check
```

**Severity:** MEDIUM (if at all) - Consider if a separate interaction test exists.

---

### When Visibility-Only Checks Are VIOLATIONS

Test names containing action verbs suggest the test should perform that action:
- `test_delete_*` - Should call `.delete()` or `.remove()`
- `test_create_*` - Should call `.create()` or `.save()`
- `test_toggle_*` - Should call `.toggle()` or `.click()`
- `test_send_*` - Should call `.send()` or `.submit()`
- `test_edit_*` - Should call `.fill()` or `.type()`

**Example - VIOLATION:**
```python
@pytest.mark.p1
def test_delete_button(self, page):
    """Delete button functionality."""
    # ❌ HIGH PRIORITY - Test name promises deletion but only checks visibility
    assert chat_page.delete_button.is_visible()
    assert chat_page.delete_button.is_enabled()
    # Test ends - button never clicked!
```

**Severity:** HIGH - Test name promises interaction that doesn't happen.

**Fix:** Either rename to indicate scope, or add interaction:
```python
# Option 1: Rename to clarify scope
def test_delete_button_visible_when_message_exists(...)

# Option 2: Add the promised interaction (better)
def test_delete_button(self, page):
    initial_count = chat_page.get_message_count()
    chat_page.delete_button.click()
    page.wait_for_load_state("networkidle")
    assert chat_page.get_message_count() < initial_count
```

---

### Detection Algorithm

```python
def detect_ui_no_interaction(test_function):
    has_visibility_checks = contains("is_visible", "is_enabled", "is_displayed")
    has_interactions = contains(".click(", ".fill(", ".type(", ".press(")
    
    test_name = test_function.name.lower()
    visibility_keywords = ["visible", "renders", "displays", "exists", "present", "loads"]
    action_keywords = ["delete", "create", "toggle", "send", "edit", "submit", "click"]
    
    if has_visibility_checks and not has_interactions:
        # Check test name intent
        if any(kw in test_name for kw in visibility_keywords):
            return "MEDIUM or SKIP"  # Acceptable if name indicates visibility
        elif any(kw in test_name for kw in action_keywords):
            return "HIGH"  # Violation - name promises action
        else:
            return "MEDIUM"  # Unclear - suggest clarifying test name
    
    return "PASS"
```

## Detection: Bare Locators in Test Code

**Core Principle:** All UI interaction must go through page objects. Tests should never contain `page.locator()` or direct Playwright element access.

### Pattern Detection

Search test functions for these patterns:
- `page.locator(` - Direct CSS/XPath locators
- `page.get_by_role(` - Accessible role selectors
- `page.get_by_label(` - Label-based selectors
- `page.get_by_text(` - Text-based selectors
- `page.get_by_placeholder(` - Placeholder-based selectors
- `page.wait_for_load_state(` - Raw networkidle wait (use `page_obj.wait_for_network()` instead)

**Severity:** **HIGH** - Violates fundamental page object pattern from `.claude/rules/ui-tests.md` → "Use Page Objects - Never Direct Locators"

**Special case — `page.wait_for_load_state(` in tests:**
- Every page object inherits `wait_for_network(timeout)` from `BasePage` which wraps this call
- Raw `page.wait_for_load_state("networkidle", ...)` in a test body should always be `page_obj.wait_for_network(timeout=...)` instead
- **Violates:** `ui-tests.md` → Forbidden Patterns #7
- **Exception:** `page.reload(wait_until="networkidle")` is still acceptable at test level when an explicit page reload is needed

### Violations

**Example - BAD:**
```python
@pytest.mark.p1
def test_delete_message(page):
    """Delete a message from chat."""
    chat = ChatPage(page)
    chat.navigate_to_chat()
    
    # ❌ HIGH - Bare locator in test code
    delete_btn = page.locator('button[aria-label="Delete"]')
    delete_btn.click()
```

**Fix:**
```python
@pytest.mark.p1
def test_delete_message(page):
    """Delete a message from chat."""
    chat = ChatPage(page)
    chat.navigate_to_chat()
    
    # ✅ Use page object method
    chat.delete_message(-1)
```

---

### Acceptable Exceptions

Bare locators are acceptable ONLY when:

1. **Dynamically triggered elements** that page object methods can't reasonably own:
   ```python
   # Acceptable - dialog triggered by method call, checking if it appeared
   chat.edit_context_settings()
   # Context settings may render as dialog OR modal - dynamic check
   dialog = page.locator('[role="dialog"], [class*="modal"]')
   expect(dialog.first).to_be_visible()
   ```

2. **Explicitly documented with clear justification:**
   ```python
   # Acceptable - comment explains why
   # This is an acceptable bare locator - checking for optional error state
   # that may or may not appear depending on backend behavior
   error = page.locator('[role="alert"]')
   if error.count() > 0:
       # Handle error
   ```

3. **OR pattern checks** where multiple element types are valid:
   ```python
   # Acceptable - checking for menu OR navigation (either is valid)
   menu = page.locator('[role="menu"], [role="listbox"]')
   url_changed = "/settings" in page.url
   assert menu_visible or url_changed  # Either outcome acceptable
   ```

**Rule:** If no exception applies, the bare locator must be moved to a page object method.

---

### Detection Algorithm

```python
def detect_bare_locators(test_function):
    bare_locator_patterns = [
        "page.locator(",
        "page.get_by_role(",
        "page.get_by_label(",
        "page.get_by_text(",
        "page.get_by_placeholder(",
        "page.wait_for_load_state(",  # Use page_obj.wait_for_network() instead
    ]
    
    for line_num, line in enumerate(test_function.body):
        for pattern in bare_locator_patterns:
            if pattern in line:
                # Check for documented exception
                prev_line = test_function.body[line_num - 1] if line_num > 0 else ""
                if "acceptable bare locator" in prev_line.lower():
                    return "ACCEPTABLE"  # Documented exception
                
                # Check for dynamic dialog/OR pattern context
                next_lines = test_function.body[line_num:line_num+5]
                if any("# may render as" in l or "either" in l.lower() for l in next_lines):
                    return "ACCEPTABLE"  # Dynamic check with justification
                
                return "HIGH"  # Violation - move to page object
    
    return "PASS"
```

## Workflow

**Before Analysis:**
1. Read `.claude/rules/api-tests.md` or `ui-tests.md` (based on test type)
2. Identify test type from path (`tests/api/` vs `tests/ui/`)

**During Analysis:**
- Check for each violation pattern
- **CRITICAL:** For UI tests, scan for `page.locator(`, `page.get_by_*` in test functions (bare locators)
- Always cite rule violations: `**Violates:** ui-tests.md → Section → Pattern #N` or `page-objects.md → Section`
- Check edge cases before flagging (custom helpers, smoke tests, page objects with built-in waits)
- For bare locators, check for documented exceptions (comments explaining why)

**Reporting:**
- Group by severity (Critical/High/Medium)
- Show line numbers, brief current/fix description
- Provide actionable recommendations

**If User Approves Fixes:**
1. Show change (line numbers, before/after, reason)
2. Ask confirmation for each
3. Apply with Edit tool, preserve style
4. Verify syntax

## Valid Exceptions
- **Custom assertion helpers** - Check if helper has proper assertions
- **@pytest.mark.smoke tests** - Intentionally minimal
- **Page object methods** - May encapsulate waits internally
- **Visibility tests** - When test name indicates visibility intent (see "Nuanced Detection" section)
- **Separate test coverage** - If visibility test exists alongside a dedicated interaction test
- **Documented bare locators** - When explicitly commented as acceptable with clear justification (dynamic dialogs, OR patterns)
- **Dynamic element checks** - Elements triggered by page object methods that can't reasonably be owned by page object (must be documented)
