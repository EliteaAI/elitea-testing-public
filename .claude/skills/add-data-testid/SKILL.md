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

```python
# LocatorDescriptor definitions — testid only, no fallback needed
save_button = LocatorDescriptor(testid="agent-form-save-button")
name_input = LocatorDescriptor(testid="agent-form-name-input")
```

## EliteaUI Changes Summary

Files modified: [count]
Branch: feat/EL-XXXX/add-data-test-ids-automation
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

## Git flow — dual-target (do this once, at the end of the case's testid work)

`EliteaAI/EliteaUI` is worked on **directly — there is no fork.** `automation/testids` is a permanent
**integration branch** holding every testid the team ever wrote: merged *and* still in review. The dev
server runs it, which is why agents never wait on the UI team's review.

Each testid must land in **two** places:

| Target | How | Why |
|---|---|---|
| `automation/testids` | merged in immediately, **no review** | unblocks the dev server and every other agent, right now |
| `EliteaAI/EliteaUI` `main` | **draft PR** from `testids/<case>-<slug>`, cut from fresh `main` | the UI team reviews a clean, single-case diff |

**Cut the review branch from `main`, never from `automation/testids`.** A PR's diff is computed against
its merge-base — a branch cut from the integration branch would drag every *other* case's unmerged testid
into your PR. Cutting from `main` is the entire reason the UI team sees one clean case.

### Step 1 — edit and commit on `automation/testids` (dev server is live on it)

Make your JSX edits **on `automation/testids`**, where the dev server already is. Vite HMR shows them
instantly — that is the fast feedback loop. Verify in the DOM snapshot, then commit:

```bash
cd ../EliteaUI                      # you are already on automation/testids
git add src/                        # ONLY files under src/ — nothing else in the UI repo
git commit -m "test: [EL-1737] add data-testid for skills import button"
```

> **Never `git checkout -b … origin/main` while the dev server is running.** It reverts the working tree
> to `main`, silently stripping every pending testid out from under the live UI. Build the review branch
> in a **worktree** (below) so the served tree is never disturbed.

### Step 2 — build the review branch in a worktree, open the draft PR

```bash
cd ../EliteaUI
git fetch origin
CASE=EL-1737-skills-import

# Replay THIS case's testid commits onto a branch cut from fresh main — in a
# separate worktree, so the dev server's tree is never touched.
git worktree add -b "testids/$CASE" ../.testid-pr origin/main
git -C ../.testid-pr cherry-pick <sha>...<sha>     # this case's testid commits only

# Verify the review diff is exactly the testids and nothing else:
git -C ../.testid-pr diff origin/main --stat
git -C ../.testid-pr diff origin/main | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vc 'data-testid'
#   ^ must be 0. Any non-testid line means you dragged in unrelated work — STOP.
#   (Character classes, not '^\+\+\+' — this workspace's grep is ugrep and rejects that.)

git -C ../.testid-pr push -u origin "testids/$CASE"
gh pr create --repo EliteaAI/EliteaUI --base main --head "testids/$CASE" --draft \
  --title "test($CASE): add data-testids for …" \
  --body "Attribute-only additions for the automated regression suite. UI behaviour unchanged."

git worktree remove ../.testid-pr    # clean up; dev server never noticed
```

**Open it as a DRAFT.** A human flips it to *ready* when the UI team should look. Agents do open these
PRs — the old blanket ban on PRing `EliteaAI/EliteaUI` is repealed — but they never mark them ready and
never merge them.

### Step 3 — push the integration branch

```bash
git push origin automation/testids       # plain FF push. NEVER --force.
```

`automation/testids` is a shared org branch: **never rebase it, never force-push it.** Sync it with
`git merge origin/main` (see the `sync-base-branches` skill).

**Invariant:** `origin/automation/testids` must contain every testid that any test on
`origin/automation/base` references. Never merge a test PR whose testids aren't pushed.

---

## Checklist

Before completing:
- [ ] All requested elements have testids added (or documented why not)
- [ ] Naming convention followed: `{section}-{element}-{type}`
- [ ] No duplicate testids introduced
- [ ] Edits committed on `automation/testids` and pushed (plain FF, never `--force`)
- [ ] Review branch `testids/<case>` cut from **fresh `origin/main`** (not from `automation/testids`)
- [ ] Review diff vs `main` contains **only** `data-testid` lines — verified, not assumed
- [ ] **Draft** PR opened against `EliteaAI/EliteaUI` `main`; left as draft, not marked ready
- [ ] Output includes ready-to-use LocatorDescriptor definitions
- [ ] Snapshot confirms testids are visible in DOM
