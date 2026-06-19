---
description: MUI/EliteAUI component interaction patterns and common pitfalls
paths:
  - automation/pages/**/*.py
  - automation/tests/ui/**/*.py
---

# MUI / EliteAUI Interaction Patterns

## Message Locators

**CRITICAL:** All chat messages (regular chat, agent-participant chat, embedded chat) render as `<ul class="MuiList-root"> <li class="MuiListItem-root">`.

```python
# ✅ CORRECT - Matches MUI List structure
messages = page.locator('main ul.MuiList-root > li.MuiListItem-root')

# ❌ WRONG - Matches config panels on agent pages
messages = page.locator('main div:has(> p)')  # BAD - too broad!
```

**Why `div:has(> p)` fails:**
- Agent detail pages have configuration panels with `<div><p>` structure
- This matches those panels instead of messages
- Results in incorrect message counts

**Source:** EliteAUI `src/components/Chat/ChatMessageList.jsx` renders `<UserMessage>` and `<ApplicationAnswer>` inside `<MessageList>` (styled MUI `<List>`).

---

## Extracting Message Text

**NEVER use `text_content()` directly on the `<li>` element** — it includes header metadata (sender name, timestamp, model).

```python
# ❌ WRONG - Gets header + body
message_li = page.locator('li.MuiListItem-root').last
text = message_li.text_content()  # "Claude Opus 12:34 PM\nYour message here"

# ✅ CORRECT - Extract body only
def _extract_message_body(message_locator):
    """Extract message body text without header metadata."""
    # Try <p> tags (AI messages via Markdown component)
    paragraphs = message_locator.locator('p')
    if paragraphs.count() > 0:
        texts = [paragraphs.nth(i).text_content() for i in range(paragraphs.count())]
        return '\n'.join(texts)
    
    # Try .MuiTypography-bodyMedium (user messages)
    body = message_locator.locator('.MuiTypography-bodyMedium')
    if body.count() > 0:
        return body.first.text_content() or ""
    
    # Streaming in progress or empty
    return ""
```

**Rule:** Always use `_extract_message_body()` or similar extraction method. Never call `text_content()` on the message `<li>` directly.

---

## MUI Form Fields (React onChange)

**MUI form inputs do NOT fire React's `onChange` on Playwright's `fill()` method.**

```python
# ❌ WRONG - Value appears in DOM but React state doesn't update
field.fill("my value")
assert form.is_save_enabled()  # Still disabled!

# ✅ CORRECT - Triggers React onChange via keyboard events
field.click()
field.press("Control+a")  # Select all
field.type("my value")     # Type character by character
```

**Why this happens:**
- Playwright's `fill()` sets the value directly via JavaScript
- React doesn't see this as user input
- `onChange` handler never fires
- Form validation state doesn't update

**Alternative (for single-line inputs):**
```python
# ✅ Also works - press_sequentially triggers onChange
field.click()
field.clear()
field.press_sequentially("my value", delay=50)
```

**When to use each:**
- `type()` - For replacing existing content (with Ctrl+A)
- `press_sequentially()` - For empty fields or appending
- `fill()` - **NEVER** for MUI/React form fields

---

## MUI Overlay Interception

MUI renders invisible overlay `<div>` elements that intercept pointer events during animations.

```python
# ❌ WRONG - Fails with "Element is not clickable"
button.click()  # Error: Element <button> is obscured by <div class="css-1pybsfx">

# ✅ OPTION 1 - Force click (bypasses actionability checks)
button.click(force=True)

# ✅ OPTION 2 - JavaScript click (bypasses Playwright's click entirely)
button.evaluate("el => el.click()")
```

**When to use each:**
- `force=True` - For elements that are visible but overlaid (conversation list items, view toggles)
- `evaluate("el => el.click()")` - For Save buttons during streaming, critical actions

**Common overlay classes:**
- `css-1pybsfx`
- `css-1b98wmy`
- `MuiBackdrop-root` with high z-index

**Rule:** If you see "Element is not clickable" errors, try `force=True` first. Use `evaluate()` for Save buttons.

