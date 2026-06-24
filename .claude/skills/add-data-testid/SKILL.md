---
name: add-data-testid
description: Adds data-testid attributes to EliteaUI components for stable test locators. Use after Stage 2 (Explore UI) when elements lack testids. Automatically edits JSX files and provides ready-to-use locators.
argument-hint: <element-list-from-snapshot>
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_navigate
---

# Add data-testid Skill

Adds `data-testid` attributes to EliteaUI components for robust test automation locators.

**Input:** $ARGUMENTS — list of elements from Stage 2 snapshot (e.g., "Save button in agent form, Name input field")

## Naming Convention

**Format:** `{section}-{element}-{type}`

| Part | Description | Examples |
|------|-------------|----------|
| section | Page/feature area | `agent-form`, `chat`, `sidebar`, `settings` |
| element | What the element represents | `save`, `name`, `model-select`, `send` |
| type | Element type | `button`, `input`, `dropdown`, `toggle`, `link` |

**Examples:**
- `agent-form-save-button`
- `chat-message-input`
- `sidebar-agents-link`
- `settings-theme-toggle`
- `credentials-name-input`

## Process

### Step 1: Parse Elements from Snapshot

Extract elements from $ARGUMENTS. For each element, identify:
- **Text/label** — visible text or aria-label
- **Element type** — button, input, select, etc.
- **Context** — parent component, section of page

### Step 2: Search in EliteaUI

For each element, search the EliteaUI source:

```bash
# Search by visible text
Grep(pattern="Save|save", path="../EliteaUI/src", glob="*.jsx")

# Search by component type + context
Grep(pattern="<Button.*onClick", path="../EliteaUI/src/[fsd]/features/agent", glob="*.jsx")

# Search by aria-label
Grep(pattern='aria-label="Save"', path="../EliteaUI/src", glob="*.jsx")
```

**Search strategy:**
1. First try exact text match
2. Then try component type in expected directory
3. Then broaden search to entire src/

### Step 3: Identify JSX Location

Read the file and find the exact element:

```javascript
// BEFORE - element without testid
<Button onClick={handleSave}>Save</Button>

// AFTER - element with testid
<Button data-testid="agent-form-save-button" onClick={handleSave}>Save</Button>
```

**Placement rules:**
- Add `data-testid` as FIRST attribute after opening tag
- Keep existing attributes unchanged
- For MUI components, testid goes on the MUI component directly

### Step 4: Apply Changes

Use Edit tool to add `data-testid` to each element:

```
Edit(
  file_path="c:/Users/.../EliteaUI/src/[fsd]/features/agent/ui/.../AgentForm.jsx",
  old_string='<Button onClick={handleSave}>',
  new_string='<Button data-testid="agent-form-save-button" onClick={handleSave}>'
)
```

**CRITICAL:** 
- Only edit files in `EliteaUI/src/` directory
- Verify the element is unique before editing (check for duplicates)
- If element appears in multiple places, add context to testid (e.g., `agent-form-save-button` vs `pipeline-form-save-button`)

### Step 5: Verify Changes

After all edits, take a new snapshot to confirm testids are present:

```
mcp__playwright__browser_snapshot()
```

Look for `data-testid` attributes in the snapshot output.

**Note:** Vite HMR should auto-reload. If not visible, the test should call `page.reload()`.

### Step 6: Output Report

Provide structured output for Stage 3 (Page Object Generator):

```
## Added data-testid Attributes

| Element | testid | File | Line |
|---------|--------|------|------|
| Save button | agent-form-save-button | src/[fsd]/features/agent/ui/AgentForm.jsx | 142 |
| Name input | agent-form-name-input | src/[fsd]/features/agent/ui/AgentForm.jsx | 87 |

## Ready Locators for Page Objects

**CRITICAL: data-testid MUST be used in BOTH testid AND fallback.**
Never use aria-label, role, or CSS selectors in fallback — always use the same data-testid.

```python
# LocatorDescriptor definitions - data-testid in BOTH fields
save_button = LocatorDescriptor(
    testid="agent-form-save-button",
    fallback=lambda page: page.locator('[data-testid="agent-form-save-button"]'),
    description="Save agent configuration"
)

name_input = LocatorDescriptor(
    testid="agent-form-name-input",
    fallback=lambda page: page.locator('[data-testid="agent-form-name-input"]'),
    description="Agent name input field"
)
```

## EliteaUI Changes Summary

Files modified: [count]
Branch: feat/EL-5226/add-data-test-ids-automation
```

---

## Edge Cases

### Element Not Found
If element cannot be located in EliteaUI:
1. Report which element couldn't be found
2. Provide the fallback locator (role/text-based) for page object
3. Continue with other elements

### Duplicate Elements
If same text appears multiple times:
1. Use more specific context in testid: `modal-save-button` vs `form-save-button`
2. Or add parent context: `agent-form-save-button` vs `pipeline-form-save-button`

### Dynamic/Generated Elements
For elements in loops (list items, messages):
1. Add testid to the container/wrapper
2. Use index-based selection in tests: `page.getByTestId("message-item").nth(0)`

### MUI Components
MUI forwards data-testid to the root element:
```jsx
<TextField data-testid="agent-form-name-input" label="Name" />
<Button data-testid="agent-form-save-button">Save</Button>
<Select data-testid="agent-form-model-dropdown" />
```

---

## Checklist

Before completing:
- [ ] All requested elements have testids added (or documented why not)
- [ ] Naming convention followed: `{section}-{element}-{type}`
- [ ] No duplicate testids introduced
- [ ] Changes are in correct EliteaUI branch
- [ ] Output includes ready-to-use LocatorDescriptor definitions
- [ ] Snapshot confirms testids are visible in DOM
