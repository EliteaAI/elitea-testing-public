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

Adds `data-testid` attributes to EliteaUI (and connected first-party repos — e.g. the Support
Assistant) components for robust test automation locators.

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

## Connected repos (Support Assistant, and future ones)

Some elements render from a **connected first-party repo** we own but consume as a package —
today the **Support Assistant** (`@eliteaai/elitea-assistant`, source in the `../elitea_assistant`
sibling; files are `.tsx`). They are **not** in `../EliteaUI/src` (grep returns nothing), but they
are still testid-able — you edit the connected repo's OWN source, one repo outward. This is NOT the
#579 third-party stop+flag exception (`.agents/testing.md`) — we own the source.

Everything below works identically, with two substitutions:
- **Search / edit** `../elitea_assistant/src/**/*.tsx` instead of `../EliteaUI/src/**/*.jsx`
  (`data-testid` syntax is identical in TSX). Local dev serves this source live via the
  `EliteaUI/vite.config.js` alias (parent `SETUP.md` § 6), so HMR still shows your edit instantly.
- **Commit + push** on the connected repo's OWN `automation/testids` branch (`cd ../elitea_assistant`)
  — same terminal step. Extra promotion hop: a human cherry-picks it to the assistant's `main`, then
  EliteaUI bumps the git-dep — see `.agents/workflow.md` § Connected repos.

Same naming, same scope discipline (#511 / #277), same testid-only policy. #579 still applies to the
connected repo's OWN third-party internals (its mermaid / react-markdown output).

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
- Only edit files in `EliteaUI/src/` — or, for a connected repo's element, its own `src/`
  (e.g. `../elitea_assistant/src`); **never** `node_modules` or a built `dist/`
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
2. **Check the connected repos** before flagging — a Support-Assistant element lives in
   `../elitea_assistant/src` (`.tsx`), not `../EliteaUI/src` (see § Connected repos)
3. **STOP+FLAG for that element — never emit a fallback/role/text locator**
   (testid-only policy: `.agents/testing.md` § Locator policy). The lead
   decides: deeper source hunt, UI-team question, or stop+flag exception
   (genuine third-party widget internals)
4. Continue with the other elements

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
at review.

### Same-element conditional pairs (canon ruling #277, 2026-07-22)

Sometimes a shared component renders two semantically different things through
the same JSX node — e.g. `CardTagSectionItem` renders both real tag chips AND
the "+N more" overflow badge, and both go through the same root `<Box>`. An
unconditional `data-testid` on that node would attach to every render and make
the used testid's locator match both — a real collision.

The fix is a prop-driven conditional on the SAME element. There are two
compliant shapes, and only two:

1. **Preferred — name only the used branch, leave the other `undefined`:**
   ```jsx
   data-testid={isOverflow ? undefined : 'entity-card-tag-chip'}
   ```
   The used branch's locator is still collision-safe (the overflow render has
   no `data-testid` attribute to match), and there is no orphan testid to
   pollute the presence-based coverage metric. Reach for this by default.

2. **Both branches named — only if the caller's test asserts the untested
   branch's absence** on the elements it exercises:
   ```jsx
   data-testid={isOverflow ? 'entity-card-tag-overflow' : 'entity-card-tag-chip'}
   ```
   ```python
   # in the test / page-object method the test invokes:
   expect(card.locator(SkillsListPage.CARD_TAG_OVERFLOW)).to_have_count(0)
   ```
   The absence assertion turns "the pair disambiguates cleanly" from a
   documented assumption into a test-enforced invariant. Both testids are now
   referenced by locators on the executed code path, so both pull their
   weight in the coverage metric.

**Not compliant:** naming both branches and explaining the untested one only
in prose (docstring, AFS PROVENANCE row, PR description). Docs don't execute
— an orphan testid still inflates coverage. Same reasoning as #511: no soft
justifications, no documentation-only carve-outs.

The reviewer's mechanical grep (`.locator(`/`get_by_*` on the diff) already
catches absence assertions the same as positive ones — no new grep needed.

## Checklist

Before completing:
- [ ] All requested elements have testids added (or documented why not)
- [ ] **Scope: only elements the caller's test actually invokes** — no
      "while I'm here" sibling adds in the same JSX array literal (canon #511)
- [ ] **Same-element conditional pair (`data-testid={cond ? A : B}`):** either
      the untested branch is `undefined`, OR the caller's test asserts the
      untested branch's absence on the elements it exercises (canon #277)
- [ ] Naming convention followed: `{section}-{element}-{type}`
- [ ] No duplicate testids introduced
- [ ] Edits committed on `automation/testids` and **pushed** (plain FF, never `--force`) — terminal step
- [ ] **No `main` PR opened** (suspended 2026-07-16; a human cherry-picks to `main`)
- [ ] Output includes ready-to-use LocatorDescriptor definitions
- [ ] Snapshot confirms testids are visible in DOM