---

## MUI Popper / Dropdown Pattern

Agent toolkit search, credential dropdowns, participant search all use `MuiPopper-root`.

```python
# ✅ CORRECT pattern
# 1. Click trigger button
add_btn.click(force=True)  # MUI overlay may intercept

# 2. Wait for popper
popper = page.locator('.MuiPopper-root')
popper.wait_for(state="visible", timeout=10000)

# 3. Optional: Search within popper
search_input = popper.locator('input[placeholder*="Search"]')
if search_input.count() > 0:
    search_input.first.fill("query")
    page.wait_for_timeout(500)  # Search debounce

# 4. Select from menu items
# IMPORTANT: Use role="menuitem", NOT role="option"
option = popper.locator('li[role="menuitem"]:has-text("Name")').first
option.click()
page.wait_for_timeout(1000)  # Selection settle
```

**Common mistakes:**
```python
# ❌ WRONG - Using role="option"
option = popper.locator('[role="option"]')  # Not used in MUI Menu

# ❌ WRONG - Not waiting for popper
add_btn.click()
page.locator('li:has-text("GitHub")').click()  # Fails - popper not ready

# ❌ WRONG - Not handling MUI overlay on trigger
add_btn.click()  # Fails - overlay intercepts
```

**Toolkit popper gotcha:** Names display with spaces removed ("My Toolkit" → "MyToolkit"). Match against `toolkit_name.replace(" ", "")`.

---

## MUI Debounce Patterns

MUI form fields have debounce delays for validation.

```python
# ❌ WRONG - Checks immediately, validation hasn't run yet
form.fill_form(name="Test", description="Desc")
assert form.is_save_enabled()  # Fails - validation pending

# ✅ CORRECT - Wait for debounce
form.fill_form(name="Test", description="Desc")
page.wait_for_timeout(500)  # MUI debounce (300-500ms typical)
assert form.is_save_enabled()

# ✅ BETTER - Encapsulate in page object
def wait_for_form_validation(self, timeout=1000):
    """Wait for MUI form validation to complete."""
    self.wait_for_network(timeout=1000)
    self.page.wait_for_timeout(500)  # MUI debounce
```

**Typical debounce times:**
- Form validation: 300-500ms
- Search inputs: 500-1000ms
- Auto-save: 1000-2000ms

**Rule:** After filling form fields, wait 500ms before checking validation state.

---

## MUI Animation Waits

MUI components have CSS transitions that require waiting.

```python
# ✅ View switching
list_page.table_view_button.click(force=True)
page.wait_for_timeout(500)  # View switch animation

# ✅ Dialog opening
dialog_trigger.click()
page.wait_for_timeout(300)  # Fade-in animation
dialog = page.locator('[role="dialog"]')
dialog.wait_for(state="visible")

# ✅ Scroll operations
element.scroll_into_view_if_needed()
page.wait_for_timeout(500)  # Smooth scroll settle
```

**Typical animation times:**
- Dialogs: 300ms fade
- View switches: 500ms transition
- Scroll: 500ms smooth scroll
- Hover effects: 200-300ms

**Rule:** After triggering animations, wait for settle before interacting with new elements.

---

## Stable Aria Labels Reference

Some elements have reliable `aria-label` attributes:

| Element | aria-label | Notes |
|---------|-----------|-------|
| Copy message | `Copy to clipboard` | Stable |
| Create Conversation | `Create Conversation` | Stable |
| Search conversations | `Search conversations` | Stable |
| Send message | `send your question` | Stable |
| Add agent (sidebar) | `Add agent` | Stable |
| Add toolkit | `Add toolkit` | Stable |
| Delete toolkit | `delete tool` | Stable |
| Refresh agents | `Refresh the agents` | Stable |

**Elements WITHOUT aria-label:**

| Element | How to locate | Notes |
|---------|--------------|-------|
| Delete message | Last button after hover | Order: Copy (0), Regenerate (1), Delete (2) |
| Tab elements | `get_by_role("tab", name="Configuration")` | Use visible text |
| View toggles | `get_by_role("button", name="Table view")` | Use visible text |

