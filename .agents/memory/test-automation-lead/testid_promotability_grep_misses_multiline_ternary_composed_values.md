---
name: Testid promotability grep misses multi-line ternary-composed values
description: A single-line testid-presence grep (data-testid or testid[:=] filter) silently misses matches where the literal string and its testid keyword span different lines — always confirm with a full file-diff when a component uses a ternary/ helper for the testid value
type: feedback
---

## What happened (2026-08-19/20, wave-15 and wave-16)

Twice in one campaign, the standard testid-promotability grep
(`git grep -- "$t" origin/main -- src/ | grep -qiE "(data-testid|testid[:=])"`)
returned a false "no" for a testid that WAS genuinely present on
`automation/testids`, because the component wrote it as a multi-line
prop/ternary rather than a single-line `data-testid="..."`:

- Wave-15: `SummaryDetailsButton`'s `testId` prop, wired across 2 lines.
- Wave-16: `ToolkitEditor.jsx`'s `discardConfirmButtonTestId={` on one
  line, `isMcpTestIdScope ? 'mcp-canvas-discard-confirm-button' :
  'toolkit-canvas-discard-confirm-button'` on the next — the grep's
  same-line filter never sees "testid" and the literal string together.

Both times, caught only by falling back to
`git diff origin/main origin/automation/testids -- <the specific file>`
and reading the hunk directly — the file-diff shows the addition
regardless of line-wrapping, since it's not filtering by pattern co-occurrence
on one line.

## Rule going forward

**Don't trust a "no" from the single-line testid grep at face value when the
component is a shared/prop-driven one** (a `*TestId` prop, a ternary
choosing between two literal testid strings, anything spanning a JSX prop
value across multiple lines). Confirm with the direct file-diff
(`git diff origin/main origin/automation/testids -- <file>`) whenever:
- the grep says "no" but the commit message / PR description claims the
  testid was added, or
- the component is known to be shared across entity types (canvas
  editors, generic list/detail wrappers) where a ternary pattern
  (`isXTestIdScope ? 'x-...' : 'y-...'`) is common.

A "yes" from the grep is trustworthy (it found a real single-line match) —
it's only the "no" that needs the file-diff fallback to rule out a
multi-line false negative.
