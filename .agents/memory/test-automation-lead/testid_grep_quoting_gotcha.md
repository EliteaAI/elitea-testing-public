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

## Recurrence (2026-07-16, control audit of #95/ELITEA-1989)

The doc fix above never landed — `workflow.md` § Closure record (still,
as of this writing, ~line 203-204) uses the literal `data-testid=\"$t\"`
form. #95's closure record pasted that exact snippet + a claimed "9/9 YES"
on `automation/testids` for the `generate-skill-modal` FSD slice's
testids, wired via the same `buttonTestId="..."` → `data-testid={...}`
indirection this entry already names. Re-running the pasted command
verbatim (fresh fetch) gave 9/9 `no` — the delivery's own memory log
repeated the same false claim, so this wasn't just a comment typo but a
real methodology gap. The bottom-line conclusion (not promotable) was
still correct once indirection is accounted for, but the pasted
"evidence" itself was not reproducible — control audit FAILed item 3 on
that basis. Filed `.agents/workflow.md`'s fix as a tracked canon-gap issue
(#553) since a memory lesson alone isn't stopping recurrence — the doc
itself needs to change.

## Recurrence (2026-07-18, #166/ELITEA-1947 delivery)

Same shape a third time, this time on `inputProps={{ 'data-testid': 'X' }}`
(`NameDescriptionInput.jsx` / `ToolBaseProperty.jsx`'s `toolkit-form-name-input`
and `toolkit-field-url-input`) — the literal `data-testid=\"$t\"` snippet
reported both as absent from BOTH `main` and `automation/testids`, which
contradicted the AFS/PR's explicit "already exists, reused as-is" claim.
That contradiction (a "no" where the implementer/AFS asserted "yes,
pre-existing") is the actionable tell: re-check the grep methodology before
writing the row, don't write "gap" just because the pattern says so. Re-ran
with a bare fixed-string `git grep -F "<testid>"` and got the correct YES
on `automation/testids` for both. `.agents/workflow.md` § Closure record
STILL carries the literal-attribute snippet as of this recurrence — #553
(or its equivalent) evidently still hasn't landed; worth a direct doc-fix
dispatch next time a framework-scale window opens rather than relying on
this memory entry alone to catch it live every time.

## Recurrence (2026-07-18, #175/ELITEA-1871 delivery) — 4th occurrence

Same shape a fourth time: `CreateAgentForm.jsx` (`inputProps={{ maxLength:
..., 'data-testid': 'agent-name-input' }}`) and `InstructionsInput.jsx`
(`inputProps={{ 'data-testid': 'agent-instructions-input' }}`). The literal
snippet from `workflow.md` reported 3 of 4 already-merged, already-live
handles absent from both `main` and `automation/testids`. Caught by a
sanity `grep -rn` on the working tree before trusting the closure-record
table. **New mistake this time, worth flagging on myself**: before checking
this memory file, I filed a brand-new issue (#624) proposing the exact same
fix #553 already proposes — a duplicate, closed after the fact. The
lesson isn't just the grep pattern; it's **check memory for a matching
curated entry before filing a "discovery" issue**, not just before doing
the verification itself. Added the recurrence as a comment on #553 instead
of a new issue. #553 has now sat open since the #95 audit (2026-07-16)
through 2 more real deliveries where it would have prevented a live
mistake — this is no longer a "worth a doc-fix dispatch sometime" note,
it's costing real turns every single case that has UI-side testids.

## Recurrence (2026-07-20, #262/ELITEA-1841 delivery) — 5th occurrence, caught proactively this time

Fifth shape: a new caller-supplied prop threaded to the real attribute —
`selectAllCheckboxTestId` (prop) then `data-testid={selectAllCheckboxTestId}`
(JSX expression, not a literal) then `selectAllCheckboxTestId="artifacts-select-all-checkbox"`
(the literal string only appears at the CALL SITE's prop assignment, several
lines away from the `data-testid={...}` JSX expression itself — a variant of
the `buttonTestId="..."` wrapper-prop shape, but one level more indirect
since the literal and the `data-testid=` JSX attribute never appear on the
same line, or even necessarily the same file). The literal
`data-testid="$t"` form reported BOTH of this case's new testids absent
from `automation/testids` — factually wrong, they were both there.

**Caught before it reached the closure record this time**: sanity-checked
the bare-string grep technique against ELITEA-1840's own already-known
testid (`artifacts-file-checkbox`, confirmed template-based/prop-threaded
the same way) on both branches BEFORE trusting the result for this case's
new testids — the sanity check itself surfaced that even 1840's testids
aren't on `main` yet either (expected — human cherry-pick pending, not a
gap). This is the pattern worth generalizing: don't just switch to the bare
form when a contradiction tips you off (the reactive catch in the 3rd/4th
recurrences above) — proactively sanity-check the grep technique against a
KNOWN-true positive/negative pair from an already-merged sibling before
running it fresh on a new case's testids, every time, not just when
something already looks wrong.

#553 (canon fix for `workflow.md`'s snippet) is STILL open as of this
recurrence, ~10 weeks after the #95 audit first flagged it, across 5 real
deliveries now. Worth escalating past "leave a comment" — consider
dispatching the doc fix directly next framework-scale window instead of
waiting for another opportunistic pass.
