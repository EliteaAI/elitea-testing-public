---
description: Page Object Model architecture rules for Playwright test automation
paths:
  - automation/pages/**/*.py
---

# Page Object Rules

## Critical: NO Method Duplication

**Never duplicate methods across page objects.** Use inheritance or composition:

```python
# ❌ WRONG - Duplicate method
class PageA:
    def get_name(self): return self.name_input.input_value()

class PageB:
    def get_name(self): return self.name_input.input_value()  # DUPLICATE!

# ✅ CORRECT - Inherit or compose
class FormPage(BasePage):
    def get_name(self): return self.name_input.input_value()

class DetailPage(FormPage):  # Inherits get_name()
    pass
```

## Locator Strategy: testid + fallback

**All locators must use `LocatorDescriptor`** with testid-first strategy:

```python
from .locator_descriptor import LocatorDescriptor

class MyPage(BasePage):
    element = LocatorDescriptor(
        testid="unique-testid",        # Most robust (data-testid)
        fallback=lambda page: page.get_by_role("button", name="Save"),  # Fallback
        description="What this element does"
    )
```

**Never use direct locators:**
```python
# ❌ WRONG
def __init__(self, page):
    self.button = page.locator('button')

# ✅ CORRECT
button = LocatorDescriptor(testid="save-btn", fallback=...)
```

## Architecture Pattern

**One class per responsibility:**

```
BasePage
├── EntityListPage      # /entities (dashboard/search)
├── EntityFormPage      # /entities/create (form operations)
│   └── EntityDetailPage  # /entities/{id} (inherits form + adds detail)
└── EntityPage (optional) # Facade - delegates methods, NO locators
```

**File naming:** `{entity}_list_page.py`, `{entity}_form_page.py`, `{entity}_detail_page.py`

### Facades vs Specialized Pages

**Facade** (optional convenience wrapper):
- Delegates method calls to specialized pages
- Does NOT expose locators
- Used when tests need operations from multiple pages
- Example: `EntityPage` wraps `EntityListPage`, `EntityFormPage`, `EntityDetailPage`

**Specialized Pages** (the actual page objects):
- Own their locators (LocatorDescriptor attributes)
- Implement page-specific methods
- Tests import these directly when they need locator access

**Rule:** If a test needs to access locators (form fields, buttons, etc.), import the specialized page directly, NOT the facade.

```python
# ❌ WRONG - Don't expose locators through facade
class EntityPage:
    def __init__(self, page):
        self.name_input = self._form_page.name_input  # BAD!

# ✅ CORRECT - Facade delegates methods only
class EntityPage:
    def __init__(self, page):
        self._form_page = EntityFormPage(page)
    
    def fill_form(self, name):
        return self._form_page.fill_form(name)  # Delegates

# ✅ CORRECT - Tests import specialized page for locators
from pages.entity_form_page import EntityFormPage

def test_edit_name(page):
    form = EntityFormPage(page)
    form.name_input.click()  # Direct locator access
```

## Locator Priority Order

1. **data-testid** - Most robust, future-proof
2. **Accessible roles** - `get_by_role("button", name="Text")`
3. **aria-label** - `locator('[aria-label="Delete"]')`
4. **Stable attributes** - `#element-id`
5. **CSS classes** - Last resort, fragile

**For elements without aria-label:** Document the locator strategy in docstring:

```python
def delete_message(self, index: int):
    """Delete message by hovering and clicking delete button.
    
    LOCATOR: Delete button has NO aria-label. Located as last button
    after hover. Button order: Copy (0), Regenerate (1), Delete (2).
    """
    message = self.messages_container.nth(index)
    message.hover()
    buttons = message.locator('button')
    buttons.last.click(force=True)  # Last button = Delete
```

## Inheritance Rules

**Use inheritance when:**
- Child page uses ALL parent functionality
- Example: `AgentDetailPage(AgentFormPage)` - detail page uses form

**Don't inherit when:**
- Pages are unrelated
- Only need a few methods - use composition instead

## Method Naming

- Navigation: `navigate()`, `navigate_to_create()`
- Wait: `wait_for_page_load(timeout: int = 15000)`
- Getters: `get_name()`, `get_items()`, `is_visible()`, `element_exists()`
- Actions: `fill_form()`, `click_save()`, `select_option()`

## Smart Navigation Pattern

**Navigation methods should wait automatically.** Don't force tests to call separate wait methods.

```python
# ✅ CORRECT - navigate() waits automatically
def navigate(self, entity_id: int):
    """Navigate to entity page and wait until ready."""
    super().navigate(f"/app/entities/{entity_id}")
    self.wait_for_page_load()  # Auto-wait
    
# ✅ CORRECT - Action methods wait for completion
def click_save(self):
    """Click save and wait for save to complete."""
    self.save_button.click()
    self.wait_for_network()  # Auto-wait

# ✅ CORRECT - Keep explicit wait for special cases
def wait_for_page_load(self):
    """Explicit wait - use after reload or external navigation."""
    self.wait_for_network()
    self.name_input.wait_for(state="visible")
```