```python
# ✅ For elements with aria-label
copy_btn = page.get_by_label("Copy to clipboard")

# ✅ For elements without aria-label - document strategy
def delete_message(self, index: int):
    """Delete message by hovering and clicking delete button.
    
    LOCATOR: Delete button has NO aria-label. Located as last button
    after hover. Button order: Copy (0), Regenerate (1), Delete (2).
    """
    message = self.messages_container.nth(index)
    message.hover()
    page.wait_for_timeout(500)  # Hover effect animation
    buttons = message.locator('button')
    buttons.last.click(force=True)  # Last button = Delete
```

---

## Test Settings Panel (Toolkit Detail Page)

Tool parameter fields have **NO accessible names** — must locate by label text.

```python
# ❌ WRONG - No accessible name/label/placeholder
field = page.get_by_label("Repository")  # Doesn't exist

# ✅ CORRECT - Find by label text in container
field_input = page.locator('.index-config-field:has(span:text("Repository")) input')

# ✅ BETTER - Filter to right panel (x > 700px)
field_locator = page.locator('.index-config-field:has(span:text("Repository")) input')
for i in range(field_locator.count()):
    box = field_locator.nth(i).bounding_box()
    if box and box["x"] > 700:  # Right panel
        target_field = field_locator.nth(i)
        break

target_field.fill("owner/repo")
```

**Why this is necessary:**
- Test Settings panel has no testids
- Field labels are `<span>` elements, not `<label>`
- Left config panel may have duplicate field names
- Must distinguish by position or parent container

**Rule:** For Test Settings fields:
1. Find by label text in parent container
2. Filter by position (right panel: x > 700px)
3. Document the locator strategy in method docstring

---

## "Run Tool" Button State

The "Run Tool" button stays disabled until all required params are filled.

```python
# ✅ Wait for button to enable
page.wait_for_function("""() => {
    const buttons = document.querySelectorAll('button');
    for (const b of buttons) {
        if (b.textContent.includes('Run Tool')) return !b.disabled;
    }
    return false;
}""", timeout=10000)

run_button = page.locator('button:has-text("Run Tool")')
run_button.click()
```

**Why wait_for_function:**
- Button exists in DOM immediately (no need to wait for element)
- But it's disabled until validation passes
- `wait_for_function` polls until condition is true

---

## Hover-Dependent Elements

Some actions only appear on hover (delete, edit, etc.).

```python
# ✅ CORRECT pattern
element.scroll_into_view_if_needed()
element.hover()
page.wait_for_timeout(500)  # CSS transition for hover effect
delete_btn.click(force=True)  # May need force if overlay present
```

**Elements commonly requiring hover:**
- Message delete buttons
- Toolkit card actions
- Conversation rename/delete
- Agent card actions

**Rule:** For hover-dependent elements:
1. Scroll into view if needed
2. Hover over container
3. Wait 500ms for CSS transition
4. Use `force=True` if click is intercepted

---

## Anti-Patterns

❌ **Don't use `fill()` for MUI form fields:**
```python
field.fill("value")  # React state doesn't update
```

✅ **Use `click()` + `type()` or `press_sequentially()`:**
```python
field.click()
field.press("Control+a")
field.type("value")
```

❌ **Don't use `div:has(> p)` for message locators:**
```python
page.locator('div:has(> p)')  # Matches config panels too!
```

✅ **Use `ul.MuiList-root > li.MuiListItem-root`:**
```python
page.locator('ul.MuiList-root > li.MuiListItem-root')
```

❌ **Don't call `text_content()` on message `<li>`:**
```python
message.text_content()  # Includes header metadata
```

✅ **Extract body only:**
```python
_extract_message_body(message)  # Body text only
```

---

## References
- MUI Components: `automation/components/mui.py` (Dialog, Popper helpers)
- Page Examples: `automation/pages/chat_page.py`, `automation/pages/agent_detail_page.py`
