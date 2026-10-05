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

## Locator Strategy: the ladder (dev-targeted factory, 2026-10)

The factory builds tests against the **DEV env as deployed** — it never adds
testids. Every locator is a class-level `LocatorDescriptor` declared with **one
explicit kind**, picked by the ladder: the first rung that **uniquely and stably**
identifies the element on DEV wins.

| Rung | Kind | Use when | Example |
|---|---|---|---|
| 1 | `testid=` | the element already carries a `data-testid` on DEV | `LocatorDescriptor(testid="agent-form-save-button")` |
| 2 | `role=` (+ `name=`, `exact=`) | ARIA role + accessible name is unique | `LocatorDescriptor(role="button", name="Save", suggested_testid="agent-form-save-button")` |
| 3 | `label=` | form control with a `<label>` / `aria-label` | `LocatorDescriptor(label="Name", suggested_testid="agent-form-name-input")` |
| 4 | `css=` | stable `id` / attribute CSS (`#id`, `[name="x"]`, `[aria-label="x"]`) | `LocatorDescriptor(css='input[name="username"]', suggested_testid="login-username-input")` |
| 5 | `xpath=` | **declared last resort** — nothing above works; say why in `description=` | `LocatorDescriptor(xpath="//span[text()='Repository']/ancestor::div[@role='group']//input", suggested_testid="toolkit-test-settings-repository-input", description="…why…")` |

**Every non-testid declaration MUST carry `suggested_testid=`** — the
`{section}-{element}-{type}` testid the weekly **testid migrator** will add to
EliteaUI and swap in. It is enforced at import time (`ValueError`), and it is what
makes the migration mechanical (`automation/scripts/locator_inventory.py` reads it).
Name it exactly as you would name the testid (call-site section, kebab-case,
dynamic ones end in `-{}`).

**Enforced at import time** (`pages/locator_descriptor.py` `_validate()` — a
violation fails collection, it cannot ship):
- exactly one kind; `name=` only with `role=`; `exact=` only with `role=`/`label=`
- positional CSS (`:nth-child`, `:first-of-type`, `>> nth=`) and positional /
  absolute XPath (`[2]`, `last()`, `position()`, `/html/…`) are **forbidden**
- `css='[data-testid=…]'` is rejected — use `testid=`
- engine-prefixed strings (`text=…`, `xpath=…` inside `css=`) are rejected
- `suggested_testid` must be kebab-case and only on non-testid kinds

**Picking a rung — rules of thumb:**
- Check DEV for an existing testid first (Playwright MCP snapshot / DOM). The UI
  team adds testids continuously — an existing one always wins.
- `role`+`name` beats CSS whenever the accessible name is stable text the case
  itself names. Avoid names that embed user data, counts or the selected model.
- Never locate by MUI generated classes (`css-1pybsfx`, `MuiList-root`) — they
  change between builds. That is not "stable CSS".
- Never locate by position (`.nth(i)`, `.first`, `.last` to pick among siblings)
  — scope to a declared parent instead and let the rung be unique inside it.
  `.first` on a set you've proven unique is a no-op and acceptable.

Locators live **only as class-level fields on page objects** — never constructed
inside method bodies, never in test/spec files. `locator=` and `fallback=` are
LEGACY parameters (old code keeps importing) and are **never valid in new or
modified declarations**.

```python
from .locator_descriptor import LocatorDescriptor, ScopedLocator

class MyPage(BasePage):
    save_button = LocatorDescriptor(testid="agent-form-save-button", description="Save the form")
    name_input = LocatorDescriptor(label="Name", suggested_testid="agent-form-name-input")
    delete_button = LocatorDescriptor(
        role="button", name="Delete", exact=True, suggested_testid="agent-form-delete-button"
    )
```

```python
# ❌ WRONG — locator built in a method
def __init__(self, page):
    self.button = page.locator('button')

# ❌ WRONG — legacy params in new code
button = LocatorDescriptor(testid="save-btn", fallback=lambda page: ...)
button = LocatorDescriptor(locator='[aria-label="Delete"]')

# ❌ WRONG — non-testid without the migration hint (raises ValueError)
button = LocatorDescriptor(role="button", name="Delete")

# ❌ WRONG — positional (raises ValueError)
row = LocatorDescriptor(css="li:nth-child(2)", suggested_testid="x-row")

# ✅ CORRECT
button = LocatorDescriptor(role="button", name="Delete", suggested_testid="agent-delete-button")
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

## Locator Rules

**Scoped and dynamic locators — `ScopedLocator` (any rung) or an UPPER_CASE
`[data-testid=…]` constant (testid rung).** Both are class-level, so every handle
stays in the inventory; both resolve inside a parent at call time.

```python
from .locator_descriptor import ScopedLocator

