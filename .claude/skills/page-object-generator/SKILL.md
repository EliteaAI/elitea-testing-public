---
name: page-object-generator
description: Generate or refactor page objects using Playwright MCP against the DEV env, emitting class-level ladder locators (existing testid → role+name → label → stable css → declared xpath, every non-testid one carrying suggested_testid=). Use when creating new page objects, exploring page elements, refactoring existing pages to use LocatorDescriptor, or checking rule compliance.
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

**Explored environment: the DEV env as deployed** (`https://dev.elitea.ai`,
`APP_PREFIX=/app`). Refresh the storage state before the first browser call —
`cd automation && ../.venv/bin/python scripts/dev_storage_state.py`. Whatever the
DOM serves there is the ground truth for every locator this skill emits; there is
no other environment to consult and no frontend change to wait for.

## Mode Detection

| `$ARGUMENTS` contains | Mode |
|-----------------------|------|
| URL or path (`/app/...`, `http...`) | Create |
| Python file (`*.py`) | Refactor |
| Word `refactor` | Refactor |
| Neither | Ask user |

## Rules

**Read `.claude/rules/page-objects.md` before generating any code.** It contains:
- LocatorDescriptor pattern — **the locator ladder**, `suggested_testid=` on every
  non-testid rung (`fallback=`/`locator=` are legacy, never generated)
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

- **Every element is a class-level declaration** — `LocatorDescriptor` /
  `OptionalLocatorDescriptor` / `ScopedLocator`, or an UPPER_CASE
  `[data-testid="…"]` constant. Never a locator built inside a method body,
  never a raw selector chained off another field, never one in a spec.
- **Pick the first ladder rung that is unique and stable in the DEV DOM you just
  snapshotted.** Exactly one kind per declaration:

  | Rung | Param | Use when |
  |---|---|---|
  | 1 | `testid=` | the element already carries a `data-testid` on DEV — always check first |
  | 2 | `role=` + `name=` | ARIA role + a stable accessible name |
  | 3 | `label=` | form control with `<label>` / `aria-label` |
  | 4 | `css=` | stable `id` / attribute (`#id`, `[name="x"]`), or a third-party library's public class (`.cm-content`, `.react-flow__node`) — **never** MUI generated/structural classes (`css-*`, `Mui*-root`) |
  | 5 | `xpath=` | declared last resort, with `description=` saying why rungs 1–4 failed |

- **A missing testid is NOT a blocker and NOT work for you.** Drop to the next
  rung that is unique and carry a `suggested_testid=` hint — that hint is the
  whole mechanism by which the testid eventually arrives. Never invent a
  `testid=` the DOM does not serve (`LocatorDescriptor` has no fallback, so the
  locator would simply never match).
- **`suggested_testid=` is mandatory on rungs 2–5** and enforced at import time
  (`ValueError` → collection fails). Name it exactly as the testid would be
  named: kebab-case `{section}-{element}-{type}`, section from the call site,
  dynamic ones ending `-{}`.
- **No positional handles, on any rung** — no `:nth-child`, `[2]`, `last()`,
  `position()`, absolute `/html/…`, no `.nth(i)` sibling pick. Scope to a
  declared parent instead. If an element is genuinely only reachable
  positionally, say so in the output as an open question rather than emitting one.
- **State is a filter, never a separate handle** — `aria-expanded`,
  `aria-selected`, `disabled`, or a `data-*` attribute DEV already renders
  (`'[data-testid="x"][data-expanded="false"]'`). Never `-expanded` / `-collapsed`
  handle variants.
- Scoped / dynamic handles: `ScopedLocator(..., suggested_testid="…")` +
  `.within(scope, *args)` (any rung), or a `[data-testid="…-{}"]` template
  constant + `.format()` at the call site (rung 1 only).
- Follow method naming conventions.
- Document complex locators in docstrings; an `xpath=` rung documents itself via
  `description=`.

### Step 5: Output

Provide:
1. **Page Object Code** — Full Python file
2. **Usage Example** — Test snippet
3. **Discovered Elements** — one row per element: `rung` | `handle` |
   `suggested_testid` | provenance (`testid on DEV ✓`, or the rung you verified
   unique in the snapshot)
4. **Open questions** — anything reachable only positionally, or an element whose
   accessible name embeds user data / counts / the selected model, so the lead can
   route it. Not "testids to add" — nothing here asks the frontend for anything.

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
- [ ] Every locator is a class-level declaration — zero raw selectors in method
      bodies, dynamic ones as `ScopedLocator` or class-level template constants
- [ ] Zero `fallback=` / `locator=` params (legacy)
- [ ] Every non-testid declaration carries a well-formed `suggested_testid=`
- [ ] No positional handles (`:nth-child`, `[2]`, `last()`, `.nth(i)` picks)
- [ ] No MUI generated/structural classes (`css-*`, `Mui*-root`) as a `css=` rung
- [ ] Every `xpath=` has a `description=` justifying it
- [ ] Method names follow conventions
- [ ] Class docstring includes URL
- [ ] No duplicate methods

### Step R3: Detect Duplicates

```bash
grep -rn "def method_name" automation/pages/ --include="*.py"
```

If duplicates: recommend moving to BasePage or shared parent.

### Step R4: Verify with Playwright MCP

1. Navigate to the page on DEV
2. `browser_snapshot` to discover current elements
3. Compare against existing locators
4. Identify broken/outdated selectors — and, for each, the highest rung that is
   unique in the snapshot you just took

### Step R5: Apply Transformations

Follow transformation patterns from `.claude/rules/page-objects.md`:
- Raw locator in a method body → a class-level declaration on the highest ladder
  rung that is unique on DEV, with `suggested_testid=` if that rung isn't `testid=`
- A declaration already on `testid=` stays there — never descend a rung
- Strip `fallback=`/`locator=` from declarations being touched (legacy params)
- Extract inline selectors → class-level constants / `ScopedLocator` templates
- Replace positional picks with a declared parent scope
- Remove duplicates via inheritance

**Behaviour-preserving only.** Refactor mode changes how an element is *addressed*,
never what a test asserts or does. If a swap turns a test red, revert it and report
it — do not adjust the spec to fit.

**Climbing a declaration from a ladder rung to `testid=` is not this skill's job.**
That is the locator-migration process, which is ledger-driven and gated on the
testid being deployed. Leave the rung and the hint as they are.

### Step R6: Output

Provide:
1. **Compliance Report** — Before/after against the Step R2 checklist
2. **Changes Summary** — What was fixed, per declaration, with the rung chosen
3. **Diff Preview** — Significant changes
4. **Locator debt delta** — `cd automation && ../.venv/bin/python scripts/locator_inventory.py scan`
   before and after: declared total, non-testid count, unmanaged handles. Unmanaged
   handles must not increase.

---

## References

- **Rules**: `.claude/rules/page-objects.md` (mechanics, enforced at import time)
- **Policy**: `.agents/testing.md` § Locator policy (authoritative — the ladder,
  the `suggested_testid=` requirement, the locator-debt metric)
- **Examples**: `automation/pages/agent_form_page.py`
