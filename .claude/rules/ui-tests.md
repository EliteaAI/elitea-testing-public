---
description: UI test guidelines using Page Object Model with Playwright
paths:
  - automation/tests/ui/**/*.py
---

# UI Test Guidelines

## Use Page Objects - Never Direct Locators

**All UI interactions must go through page objects:**

```python
# ❌ WRONG - Direct Playwright locators in test
def test_create_agent(page):
    page.locator('button:has-text("Create")').click()
    page.locator('input[name="name"]').fill("Test")
    page.locator('button:has-text("Save")').click()

# ✅ CORRECT - Use page object methods
def test_create_agent(page, agent_api):
    from pages.agent_form_page import AgentFormPage
    
    form_page = AgentFormPage(page)
    form_page.navigate_to_create()
    form_page.fill_form(name="Test", description="Test agent")
    form_page.click_save()
```

**Why:** Page objects encapsulate selectors and provide stable, maintainable interface.

### Which Page Object to Import?

**Import the specialized page that matches your test context:**

```python
# Dashboard/list tests
from pages.agents_list_page import AgentsListPage
list_page = AgentsListPage(page)
list_page.search_input.fill("query")  # Locator access ✅

# Form tests
from pages.agent_form_page import AgentFormPage
form_page = AgentFormPage(page)
form_page.name_input.click()  # Locator access ✅

# Detail page tests
from pages.agent_detail_page import AgentDetailPage
detail_page = AgentDetailPage(page)
detail_page.name_input.click()  # Inherited locator ✅

# Multi-operation tests (use facade for convenience)
from pages.agent_page import AgentPage
agent = AgentPage(page)
agent.navigate_to_agents()  # Method delegation ✅
```

**Rule:** If you need locator access (form fields, buttons), import the specialized page directly, NOT a facade.

## Fixture Location

**All fixtures must live in `automation/fixtures/`, never inside test files.**

See `.claude/rules/api-patterns.md` → Anti-Patterns → "Don't define fixtures inside test files"
for the full rule, examples, and rationale.

## Test Data Lifecycle

**Always clean up test data, even on failure:**

```python
# ✅ Option 1: Use fixtures (preferred)
def test_something(page, agent_id):  # Fixture creates & deletes
    agent_page = AgentPage(page)
    agent_page.navigate_to_agent(agent_id)
    # Test logic

# ✅ Option 2: Manual cleanup with try/finally
def test_something(page, agent_api):
    agent_id = None
    try:
        agent = agent_api.create_agent(name="Test", description="Test")
        agent_id = agent["id"]
        # Test logic
    finally:
        if agent_id:
            agent_api.delete_agent(agent_id)
```

## Wait Patterns

**Use page object wait methods, not arbitrary sleeps:**

```python
# ❌ WRONG - Arbitrary sleep
def test_form(page):
    page.locator('button').click()
    page.wait_for_timeout(5000)  # Hope it's enough?

# ✅ CORRECT - Use page object wait methods
def test_form(page):
    form_page = AgentFormPage(page)
    form_page.click_save()
    form_page.wait_for_page_load()  # Waits for actual conditions
```

**For AI responses:** Use content stability wait:

```python
chat.send_message("Hello")
chat.wait_for_ai_response(initial_count=0)
chat.wait_for_message_content_stable(stable_duration_ms=2000, timeout=30000)
```

## Timeout Constants

**Define timeouts at module level for easy tuning:**

```python
# At top of test file
AI_RESPONSE_TIMEOUT = 30_000   # AI message generation
UI_ELEMENT_TIMEOUT = 10_000    # Buttons, dialogs, dropdowns
NAVIGATION_TIMEOUT = 15_000    # SPA route changes
FORM_SAVE_TIMEOUT = 15_000     # Form save + network settle
```

## Test Structure

**Use clear Given/When/Then structure:**

