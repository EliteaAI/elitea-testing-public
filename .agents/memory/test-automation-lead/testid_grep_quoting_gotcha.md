---
name: Testid grep quoting gotcha in closure-record promotability checks
description: git grep -q "data-testid=\"$t\"" silently under-reports — EliteaUI mixes 'data-testid':'...' object-literal props and buttonTestId="..." wrapper props with the JSX-attribute literal form; grep the bare testid string instead
type: feedback
---

## What happened

While building the closure record's promotability table for #73
(ELITEA-1990), the `workflow.md` § Closure record verification snippet
(`git grep -q "data-testid=\"$t\"" origin/main -- src/`) reported **every
single testid as absent from both `main` and `automation/testids`** —
including several that were plainly present and merged (e.g.
`skill-controls-menu-button`, used by pre-existing, long-merged cleanup
code). That's a false negative on a scale that would make the whole
verification block worthless if trusted blindly.

## Root cause

`EliteaAI/EliteaUI` does not exclusively use the JSX literal-attribute form
`data-testid="foo"`. It also uses:
- MUI `inputProps`/`slotProps` object literals with single-quoted keys/values:
  `'data-testid': 'skill-name-input-field'`
- Wrapper-component props that aren't literally named `data-testid`:
  `buttonTestId="generate-skill-open-button"` (a custom prop the wrapper
  component threads down to the real `data-testid` internally)

The `"data-testid=\"$t\""` pattern only matches the first form.

## Fix

Grep the **bare testid string** instead of assuming a specific attribute
syntax:

```bash
git grep -q -- "$t" origin/main -- src/
```

This matches regardless of which prop pattern was used to wire it. Re-ran
the #73 promotability check this way and got the correct, sane result
(2 of 13 testids already on `main`, 11 still in open draft PRs — matching
what `gh pr list` independently showed).

## Action for future closure records

Update the verification snippet in `workflow.md` § Closure record to the
bare-string form before the next case that needs a promotability table —
this was caught by cross-checking against `gh pr list`, but a future run
might not catch it and would then post a false "0% promotable" (or worse,
a false "promotable" if the literal pattern happens to match unrelated
text) into a permanent closure record.
