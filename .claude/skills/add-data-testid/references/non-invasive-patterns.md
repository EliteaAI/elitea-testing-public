# Non-invasive patterns — before/after for all eight PR #753 violations

These are the real cases that drove the hard-gate rules in `SKILL.md`. Each entry names
the file, what was wrong, and the compliant form that is now in the tree.

---

## 1. `Toast.jsx` — MUI `Alert` close button (ladder rung 3: `slotProps`)

**Violation:** replaced `Alert`'s built-in close `<IconButton>` with a custom one via the
`action` prop. `Alert.js:247` renders the built-in close button only when
`action == null && onClose` — passing `action` **replaces** it, silently changing the
icon, its size (20→18px), and losing `currentColor` severity tint + native
`title="Close"`.

**Compliant form (live at `Toast.jsx:71`):**
```jsx
// BEFORE (violation)
action={
  <IconButton
    size="small"
    aria-label="close"
    onClick={onClose}
    data-testid="toast-dismiss-button"
  >
    <CloseIcon fontSize="small" />
  </IconButton>
}

// AFTER (compliant)
slotProps={{ closeButton: { 'data-testid': 'toast-dismiss-button' } }}
```
`undefined` renders no attribute — every caller that doesn't pass `onClose` keeps
byte-identical DOM.

---

## 2. `ToolkitEditor.jsx` — product state frozen into `useState` (banned)

**Violation:** `isMCP` (a per-render derived value with 9 consumers) was moved into
`useState` to get a mount-stable value for a testid. That changed the logic for all
9 consumers: the value was computed once at mount, not per render.

**Compliant form (live at `pages/NewChat/ToolkitEditor.jsx`):**
```jsx
// BEFORE (violation)
const [isMCP, setIsMCP] = useState(toolkit?.isMCP || toolkit?.meta?.mcp || false);

// AFTER (compliant) — product isMCP stays per-render; a SEPARATE mount-scoped var
//                     holds the testid scope, never touching the product value
const isMCP = toolkit?.isMCP || toolkit?.meta?.mcp || false;   // per-render, unchanged
const [isMcpTestIdScope] = useState(
  () => toolkit?.isMCP || toolkit?.meta?.mcp || false,
);                                                              // testid-only, mount-stable
```

---

## 3. `AnalyticsUserDetailed.jsx` — recharts render prop form (banned)

**Violation:** recharts `<RechartsTooltip content={…} />` was changed from element form
to an inline arrow function. recharts' `renderContent` does `cloneElement` for elements
but `createElement` for functions — an inline arrow is a **new component type every
render**, causing the tooltip to remount on every data update.

**Compliant form (live at `AnalyticsUserDetailed.jsx:200`):**
```jsx
// BEFORE (violation)
content={props => <ChartTooltip {...props} testId="analytics-user-detail-chart-tooltip" />}

// AFTER (compliant) — element form; recharts cloneElement injects props, testId passed directly
content={<ChartTooltip testId="analytics-user-detail-chart-tooltip" />}
```

---

## 4. `InfoTooltip.jsx` — wrapper node inside MUI Tooltip popper (ladder rung 3: `slotProps`)

**Violation:** a new `<Box>` wrapper was added inside the Tooltip popper purely to host
the `contentTestId`. This added a DOM node for every InfoTooltip instance, whether or not
the caller opted in.

**Compliant form (live at `InfoTooltip.jsx:107-118`):**
```jsx
// BEFORE (violation)
<Tooltip
  title={<Box data-testid={contentTestId}>{titleContent}</Box>}
  ...
>

// AFTER (compliant) — MuiTooltip's own `tooltip` slot (already exists), undefined = no attr
slotProps={{
  popper: { sx: { zIndex: tooltipConfig.zIndex } },
  // Caller-scoped testid on MuiTooltip's own `tooltip` slot (the bubble element that
  // already exists), NOT on a new wrapper node — so the popper DOM is byte-identical
  // for every InfoTooltip instance, whether or not a caller opts in.
  tooltip: { 'data-testid': contentTestId },
}}
```

---

## 5. `RunStateDialog.jsx` — `display: contents` wrappers (banned)

**Violation:** two `<Box sx={{ display: 'contents' }}>` wrappers were added purely to
host grouping testids `pipeline-run-details-timeline-section` and
`pipeline-run-details-states-section`. These added DOM nodes — even `display: contents`
is still a real DOM element.

**Compliant form:** nothing. No rung in the ladder applied. Both wrappers were reverted
and the two grouping testids were dropped. A dropped grouping testid is cheaper than a
DOM change. The existing child elements keep their own testids.

---

## 6. `ZipDownloadProgressDialog.jsx` — wrapper for dialog title (ladder rung 1: existing prop)

**Violation:** a new `<Typography>` wrapper with `data-testid` was added around the dialog
title text, adding a DOM node.

