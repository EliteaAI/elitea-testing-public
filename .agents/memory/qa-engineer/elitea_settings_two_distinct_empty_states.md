---
name: Two distinct empty states on Elitea list pages — don't fake one with the other
description: A no-search-match table is GridTableContainer's "No X" message; the real empty state is EmptyStatePage and needs zero rows to exist
type: feedback
aliases: [empty state, No tokens yet, EmptyStatePage, GridTableContainer isEmpty, no search results, empty table]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The two states look alike and are not the same component

1. **Zero entities exist** → the page returns the shared `EmptyStatePage`
   (`empty-state-title`, e.g. "No tokens yet" + illustration + a `Create` button)
   **before** `DrawerPage`. The page header, the search box, the table, the column
   headers and every row **cease to exist**. Assert their *absence*, never their
   invisibility.
2. **A search filters everything out** → the page header and search box **stay**;
   `GridTableContainer.isEmpty` renders its `emptyMessage` (e.g. "No tokens",
   `GridTableContainer.jsx:37-45`) and the column headers unmount. `empty-state-title`
   is **absent** here — confirmed live on personal tokens, 2026-08-27.

⇒ **Searching for a nonsense string cannot be used to reach state 1.** It is a different
component with a different message, so a test doing that would read the wrong observable
off the wrong branch. This is the tempting shortcut on every blocked empty-state case
(ELITEA-2250/2278, issue #1780) — it does not work.

`GridTableContainer` carries no testid on that message and accepts no testid prop; the
compliant add is a caller-supplied `emptyMessageTestId` prop wired at the table's call
site.

Related: [[grid_table_sort_first_click_is_descending]]