class ChatPage(BasePage):
    messages = LocatorDescriptor(testid="chat-message-list")
    # testid rung, scoped — string constant
    CHAT_DELETE_SELECTOR = '[data-testid="chat-message-delete-button"]'
    # non-testid rung, scoped — ScopedLocator with the migration hint
    MESSAGE_COPY_BUTTON = ScopedLocator(
        role="button", name="Copy to clipboard", suggested_testid="chat-message-copy-button"
    )

    def copy_message(self, message: Locator) -> None:
        self.MESSAGE_COPY_BUTTON.within(message).click()

    def delete_message(self, message: Locator) -> None:
        message.locator(self.CHAT_DELETE_SELECTOR).click()
```

**Dynamic (runtime-parameterized) locators — same mechanisms, templated with `{}`:**
```python
# ✅ testid rung — class-level template constant
SKILL_TAG_OPTION = '[data-testid="skill-tag-option-{}"]'
def select_tag(self, tag_name: str):
    self.page.locator(self.SKILL_TAG_OPTION.format(tag_name)).click()

# ✅ non-testid rung — ScopedLocator template; args fill every {} placeholder
TAG_OPTION = ScopedLocator(role="option", name="{}", suggested_testid="skill-tag-option-{}")
def select_tag(self, tag_name: str):
    self.TAG_OPTION.within(self.page, tag_name).click()

# ❌ WRONG — inline f-string locator in a method body (invisible to the inventory)
def select_tag(self, tag_name: str):
    self.page.get_by_role("option", name=tag_name).click()
```
Naming for dynamic hints/testids: `{section}-{element}-{param}` → `…-{}` (parameter last).
Template args are test-generated data only.

**Locators MUST be class-level fields, NEVER inline in methods:**
```python
# ❌ WRONG - inline locator in method
def click_save(self):
    self.page.get_by_role("button", name="Save").click()

# ✅ CORRECT - class-level LocatorDescriptor
save_button = LocatorDescriptor(role="button", name="Save", suggested_testid="agent-form-save-button")
def click_save(self):
    self.save_button.click()
```

**Measure, don't guess.** `../.venv/bin/python scripts/locator_inventory.py scan`
(from `automation/`) prints the locator-debt metric: non-testid declarations /
all declarations, plus "unmanaged handles" (raw calls in methods — legacy debt).
New code adds declarations, never unmanaged handles.

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

✅ **Use a class-level declaration:**
```python
save_button = LocatorDescriptor(role="button", name="Save", suggested_testid="agent-form-save-button")
def click_save(self):
    self.save_button.click()  # GOOD
```

❌ **Don't chain a raw selector off an existing field inside a method** — it
looks compliant (it starts from a real class field) but bakes an untracked
selector into method code. Real case (`automation/pages/skill_form_page.py`,
ELITEA-1737):
```python
instructions_editor = LocatorDescriptor(testid="skill-instructions-editor")

def get_instructions_text(self):
    content = self.instructions_editor.locator(".cm-content")  # BAD - raw CSS chained on
    return content.text_content()
```

✅ **Declare the sub-element — its own field, or a `ScopedLocator` resolved inside the parent:**
```python
instructions_editor = LocatorDescriptor(testid="skill-instructions-editor")
EDITOR_CONTENT = ScopedLocator(css=".cm-content", suggested_testid="skill-instructions-editor-content")

def get_instructions_text(self):
    return self.EDITOR_CONTENT.within(self.instructions_editor).text_content()  # GOOD
```
(Third-party editor internals like CodeMirror's `.cm-content` are a legitimate
`css=` rung — the class is the library's public contract, not a generated MUI hash.)

❌ **Don't pick among siblings by position:**
```python
self.toolbar_buttons.nth(2).click()  # BAD - breaks when a button is added
```

✅ **Declare the element by what it is:**
```python
regenerate_button = LocatorDescriptor(role="button", name="Regenerate", suggested_testid="chat-message-regenerate-button")
```

## Sign off Checklist

Verify:
- [ ] No duplicate methods across page objects
- [ ] Every locator is a class-level `LocatorDescriptor` / `ScopedLocator` /
      UPPER_CASE `[data-testid=` constant — nothing built in method bodies or specs
- [ ] Each declaration uses the highest ladder rung that is unique on DEV
      (existing testid first)
- [ ] Every non-testid declaration carries a correctly named `suggested_testid=`
- [ ] No `locator=` / `fallback=` in new or modified declarations
- [ ] No positional selectors (`nth`, `:nth-child`, `[2]`, `last()`) and no MUI
      generated classes
- [ ] No raw selectors chained off an existing field inside a method
- [ ] Every `xpath=` declaration says in `description=` why rungs 1–4 failed
- [ ] Complex locators documented in docstring
- [ ] Method names follow conventions
- [ ] Class docstring includes URL pattern
- [ ] Tests don't contain direct `page.locator()` / `get_by_*()` calls

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
