---
name: page-object-generator
description: Generate or refactor page objects using Playwright MCP. Use when creating new page objects, exploring page elements, refactoring existing pages to use LocatorDescriptor, or checking rule compliance.
argument-hint: <url-or-file> [create|refactor]
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(grep *)
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
  - mcp__playwright__browser_fill_form
  - mcp__playwright__browser_wait_for
  - mcp__playwright__browser_hover
  - mcp__playwright__browser_take_screenshot
---

# Page Object Generator

Generate or refactor Page Object Model code by exploring pages with Playwright MCP.

**Target:** $ARGUMENTS

## Mode Detection

| `$ARGUMENTS` contains | Mode |
|-----------------------|------|
| URL or path (`/app/...`, `http...`) | Create |
| Python file (`*.py`) | Refactor |
| Word `refactor` | Refactor |
| Neither | Ask user |

## Rules

**Read `.claude/rules/page-objects.md` before generating any code.** It contains:
- LocatorDescriptor pattern with testid + fallback
- Architecture pattern (list/form/detail + optional facade)
- Method naming conventions
- Common patterns (hover, MUI fields)
- Anti-patterns to avoid
- Validation checklist

**CRITICAL:** Facades delegate methods only, NEVER expose locators. Tests import specialized pages directly for locator access.

---

# MODE: CREATE

### Step 1: Navigate to Page

```
1. Construct URL from $ARGUMENTS + ELITEA_URL (.env.test)
2. Use browser_navigate to open page
3. If login required: browser_fill_form with TEST_USER_EMAIL/PASSWORD
4. browser_wait_for page to load
```

### Step 2: Snapshot and Analyze

Use `browser_snapshot` to capture page structure. Identify:
- **Forms**: inputs, dropdowns, textareas
- **Actions**: buttons, links
- **Lists**: repeating items, tables
- **Sections**: header, main content, sidebar

### Step 3: Explore Interactions

For complex elements:
1. `browser_hover` to reveal hidden buttons
2. `browser_click` to test dialogs/popovers
3. `browser_snapshot` again to capture dynamic content

### Step 4: Generate Code

Follow templates and patterns from `.claude/rules/page-objects.md`:
- Use LocatorDescriptor for ALL elements
- Add testid (even if not in frontend) + fallback
- Follow method naming conventions
- Document complex locators in docstrings

### Step 5: Output

Provide:
1. **Page Object Code** — Full Python file
2. **Usage Example** — Test snippet
3. **Discovered Elements** — Table with locators
4. **Frontend Recommendations** — testids to add

---

# MODE: REFACTOR

### Step R1: Analyze Existing Code

```bash
# Scan for issues
grep -n "page.locator" automation/pages/$ARGUMENTS
grep -n "def " automation/pages/$ARGUMENTS
```

### Step R2: Check Compliance

Compare against `.claude/rules/page-objects.md` checklist:
- [ ] LocatorDescriptor for all elements
- [ ] testid + fallback for each
- [ ] Method names follow conventions
- [ ] Class docstring includes URL
- [ ] No duplicate methods

### Step R3: Detect Duplicates

```bash
grep -rn "def method_name" automation/pages/ --include="*.py"
```

If duplicates: recommend moving to BasePage or shared parent.

### Step R4: Verify with Playwright MCP

1. Navigate to page
2. `browser_snapshot` to discover current elements
3. Compare against existing locators
4. Identify broken/outdated selectors

### Step R5: Apply Transformations

Follow transformation patterns from `.claude/rules/page-objects.md`:
- Convert direct locators → LocatorDescriptor
- Add missing fallbacks
- Extract inline selectors
- Remove duplicates via inheritance

### Step R6: Output

Provide:
1. **Compliance Report** — Before/after scores
2. **Changes Summary** — What was fixed
3. **Diff Preview** — Significant changes
4. **Frontend Recommendations** — testids to add

---

## References

- **Rules**: `.claude/rules/page-objects.md`
- **Examples**: `automation/pages/agent_form_page.py`