```python
@pytest.mark.p0
@pytest.mark.smoke
def test_create_agent_via_ui(page, agent_api):
    """Create agent through UI and verify in list.
    
    Steps:
    1. Navigate to create agent page
    2. Fill name + description + instructions
    3. Click Save
    4. Verify navigation to detail page
    5. Verify agent appears in list
    """
    # Given - Setup
    agent_name = "autotest_create_ui"
    
    # When - Action
    agent_page = AgentPage(page)
    agent_page.navigate_to_create_agent()
    agent_page.fill_agent_form(
        name=agent_name,
        description="Created by automation",
        instructions="Test instructions"
    )
    agent_page.click_save()
    
    # Then - Verification
    agent_page.wait_for_agent_detail()
    assert agent_page.get_name() == agent_name
    
    # Cleanup
    agent_id = agent_page.get_agent_id_from_info()
    agent_api.delete_agent(int(agent_id))
```

## Assertion Quality Standards

**Use descriptive assertions with failure messages:**

```python
# ❌ WRONG - Unclear failure
assert count > 0

# ✅ CORRECT - Clear failure message
assert count > 0, f"Expected at least 1 agent, got {count}"

# ✅ CORRECT - Descriptive assertion
assert agent_page.agent_exists_in_list("Test Agent"), (
    "Agent 'Test Agent' should appear in list after creation"
)
```

### ❌ Forbidden Patterns

**1. Trivial/Tautological Assertions (Always Forbidden):**
```python
# ❌ WRONG - Always passes, meaningless
assert True
assert x == x
assert 1 == 1
assert len([]) == 0

# ✅ CORRECT - Test actual behavior
assert chat_page.get_message_count() > 0
assert agent_page.is_save_enabled()
```

**2. Assertion-less Tests (Critical Violation):**
```python
# ❌ WRONG - Test doesn't verify anything!
def test_send_message(page):
    chat_page = ChatPage(page)
    chat_page.navigate()
    chat_page.send_message("Hello")
    # No assertions - test is useless!

# ✅ CORRECT - Verify the behavior
def test_send_message(page):
    chat_page = ChatPage(page)
    chat_page.navigate()
    
    initial_count = chat_page.get_message_count()
    chat_page.send_message("Hello")
    chat_page.wait_for_ai_response()
    
    assert chat_page.get_message_count() > initial_count
    assert chat_page.is_input_empty()
```

**3. UI Tests Without Interaction (Critical Violation):**
```python
# ❌ WRONG - Only checks visibility, never uses the element
def test_delete_button(page):
    chat_page = ChatPage(page)
    assert chat_page.delete_button.is_visible()
    assert chat_page.delete_button.is_enabled()
    # Test ends - button never clicked!

# ✅ CORRECT - Actually test the behavior
def test_delete_button(page):
    chat_page = ChatPage(page)
    initial_count = chat_page.get_message_count()
    
    # Verify button exists
    assert chat_page.delete_button.is_visible()
    
    # Perform the action
    chat_page.delete_button.click()
    chat_page.wait_for_network()  # BasePage method — wraps wait_for_load_state("networkidle")
    
    # Verify the result
    assert chat_page.get_message_count() < initial_count
```

**4. Race Conditions (Common UI Bug):**
```python
# ❌ WRONG - No wait between action and check
def test_send_message(page):
    chat_page = ChatPage(page)
    chat_page.send_message("Test")
    assert chat_page.get_message_count() > 0  # May fail - race condition!

# ✅ CORRECT - Wait for state change
def test_send_message(page):
    chat_page = ChatPage(page)
    initial_count = chat_page.get_message_count()
    
    chat_page.send_message("Test")
    chat_page.wait_for_ai_response(initial_count=initial_count)
    
    assert chat_page.get_message_count() > initial_count
```

**5. Hard-coded Sleeps Instead of Proper Waits:**
```python
# ❌ WRONG - Arbitrary timeout, flaky
def test_form_save(page):
    form_page = AgentFormPage(page)
    form_page.click_save()
    page.wait_for_timeout(3000)  # Hope it's enough?
    assert form_page.get_success_message()

# ✅ CORRECT - Wait for actual condition
def test_form_save(page):
    form_page = AgentFormPage(page)
    form_page.click_save()
    form_page.wait_for_page_load()  # Waits for real conditions
    assert form_page.get_success_message()
```

