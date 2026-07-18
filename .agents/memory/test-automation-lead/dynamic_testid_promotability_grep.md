---
name: Promotability checks must resolve dynamically-constructed testids, not literal-grep them
description: EliteaUI's DotMenu.jsx builds several testids via template concatenation (`${key}-menuitem`, `${id}-menu-button`); a literal-string git grep for the full concatenated testid silently reports "not found" even when the locator resolves correctly at runtime — grep the key/id fragment and confirm the template mechanism instead
type: feedback
---

## What happened (#150, ELITEA-1892, PR #615 closure record)

Running the mandatory fresh promotability check (`git grep` for each testid
the test depends on, main vs. `automation/testids`), four testids came back
`main:no testids:no` even though the test had been passing green across
40+ local runs and a round-2 reviewer had already independently confirmed
two of them resolved correctly:

- `publish-version-menuitem`, `unpublish-version-menuitem` (new, this case)
- `agent-actions-menu-button`, `delete-agent-menuitem` (pre-existing,
  reused from other already-merged/promoted cases)

All four are built via `src/components/DotMenu.jsx`'s template
concatenation:
```js
data-testid={testId ? `${testId}-menuitem` : undefined}   // menu items
data-testid={id ? `${id}-menu-button` : undefined}          // trigger button
```
The source only ever contains the fragment (`key: 'publish-version'`,
`id="agent-actions"`) and the template literal (`` `${testId}-menuitem` ``)
separately — the fully concatenated string never appears verbatim
anywhere, so a literal-string grep for it always misses, regardless of
whether the locator is real and correctly wired.

## The fix

When a promotability grep comes back "not found" for a testid that the
test is demonstrably exercising successfully:

1. **Don't conclude it's missing/broken.** Check whether it's built via a
   known dynamic-construction mechanism in this codebase (DotMenu's
   `${key}-menuitem` / `${id}-menu-button`, or any other template-literal
   pattern discovered in a future case).
2. **Grep for the fragment instead** — the `key:`/`id=` value that feeds
   the template (e.g. `key: 'publish-version'`, `id="agent-actions"`) —
   and confirm the template mechanism itself is present in the same file.
3. Record BOTH pieces of evidence in the closure record (the fragment
   match + the template mechanism), not just a bare "main:YES" — a future
   auditor re-deriving this needs the same reasoning available, not a
   conclusion they have to re-discover from scratch.

## Relationship to prior memory

This is the same root failure class as
`testid_grep_quoting_gotcha.md` (`data-testid="$t"` under-reporting on
mixed quote styles) and the round-2 reviewer's independent note in this
same case ("the two dynamically-computed testids... resolve correctly even
though a literal grep doesn't find them") — a THIRD documented shape of
"testid promotability grep silently under-reports a real, working
locator." Any closure-record promotability check should now default to
trying the fragment-based check whenever a straightforward literal grep
comes back empty, before concluding a testid is genuinely missing.
