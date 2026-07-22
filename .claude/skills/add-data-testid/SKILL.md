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

## Conventions (UI-team rulings — EliteaUI PR #581 review, 2026-07-16)

1. **Testid = stable identity; state via `data-*` attributes.** Never make a testid's
   presence or value depend on component state. Wrong: `data-testid={!isExpanded ?
   id : undefined}`, `data-testid={done ? 'x-complete' : 'x-preview'}`. Right:
   ```jsx
   data-testid={toggleTestId}
   data-expanded={isExpanded}
   ```
   Automation filters on the state attribute (`[data-testid="x"][data-expanded="false"]`).
2. **Shared components (`src/components/`, `src/[fsd]/shared/`) never hardcode a
   feature-scoped testid.** Use a GENERIC value (`search-send-button`) or accept a
   `testId` prop and wire the `{section}-…` value at the feature's call site — the
   section in the name is the CALLER's, not the shared component's first consumer.
3. **Testid props are named `testId` / `<part>TestId`** (`closeButtonTestId`) —
   never `dataTestId` / `<part>DataTestId`; the `data` prefix is redundant.

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

```python
# LocatorDescriptor definitions — testid only, no fallback needed
save_button = LocatorDescriptor(testid="agent-form-save-button")
name_input = LocatorDescriptor(testid="agent-form-name-input")
```

## EliteaUI Changes Summary

Files modified: [count]
Branch: automation/testids (commit born + pushed here; human cherry-picks to main)
```

---

## Edge Cases

### Element Not Found
If the element cannot be located in EliteaUI source:
1. Report which element couldn't be found (search terms tried, dirs covered)
2. **STOP+FLAG for that element — never emit a fallback/role/text locator**
   (testid-only policy: `.agents/testing.md` § Locator policy). The lead
   decides: deeper source hunt, UI-team question, or stop+flag exception
   (third-party widget)
3. Continue with the other elements

### Duplicate Elements
If same text appears multiple times:
1. Use more specific context in testid: `modal-save-button` vs `form-save-button`
2. Or add parent context: `agent-form-save-button` vs `pipeline-form-save-button`

### Dynamic/Generated Elements
For elements in loops (list items, messages):
1. Add testid to the container/wrapper; index-select in the page object
   (`.nth(i)`)
2. If items need identity (select-by-name), emit a PARAMETERIZED testid in the
   JSX (`data-testid={`skill-tag-option-${name}`}`) and report the pattern —
   the page object consumes it via a class-level template constant
   (`'[data-testid="skill-tag-option-{}"]'` + `.format()`), never an inline
   f-string `get_by_test_id`

### MUI Components
MUI forwards data-testid to the root element:
```jsx
<TextField data-testid="agent-form-name-input" label="Name" />
<Button data-testid="agent-form-save-button">Save</Button>
<Select data-testid="agent-form-model-dropdown" />
```

---

## Git flow — commit + push `automation/testids`, then stop (do this once, at the end of the case's testid work)

`EliteaAI/EliteaUI` is worked on **directly — there is no fork.** `automation/testids` is a permanent
**integration branch** holding every testid the team ever wrote: those on `main` *and* those still only
here. The dev server runs it, which is why agents never wait on the UI team's review.

**Current policy (2026-07-16): a testid lands in ONE place — `automation/testids`, committed and
pushed. That is the agent's terminal step.** Promotion to `EliteaAI/EliteaUI` `main` is a **human**
cherry-pick from `automation/testids`, done out of band. **Agents do NOT open `main` PRs.**

> ⏸ **Suspended, not deleted.** The prior flow cut a `testids/<case>-<slug>` branch from fresh `main`,
> cherry-picked the case's commits onto it, and opened a **draft PR to `main`** for the UI team. It is on
> hold by operator request — restore steps in `.agents/_reverted/RESTORE-testid-draft-pr-flow.md`.

### Step 1 — edit and commit on `automation/testids` (dev server is live on it)

Make your JSX edits **on `automation/testids`**, where the dev server already is. Vite HMR shows them
instantly — that is the fast feedback loop. Verify in the DOM snapshot, then commit:

```bash
cd ../EliteaUI                      # you are already on automation/testids
git add src/                        # ONLY files under src/ — nothing else in the UI repo
git commit -m "test: [EL-1737] add data-testid for skills import button"
```

> **Never `git checkout … origin/main` in the main tree while the dev server is running.** It reverts the
> working tree to `main`, silently stripping every pending testid out from under the live UI. Stay on
> `automation/testids`.

### Step 2 — push the integration branch (terminal step)

```bash
cd ../EliteaUI
git merge origin/main                    # keep it current (additive JSX attrs rarely conflict)
git push origin automation/testids       # plain FF push. NEVER --force.
```

That's it — **no `main` PR.** `automation/testids` is a shared org branch: **never rebase it, never
force-push it.** Sync it with `git merge origin/main` (see the `sync-base-branches` skill). A **human**
cherry-picks these commits to `EliteaAI/EliteaUI` `main` when they choose.

**Invariant:** `origin/automation/testids` must contain every testid that any test on
`origin/automation/base` references. Never merge a test PR whose testids aren't pushed.

---

## Scope discipline (canon ruling #511, 2026-07-22)

Add ONLY the testids the caller's test actually invokes on its executed code
path. **A testid wired into a page-object method that this test never calls is
NOT "referenced"** — no carve-out for reusable scaffolding, parameterized
methods used by sibling cases with other args, or "plausible future use." When
you touch a JSX array literal (a `<Select>` options list, a menu-items array,
a toggle-button-group config), it is tempting to sprinkle testids across every
sibling while you're in there — **don't**. Add only the one testid the caller
named; leave the rest to the case that exercises them. Blanket-adding sibling
testids inflates the presence-based coverage metric and is `CHANGES_REQUESTED`
at review. (Structural locator-disambiguation pairs — where a sibling testid
must exist to make the used testid's locator unambiguous — are a distinct
question tracked in #277; don't invoke that as a general carve-out.)

## Checklist

Before completing:
- [ ] All requested elements have testids added (or documented why not)
- [ ] **Scope: only elements the caller's test actually invokes** — no
      "while I'm here" sibling adds in the same JSX array literal (canon #511)
- [ ] Naming convention followed: `{section}-{element}-{type}`
- [ ] No duplicate testids introduced
- [ ] Edits committed on `automation/testids` and **pushed** (plain FF, never `--force`) — terminal step
- [ ] **No `main` PR opened** (suspended 2026-07-16; a human cherry-picks to `main`)
- [ ] Output includes ready-to-use LocatorDescriptor definitions
- [ ] Snapshot confirms testids are visible in DOM