**6. Wrong Variable Assertions:**
```python
# ❌ WRONG - Checking wrong/stale variable
def test_delete_message(page):
    chat_page = ChatPage(page)
    count_before = chat_page.get_message_count()
    chat_page.delete_message(-1)
    assert count_before < chat_page.get_message_count()  # WRONG - should be >

# ✅ CORRECT - Check the right relationship
def test_delete_message(page):
    chat_page = ChatPage(page)
    count_before = chat_page.get_message_count()
    chat_page.delete_message(-1)
    chat_page.wait_for_network()  # BasePage method — never call page.wait_for_load_state() in tests
    count_after = chat_page.get_message_count()
    assert count_after < count_before, f"Count should decrease: {count_before} -> {count_after}"
```

**7. Raw `page.wait_for_load_state()` Instead of Page Object Method:**
```python
# ❌ WRONG - Raw Playwright call leaks through abstraction boundary
def test_delete_message(page):
    chat_page = ChatPage(page)
    chat_page.delete_message(-1)
    page.wait_for_load_state("networkidle", timeout=5000)  # BAD
    assert chat_page.get_message_count() < initial_count

# ✅ CORRECT - Use BasePage.wait_for_network() via page object
def test_delete_message(page):
    chat_page = ChatPage(page)
    chat_page.delete_message(-1)
    chat_page.wait_for_network(timeout=5000)  # Wraps networkidle, stays in page-object layer
    assert chat_page.get_message_count() < initial_count
```

**Why:** `BasePage.wait_for_network(timeout)` exists in every page object and wraps `page.wait_for_load_state("networkidle")`. Calling `page.wait_for_load_state()` directly in a test bypasses the page object layer. If the wait strategy ever changes (e.g., to a specific condition), it has to be updated in every test file instead of one method.

**Exception:** Inside page object methods, `self.page.wait_for_load_state(...)` is fine — the call is already behind an abstraction.

**8. Overly Broad Assertions:**
```python
# ❌ WRONG - Too permissive, doesn't catch bugs
assert agent_page.get_agent_count() > 0  # Should specify expected count
assert "success" in message.lower() or "error" in message.lower()  # Meaningless

# ✅ CORRECT - Specific expected values
assert agent_page.get_agent_count() == 3, "Should have exactly 3 agents after creation"
assert "Agent created successfully" in message
```

**8. Brittle Locators (Anti-pattern):**
```python
# ❌ WRONG - Breaks if structure changes
element = page.locator('div > div > div:nth-child(5) > span:nth-child(2)')

# ❌ WRONG - Text-based without context
button = page.locator('button:has-text("Save")')  # Which Save button?

# ✅ CORRECT - Use page object with semantic locators
form_page = AgentFormPage(page)
form_page.save_button.click()  # Page object uses role-based locator
```

**9. Testing Implementation Details:**
```python
# ❌ WRONG - Checks internal state
assert chat_page._message_cache is not None
assert agent._version == 2

# ✅ CORRECT - Tests user-visible behavior
assert chat_page.get_message_count() > 0
assert agent_page.get_version_display() == "Version 2"
```

## Markers

**Use appropriate pytest markers:**

```python
@pytest.mark.ui           # Requires browser
@pytest.mark.agents       # Agent-related tests
@pytest.mark.p0           # Critical priority
@pytest.mark.smoke        # Fast smoke test (<5 min suite)

def test_something(page):
    pass
```

**Priority markers:**
- `p0` - Critical, must pass for deploy
- `p1` - High priority
- `p2` - Medium priority
- `p3` - Low priority

## UI Test Coverage Requirements

**Every UI feature needs these test types:**

### 1. Happy Path Test (P0)
```python
@pytest.mark.p0
@pytest.mark.ui
def test_create_agent_success(page, agent_api):
    """User can create agent with valid inputs."""
    agent_page = AgentPage(page)
    agent_page.navigate_to_create_agent()
    
    agent_page.fill_form(name="Test Agent", description="Test Description")
    agent_page.click_save()
    
    agent_page.wait_for_agent_detail()
    assert agent_page.get_name() == "Test Agent"
```

