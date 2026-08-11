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

## Hard gate: the diff is testids and nothing else (EliteaUI PR #753 review, 2026-08-11)

**The gate.** Every line you add or remove in EliteaUI must be either **(a)** a testid
attribute/prop, or **(b)** the *minimum* plumbing that attribute requires. Anything else
— a new DOM node, a replaced MUI internal, a moved hook, a reshaped render prop, product
state frozen into `useState` — is **out of scope even when it works and even when the
testid genuinely needs it.** If a testid cannot be attached without one of those,
**stop and flag that element** (§ Edge Cases → Element Not Found) and do not attach it.

> Origin: PR #753 promoted 400 accumulated testids and carried **eight** changes that
> were neither testid additions nor legitimately testid-driven — each one changed
> rendered DOM or product logic to make a testid attachable **when a non-invasive
> channel already existed.** Worked before/after for all eight:
> `references/non-invasive-patterns.md`.

### The preference ladder — try in order, stop at the first rung that works

1. **An existing prop channel on the component you are calling.** Grep the shared
   component for `TestId` **before editing anything**:
   ```bash
   grep -rn "TestId" ../EliteaUI/src/\[fsd\]/shared/ui/ ../EliteaUI/src/components/
   ```
   Channels already in the tree: `BaseModal.titleTestId`, `InputBase.helperTextTestId`,
   `KPICard.valueTestId`, `InfoTooltip.contentTestId`, `InfoTooltip.testId`.
   **This rung alone resolved 3 of the 8 PR #753 violations** — the wrapper nodes added
   for a dialog title and two error-text elements were all already reachable by a prop
   (`ZipDownloadProgressDialog.jsx:64`, `EditSecretInputGridTable.jsx:93`,
   `CreatePersonalToken.jsx:162`).
2. **`data-testid` directly on the element / MUI component that already renders it.**
   MUI forwards unknown props to the root DOM node — no wrapper needed.
3. **MUI `slotProps` on a slot element that already exists.** This is the channel for
   **anything inside** a MUI component: you get the attribute without changing what MUI
   renders. Verified slots: `Alert.closeButton`, `Tooltip.tooltip`,
   `TextField.formHelperText`, `TextField.htmlInput`, `Switch.input` (full table:
   § Edge Cases → MUI Components). **This rung resolved 2 of the 8 violations**
   (`Toast.jsx:71`, `InfoTooltip.jsx:117`). `undefined` renders no attribute, so every
   non-opting caller keeps byte-identical DOM.
4. **A new caller-opt-in prop on the shared component, defaulting to `undefined`.**
   Canonical shape, live at
   `[fsd]/widgets/pin-toggler/lib/hooks/usePinMenu.hooks.jsx:20`:
   ```jsx
   ...(key ? { key } : {}),   // absent by default → every existing caller unchanged
   ```
   Add the new prop to the enclosing `useMemo`/`useCallback` dep array. Name it
   `testId` / `<part>TestId` (§ Conventions rule 3) — never `dataTestId`.
5. **Nothing.** No rung applies ⇒ report the element as unreachable and move on. **A
   dropped grouping testid is cheaper than a DOM change** (`RunStateDialog` precedent:
   two `display: contents` wrappers reverted, two grouping testids dropped).

### Banned — never do any of these to host a testid

Each one is a real PR #753 finding, not a hypothetical:

- ❌ **Add a wrapper element.** Includes `display: contents` wrappers, promoting
  `<>…</>` to `<Box>`, and an extra `<span>`. **Zero new DOM nodes.**
- ❌ **Replace a MUI built-in sub-element with your own** (`Alert`'s close button, a
  `Dialog` title, a `Select` icon). Read the MUI source before assuming your addition is
  additive — `Alert.js:247` renders the built-in close button only when
  `action == null && onClose`, so passing `action` **replaces** it. The PR #753 version
  silently swapped the icon, changed 20→18px, and lost both the `currentColor` severity
  tint and the native `title="Close"`. Compliant form now in the tree at `Toast.jsx:71`.
- ❌ **Freeze product state into `useState` / `useRef` for testid scoping.** If you need
  a mount-stable value for a testid, add a **separate** variable and leave the product
  one computed per render (`ToolkitEditor.isMCP` had 9 consumers).
- ❌ **Convert a render prop between element form and function form.** recharts'
  `renderContent` does `cloneElement` for elements but `createElement` for functions, so
  an inline arrow is a **new component type every render** and the child remounts. Pass
  the testid as a prop on the element instead —
  `content={<ChartTooltip testId="…" />}` (`AnalyticsUserDetailed.jsx:200`).
- ❌ **Move, add, or conditionalize a hook call.**
- ❌ **Change a `key`, `id`, or `className` whose value feeds product logic** — unless
  you read every consumer and say so in the commit body (`BucketItem` `id="bucket-menu"`
  → `` id={`bucket-menu-${name}`} `` was kept on exactly those terms: `DotMenu` derives
  its testids from `id`, and the change also fixed duplicate DOM ids).
- ❌ **Add a `data-*` state attribute without first proving no stylesheet selects on it:**
  ```bash
  grep -rn '\[data-active' ../EliteaUI/src/ \
    ../EliteaUI/node_modules/@mui/material ../EliteaUI/node_modules/@mui/x-data-grid
  ```