**Compliant form (live at `ZipDownloadProgressDialog.jsx:64`):**
```jsx
// BEFORE (violation)
title={<Typography data-testid="artifacts-zip-download-progress-title">
  {`Preparing ${bucket || 'artifacts'}.zip`}
</Typography>}

// AFTER (compliant) — BaseModal already has a titleTestId prop
<BaseModal
  open={open}
  data-testid="artifacts-zip-download-progress-dialog"
  title={`Preparing ${bucket || 'artifacts'}.zip`}
  titleTestId="artifacts-zip-download-progress-title"
  ...
/>
```
The prop channel existed before the PR; grepping `grep -n "titleTestId"` in `BaseModal`
would have found it in 30 seconds.

---

## 7. `EditSecretInputGridTable.jsx` + `CreatePersonalToken.jsx` — wrapper for error text (ladder rung 1: existing prop)

**Violation:** a new `<span>` wrapper with `data-testid` was added around the
`helperText` string to make it locatable. The wrapper was inside a prop value —
still a new DOM node.

**Compliant form (live at `EditSecretInputGridTable.jsx:93`, `CreatePersonalToken.jsx:162`):**
```jsx
// BEFORE (violation)
helperText={<span data-testid="secret-name-error">{helperText}</span>}

// AFTER (compliant) — InputBase.StyledInputEnhancer already has helperTextTestId prop
<Input.StyledInputEnhancer
  helperText={helperText}
  helperTextTestId={field === 'name' ? 'secret-name-error' : undefined}
  inputProps={{ maxLength: MAX_VARIABLES_LENGTH, 'data-testid': … }}
  ...
/>
```
`undefined` renders no helper-text testid on the value field — byte-identical DOM for
the non-name branch.

---

## 8. `BucketItem.jsx` — id change (KEPT, declared improvisation)

**Finding:** `id="bucket-menu"` → `` id={`bucket-menu-${name}`} ``. This is a change to
a value that feeds product logic — `DotMenu` derives its item testids from the parent's
`id` attribute.

**Why it was KEPT (not reverted):**
- Every consumer was read before the change.
- `DotMenu.jsx` derives `testId: item.key` from menu items, and menu items get their
  `key` from the `id` prop — so the change is testid-driven AND fixes duplicate DOM ids
  that existed when multiple `BucketItem` components rendered on the same page.
- Declared as an improvisation in the commit body per
  `.agents/role-overrides.md` § Declared-improvisation protocol.

This is NOT a precedent for making arbitrary `id`/`key`/`className` changes. It passed
because: (a) every consumer was verified, (b) it was documented, and (c) it fixed a
real separate bug (duplicate DOM ids).

---

## `slotProps` slot table (full reference)

| MUI component | Slot name | DOM element targeted | Note |
|---|---|---|---|
| `Alert` | `closeButton` | The built-in close `<IconButton>` | Only rendered when `action == null && onClose` |
| `Tooltip` | `tooltip` | The bubble `<div>` | `undefined` → no attribute; popper slot = outer wrapper |
| `TextField` | `formHelperText` | The helper/error `<p>` | Wired via `InputBase.helperTextTestId` prop |
| `TextField` | `htmlInput` | The `<input>` element | `inputProps` maps to this slot (MUI v7 `TextField.js:148`) |
| `Switch` | `input` | The hidden `<input>` | |
| `Dialog` / `Modal` | — | Use `BaseModal.titleTestId` prop | No slot needed for dialog titles |

---

## Token-level normalizer recipe (for large batches)

Line diffs are unreliable under `singleAttributePerLine: true` — a single attribute
insertion on a one-line tag expands to N lines, making 300-line diffs where the real
change is three characters. A token-level comparison is the only reliable instrument
for batch review.

```python
# /tmp/_lib.py — shared helpers
import re, subprocess

MB = "origin/main"  # merge base

# testid-attribute patterns to strip before comparing
NAME = re.compile(
    r'\s*(?:data-testid|testId|[a-z]+TestId)\s*=\s*(?:"[^"]*"|{[^}]*})',
    re.IGNORECASE,
)

def strip_entries(text):
    return NAME.sub("", text)

def strip_comments(text):
    # remove single-line JSX comments {/* … */}
    return re.sub(r'\{/\*.*?\*/\}', "", text, flags=re.DOTALL)

def tok(text):
    return re.findall(r'\w+|[^\w\s]', text)
```

```python
# /tmp/an4.py — token-level file comparison
import sys, subprocess
sys.path.insert(0, "/tmp")
from _lib import MB, strip_entries, strip_comments, tok

def simplify(text):
    return tok(strip_comments(strip_entries(text)))

def git_show(ref, path):
    r = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True, text=True,
        cwd="/path/to/EliteaUI",
    )
    return r.stdout if r.returncode == 0 else None

# Compare every changed file
changed = subprocess.run(
    ["git", "diff", "--name-only", f"{MB}...HEAD", "--", "src/"],
    capture_output=True, text=True,
    cwd="/path/to/EliteaUI",
).stdout.splitlines()

clean, residual = 0, 0
for f in changed:
    base = git_show(MB, f)
    head = git_show("HEAD", f)
    if base is None or head is None:
        residual += 1; continue
    if simplify(base) == simplify(head):
        clean += 1
    else:
        residual += 1
        print(f"RESIDUAL: {f}")

print(f"\n{clean} clean / {residual} residual of {len(changed)} files")
```

Expected for a pure testid batch: all files clean, or only files with declared
mandatory exceptions in the residual set.