### 2. Validation Test (P1)
```python
@pytest.mark.p1
@pytest.mark.ui
def test_create_agent_empty_name(page):
    """Form prevents submission with empty name."""
    form_page = AgentFormPage(page)
    form_page.navigate_to_create()
    
    form_page.name_input.fill("")
    form_page.description_input.fill("Valid Description")
    
    assert not form_page.is_save_enabled(), "Save should be disabled with empty name"
```

### 3. State Change Test (P1)
```python
@pytest.mark.p1
@pytest.mark.ui
def test_toggle_button_state(page):
    """Button toggles between enabled/disabled states."""
    page_obj = SomePage(page)
    
    # Initial state
    assert page_obj.toggle_button.is_enabled()
    
    # First toggle
    page_obj.toggle_button.click()
    page.wait_for_timeout(500)  # CSS transition
    assert not page_obj.toggle_button.is_enabled()
    
    # Toggle back
    page_obj.toggle_button.click()
    page.wait_for_timeout(500)
    assert page_obj.toggle_button.is_enabled()
```

### 4. Error Handling Test (P2)
```python
@pytest.mark.p2
@pytest.mark.ui
def test_network_error_handling(page, agent_api):
    """UI shows error message when API fails."""
    # Setup: Make API fail
    agent_api.set_failure_mode(True)
    
    form_page = AgentFormPage(page)
    form_page.navigate_to_create()
    form_page.fill_form(name="Test", description="Test")
    form_page.click_save()
    
    # Verify error shown to user
    assert form_page.get_error_message() is not None
    assert "failed" in form_page.get_error_message().lower()
```

## Test Isolation

**Each test should be independent:**

```python
# ✅ CORRECT - Fresh entity per test via fixture
def test_agent_detail(page, agent_id):  # Fixture creates unique agent
    agent_page = AgentPage(page)
    agent_page.navigate_to_agent(agent_id)
    # Test runs in isolation

# ❌ WRONG - Shared state between tests
shared_agent_id = None

def test_create():
    global shared_agent_id
    # Creates agent, stores ID
    
def test_edit():
    global shared_agent_id  # BAD - depends on test_create
    # Edits the agent
```

## Handling Flaky Elements

**For elements that require special handling:**

```python
# Hover-dependent elements
message.hover()
page.wait_for_timeout(500)  # Wait for CSS transition
button.click(force=True)

# MUI overlays
button.click(force=True)  # Bypass actionability check

# SPA navigation with retry
chat_page.navigate_to_chat(conversation_id)  # Has built-in retry
```

## Screenshot on Failure

**Screenshots are automatic via conftest.py, but you can take manual ones:**

```python
def test_complex_flow(page):
    agent_page = AgentPage(page)
    agent_page.navigate_to_create_agent()
    
    # Take screenshot at specific point for debugging
    agent_page.screenshot("before_save", "State before clicking save")
    
    agent_page.click_save()
```

## Common Anti-Patterns

❌ **Don't mix locators and page objects:**
```python
def test_mixed(page):
    agent_page = AgentPage(page)
    agent_page.navigate_to_create_agent()
    page.locator('input').fill("Test")  # BAD - breaks abstraction
```

❌ **Don't use page.wait_for_timeout() unless absolutely necessary:**
```python
def test_wait(page):
    page.locator('button').click()
    page.wait_for_timeout(3000)  # BAD - arbitrary wait
```

❌ **Don't check element attributes directly:**
```python
def test_check(page):
    assert page.locator('button').get_attribute('disabled') is None  # BAD
```

✅ **Use page object methods:**
```python
def test_check(page):
    form_page = AgentFormPage(page)
    assert form_page.is_save_enabled()  # GOOD
```
## References

- Page objects: `automation/pages/`
- Test examples: `automation/tests/ui/agents/test_agent_management.py`
- Fixtures: `automation/conftest.py`
- Related rules: `.claude/rules/api-tests.md` (for API-specific standards)