### Mandatory-plumbing exceptions (allowed — must be minimal, and declared)

- **Widening `undefined` → `{}`** when there is genuinely nowhere else to attach,
  **preserving every existing key**:
  `inputProps={{ maxLength: MAX_VARIABLES_LENGTH, 'data-testid': … }}`,
  `{ name: name || 'api_key', ...(testId && { 'data-testid': testId }) }`.
- **A new caller-opt-in prop + its dep-array entry** (ladder rung 4).
- **A pure, null-safe testid-slug helper.**

Each exception you use gets **one line in the commit body** stating why it was
unavoidable. An undeclared exception is a violation
(`.agents/role-overrides.md` § Declared-improvisation protocol).

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
- **Append `data-testid` after the existing attributes** — do NOT insert it as the first
  attribute. EliteaUI's Prettier config sets `printWidth: 110` + **`singleAttributePerLine: true`**,
  so touching the attribute order of a one-line tag explodes it into N lines and buries
  your actual change. Appending after existing attributes keeps the diff to one line
  (or the minimal reflow Prettier needs), which is the only way a reviewer can spot a
  violation at a glance.
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

### Step 5.5: Prove zero functional impact

Before committing, run these checks against every touched file:

```bash
cd ../EliteaUI
git diff -- <file>         # every +/- line is a testid attribute, prop, or listed exception
npx prettier --check src/  # confirms reflow noise is Prettier's, not yours
npx eslint src/<file>
```

Then three targeted greps over the whole diff — each one catches a different violation
class from PR #753:

```bash
# Any new hook call added?
git diff origin/main...HEAD -- src/ | grep -nE '^\+.*\buse(State|Effect|Memo|Callback|Ref)\('

# Any new DOM node added?
git diff origin/main...HEAD -- src/ | grep -nE '^\+.*<(Box|div|span|Fragment)'

# Any real deletion (not just Prettier reflow of a testid line)?
git diff origin/main...HEAD -- src/ | grep -nE '^-' | grep -vE 'testid|TestId'
```

**Expected output:** empty, empty, and (for the third) only lines whose new form differs
solely by Prettier reflow. **Any non-empty result must be explained in the commit body or
reverted.** For a large batch, a token-level normalizer (strip testid attributes + scaffolding,
tokenize, compare `git show base:f` vs `git show HEAD:f`) is the only reliable instrument —
line diffs are worthless under `singleAttributePerLine`.

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

**Root element (the default).** MUI forwards `data-testid` (and any unknown prop) to the
root DOM node — place it directly on the MUI component:

```jsx
<TextField data-testid="agent-form-name-input" label="Name" />
<Button data-testid="agent-form-save-button">Save</Button>
<Select data-testid="agent-form-model-dropdown" />
```

**Anything inside a MUI component goes through `slotProps` — never by replacing the
built-in.** MUI v7 exposes every internal sub-element as a named slot. Pass the testid
via `slotProps.<slot>` on the slot that already renders the element:

| Slot path | What it targets | Example |
|---|---|---|
| `Alert.slotProps.closeButton` | The built-in close `<IconButton>` | `slotProps={{ closeButton: { 'data-testid': 'toast-dismiss-button' } }}` |
| `Tooltip.slotProps.tooltip` | The tooltip bubble `<div>` | `slotProps={{ …existing, tooltip: { 'data-testid': contentTestId } }}` |
| `TextField.slotProps.formHelperText` | The helper/error text | wired via `InputBase.helperTextTestId` prop channel |
| `TextField.slotProps.htmlInput` | The `<input>` element | `inputProps={{ …existing, 'data-testid': … }}` (MUI v7 maps `inputProps` → `slotProps.htmlInput`) |
| `Switch.slotProps.input` | The hidden `<input>` | `slotProps={{ input: { 'data-testid': … } }}` |

**The `inputProps` → `htmlInput` mapping (MUI v7, `TextField.js:148`).** MUI silently
maps the deprecated `inputProps` into `slotProps.htmlInput` — a *different* slot from
`input`/`inputLabel`. This means widening `inputProps={{ maxLength, 'data-testid': … }}`
is safe: it cannot clobber existing `slotProps` entries.

`undefined` renders no attribute, so callers that don't opt in keep byte-identical DOM.

**Never replace a built-in sub-element to add a testid.** The `action` prop on `Alert` is the
canonical example: `Alert.js:247` renders the built-in close button only when
`action == null && onClose`. Passing `action` **replaces** the button — silently swapping
the icon, changing size, and losing `currentColor` severity tint + `title="Close"`. The
compliant form is `slotProps.closeButton` (live at `Toast.jsx:71`).

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
- [ ] **Every added line is a testid attribute, prop, or a declared mandatory exception**
      (§ Hard gate — the gate)
- [ ] **Zero new DOM nodes; zero replaced MUI built-ins; zero hook changes** — if any of
      the three Step 5.5 greps returns a hit, explain it in the commit body or revert
- [ ] **Highest applicable ladder rung used** — existing prop channel → direct attr →
      `slotProps` → new opt-in prop (§ Hard gate → preference ladder)
- [ ] **Step 5.5 greps run** and output pasted into the commit body or report (empty
      output is valid evidence; a missing paste is a gap)
