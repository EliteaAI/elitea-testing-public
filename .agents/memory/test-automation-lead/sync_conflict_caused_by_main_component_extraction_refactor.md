---
name: sync conflict caused by main component-extraction refactor
description: automation/testids merge conflicts from main's inline-component-to-sibling-file refactor — resolve by re-adding testids to the new file, not a real conflict
type: feedback
---

Since the EL-0000 "fsd-audit" refactor commits landed on EliteaUI `main`, a
growing share of `sync-base-branches` Part 2 conflicts on `automation/testids`
are NOT genuine competing edits — they're main having moved an inline
sub-component OUT of the file our testid commit touched and INTO its own
sibling file (e.g. `ComponentX.jsx`'s inline `SubWidget` → a new
`SubWidget.jsx`). Git conflicts because both sides touch the same region, but
the real answer is always the same shape:

1. `git show ":3:<file>"` (main's side) — if it's short/empty and just an
   import of a new sibling file, that's the tell.
2. Find the new file main created, confirm it's a near-verbatim extraction of
   the "ours" inline component (same JSX, same styles) MINUS our
   `data-testid`/`testId=` props.
3. Strip the conflict block down to main's version (usually just the import
   line), then re-add our testid props/attrs onto the extracted file — same
   props, same names, same shape as they had inline. Don't try to resolve the
   old inline body in-place; it no longer belongs in the conflicted file at
   all.
4. Often the SAME file has a second region (the parent component that used to
   define the sub-component and still uses it) that auto-merges CLEANLY
   because main didn't touch it — meaning a `nameCellTestId`-style prop
   threaded from the parent survives the merge on its own; only the
   extracted child needs its testid manually restored.

The testid-loss guard (before/after `comm` diff over the whole `src/` tree)
still catches anything missed — always run it before pushing regardless of
how many "just an extraction" conflicts you resolved.

Worked example (2026-08-07, `EliteaAI/EliteaUI@40c57a3e`): 7 conflicts, all
this shape — `GridTableRowNameCell`→`DefaultNameCellContent`,
`UserMentionList`→`UserMentionItem`, `InputMappingItem`→
`{BooleanField,TextInputField}`, `SimpleLLMInputItem`→`NodeFieldInput`,
`RunStateDialog`→5 sub-components, `TokensTable`→
`{ExpiryInDays,TokenActionsCell}`, `ToolkitsTabBar`→`ToolkitsTabBarContainer`.
Zero true testid loss (576→576) once all 7 were resolved this way.