**In tests:**
```python
# ✅ CORRECT - Clean and concise
detail_page = EntityDetailPage(page)
detail_page.navigate(entity_id)  # Waits automatically
detail_page.name_input.click()   # Ready to interact

# ✅ CORRECT - Explicit wait after reload
page.reload()
detail_page.wait_for_page_load()  # Explicit - makes sense

# ❌ WRONG - Redundant wait
detail_page.navigate(entity_id)
detail_page.wait_for_page_load()  # Redundant! navigate() already waits
```

**Benefits:**
- **DRY** - Don't repeat waits in every test
- **Encapsulation** - Page knows its own loading conditions
- **Cleaner tests** - Focus on actions, not waiting
- **Less verbose** - 1 line instead of 2

## Required Documentation

**Class docstring:**
```python
class AgentDetailPage(AgentFormPage):
    """Agent detail/edit page.
    
    Inherits form operations from AgentFormPage.
    Adds toolkit management, embedded chat, and actions menu.
    
    URL: /app/agents/all/{id}
    """
```

**Method docstring for complex operations:**
```python
def add_toolkit(self, toolkit_name: str, timeout: int = 10000):
    """Add external toolkit to agent.
    
    Opens toolkit popper, searches by name, selects from dropdown.
    Waits for toolkit card to appear in configuration.
    
    Args:
        toolkit_name: Name of toolkit (e.g. "GitHub")
        timeout: Maximum wait time in ms
    """
```

## Common Patterns

**Hover-dependent elements:**
```python
element.scroll_into_view_if_needed()
element.hover()
self.page.wait_for_timeout(500)  # Wait for CSS transition
button.click(force=True)  # Bypass visibility check if needed
```

**MUI form fields (React onChange):**
```python
# ❌ WRONG - fill() doesn't trigger React onChange
field.fill("value")

# ✅ CORRECT - click + press_sequentially triggers onChange
field.click()
field.clear()
field.press_sequentially("value", delay=50)
```

**Reusable MUI components:**
```python
from components.mui import Dialog, Popper

Dialog.wait_for(page)
Dialog.click_button(dialog, "Confirm")

Popper.open(page, trigger_button)
Popper.select_option(page, "Option Name")
```

## Anti-Patterns

❌ **Don't use locators in tests:**
```python
def test_save(page):
    page.locator('button').click()  # BAD - locator in test
```

✅ **Use page object methods:**
```python
def test_save(page):
    my_page = MyPage(page)
    my_page.click_save()  # GOOD
```

❌ **Don't hardcode selectors in methods:**
```python
def click_save(self):
    self.page.locator('button:has-text("Save")').click()  # BAD
```

✅ **Use LocatorDescriptor:**
```python
save_button = LocatorDescriptor(testid="save", fallback=...)
def click_save(self):
    self.save_button.click()  # GOOD
```

## Sign off Checklist

Verify:
- [ ] No duplicate methods across page objects
- [ ] All locators use LocatorDescriptor with testid + fallback
- [ ] Complex locators documented in docstring
- [ ] Method names follow conventions
- [ ] Class docstring includes URL pattern
- [ ] Tests don't contain direct page.locator() calls

## Test Imports - Which Page Object to Use

**Rule:** Import the specialized page that matches your test's context.

### Dashboard/List Tests
```python
from pages.agents_list_page import AgentsListPage

def test_agent_search(page):
    list_page = AgentsListPage(page)
    list_page.search_input.fill("query")  # Locator access
    list_page.search("query")             # Or use method
```

### Create/Edit Form Tests
```python
from pages.agent_form_page import AgentFormPage

def test_fill_form(page):
    form_page = AgentFormPage(page)
    form_page.name_input.click()       # Locator access
    form_page.fill_form(name="Test")   # Or use method
```

### Detail Page Tests
```python
from pages.agent_detail_page import AgentDetailPage

def test_agent_detail(page, agent_id):
    detail_page = AgentDetailPage(page)
    detail_page.navigate(agent_id)
    detail_page.name_input.click()     # Inherited from AgentFormPage
    detail_page.add_toolkit("GitHub")  # Detail-specific method
```

### Multi-Operation Tests (Use Facade)
```python
from pages.agent_page import AgentPage  # Facade

def test_full_workflow(page):
    agent = AgentPage(page)  # Convenience wrapper
    agent.navigate_to_agents()    # Delegates to list
    agent.click_create_agent()    # Delegates to list
    agent.fill_agent_form(...)    # Delegates to form
    # BUT if you need locator access, import specialized page!
```

**Summary:** Facades are for convenience when calling methods. Specialized pages are for locator access.

## References

- Examples: `agent_page.py`, `agent_detail_page.py`, `agent_form_page.py`
- Components: `automation/components/mui.py`
