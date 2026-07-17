---
name: Promotability grep can false-negative on non-attribute-string testids
description: A closure-record promotability check that greps for `data-testid="<value>"` (literal JSX attribute syntax) will wrongly report a testid as absent when it's actually set via an object-literal prop, a conditional JSX expression, or a spread — grep the bare value first, then read the line to classify syntax
type: feedback
---

## What happened

Issue #26 (ELITEA-1735 testid-only rework), closure-record promotability check.
I ran:

```bash
git grep -q "data-testid=\"$t\"" origin/main -- src/
```

for every testid the case's diff uses, and got `no` for both `chat-message-input`
and `skill-test-last-response` on **both** `origin/main` and
`origin/automation/testids` — which would have meant the test literally could
never pass anywhere, contradicting the fact that the test had just run GREEN
3/3 against a live app serving one of those two branches.

Re-grepping with the bare value (`git grep -n "chat-message-input" origin/main --
src/`, no attribute-syntax assumption) found both immediately:

```jsx
// UserInput.jsx — object-literal prop, not a JSX attribute string
slotProps={{ htmlInput: { 'data-testid': 'chat-message-input' } }}

// ApplicationAnswer.jsx — conditional JSX expression
data-testid={isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'}
```

Neither matches `data-testid="literal-value"` — the first sets the attribute
through a nested prop object (MUI `slotProps`), the second through a ternary
expression. Both are real, both render the correct DOM attribute, both were
already confirmed live via `element.evaluate()` in the analyst's earlier pass
— the grep pattern was simply too narrow to see them.

## Why it matters

A promotability row is the load-bearing fact in a closure record — it's what
tells `promote-automation-batch` (and a human skimming the issue six months
later) whether a merged test can survive on a deployed env. A false NEGATIVE
here is less dangerous than a false POSITIVE (worst case you under-claim
readiness, not over-claim it) — but it still corrupts the record: a case
correctly reported as "blocked, 7 of 11 testids draft-only" could just as
easily have been mis-reported as "blocked, 9 of 11" if I hadn't sanity-checked
the two suspicious "no/no" rows against the fact that the test was passing.

## Rule going forward

When verifying testid presence for a closure record:

1. **First grep the bare value/substring**, not the attribute-string pattern:
   `git grep -n "<testid-value>" origin/<ref> -- src/` — this catches every
   syntax shape (literal attribute, object-literal prop, conditional
   expression, template string, spread).
2. **Then read the matched line(s)** to confirm it's actually a `data-testid`
   assignment (not, e.g., a comment or an unrelated string that happens to
   contain the same substring) and to classify the syntax for your own
   understanding — but don't require it to match a specific attribute-string
   shape before counting it as present.
3. If a row's grep comes back genuinely empty on both refs, cross-check it
   against known behavior (did the test actually use this element? did it
   pass?) before trusting the negative — a real absence and a syntax-pattern
   miss both look identical as bare "no" output until you look at *why*.

## Deeper variant: runtime-templated testids (id/key props, not literal strings at all)

Issue #62 control-audit (ELITEA-1894, PR #514). Even a bare-value grep for
`agent-actions-menu-button`, `agent-actions-export-menuitem`, and
`delete-agent-menuitem` came back **empty on both refs** — because the
literal string never exists in EliteaUI source anywhere. These testids are
assembled at runtime, several files away from where the case's own diff
lives, by a *shared* menu component:

```jsx
// DotMenu.jsx — generic dropdown shared by many entities
data-testid={id ? `${id}-menu-button` : undefined}
data-testid={testId ? `${testId}-menuitem` : undefined}   // testId = item.key
```

fed by call sites that only set the short `id`/`key`:

```jsx
// ApplicationControls.jsx
<Controls.ControlsDropdown id="agent-actions" menuItems={menuItems} />
// ExportApplicationButton.jsx
{ key: 'agent-actions-export', label: 'Export', ... }
```

Rule: when a bare-value grep for a `*-menu-button` / `*-menuitem` (or any
testid that reads like `{something}-{suffix}`) comes back empty on a ref
where the test demonstrably passes, don't stop at "false — corrupted
claim." Search for the shared component that likely template-constructs it
(grep the suffix alone, e.g. `-menu-button"` or `-menuitem`, across the
whole `src/` tree) and trace which `id`/`key` prop feeds it. Confirm
presence/absence by diffing that upstream `id`/`key` source between refs
instead — that's what actually determines whether the templated testid
renders. This is a different mechanism from the object-literal/conditional
case above (there the attribute assignment itself was on a different line
shape; here the *value* itself isn't a literal at all) — treat "empty bare
grep" as "go find the template," not as automatic proof of absence,
whenever the element in question is a shared dropdown/menu/list item.

### Third occurrence: template-literal column testid, only the suffix is checkable

Issue #66 (ELITEA-1944, PR #523, EliteaUI#564). Same failure shape again, this
time on a `GridTableHeader.jsx` column-header testid:

```jsx
data-testid={
  columnTestIdPrefix ? `${columnTestIdPrefix}-column-header-${column.field}` : undefined
}
```

A bare-value grep for `mcp-table-column-header-name` (the fully composed
string I expected to render for the `name` column) came back empty on
**both** `main` and `automation/testids` — even though the implementer's own
live DOM check and the merged, passing test both confirmed the attribute was
actually rendering. The composed string never exists in source at all: it's
built from a prop (`columnTestIdPrefix`, itself set to the literal
`'mcp-table'` in a *third* file, `DataTable.jsx`) concatenated with a runtime
`column.field` value. No single grep target can prove presence here — the
value is assembled from two separate variables in two separate files, only
one of which (`columnTestIdPrefix`'s literal `'mcp-table'` assignment) is a
static string at all.

### Fourth occurrence: rule applied correctly on first re-check (#128, ELITEA-1911)

Ran the literal `data-testid="$t"`-shaped grep out of habit on the FIRST pass
of this closure record's verification and got false "no" on several testids
that plainly work live (`generate-agent-open-button` via a `buttonTestId="..."`
prop-forwarding wrapper; `generate-agent-resource-section-skill` via a
template-literal `data-testid={\`generate-agent-resource-section-${entityType}\`}`).
Caught it against this entry's own rule before writing the closure record,
re-ran with a bare `git grep -q -- "$t"` substring match, got the correct
all-YES result on both refs. No bad record shipped. Filing this occurrence
mainly to confirm the rule holds and is actionable in real time, not just in
hindsight — the fix is now reliably the FIRST thing reached for, not a
recovery step after a wrong claim almost went out.

What actually worked: grep for the **prop name** (`columnTestIdPrefix`)
across `src/`, confirmed present on `automation/testids` / absent on `main`.
For the sibling testid on the same PR that *was* a plain literal
(`mcp-table-row-name` in `DataTableNameCell.jsx`, no interpolation), the
ordinary bare-value grep worked fine — so check each testid on its own
diff-syntax merits, don't apply one grep strategy uniformly across an
entire case's testid list. General rule: before grepping, glance at the
`add-data-testid`/implementer diff for each testid's assignment line — if
it's a template literal or multi-file composition, grep the prop/constant
name that's actually static, not the fully-composed value you expect to
see in the DOM.
