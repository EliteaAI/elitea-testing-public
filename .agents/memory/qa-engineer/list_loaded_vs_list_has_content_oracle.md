---
name: List-page "loaded" oracle vs content assertion (review lens)
description: How to verify a cards-OR-empty-state disjunction really excludes loading/error — read the sibling render, not just the gate expression
type: feedback
---

**When a repair replaces "at least one card renders" with a
`entity-card-name OR empty-state-title` disjunction, the gate expression is
NOT the proof.** Reviewing PR #1852 (ELITEA-1901), the claim was that
`CardList.jsx:40-42`'s `showEmptyOrError = !isLoading && (isError || isEmptyList)`
/ `showCustomEmptyState = showEmptyOrError && customEmptyState && !isError`
makes the disjunction unsatisfiable on a loading or errored list.

The `isError` term alone does NOT settle it — you must read **what the error
branch actually renders**. Here it holds up: `showDefaultEmptyState` (the
`isError` path) renders `EmptyListBox`, which carries **no testid at all**
("Oops! Something went wrong."), so an errored list matches neither selector
and the wait times out. Had `EmptyListBox` reused `EmptyStatePage`, the
"cannot pass on an errored list" claim would have been false and the repair
would have been a real weakening.

**Two blind spots such a disjunction usually still has** (both true on the
Agents list, EliteaUI `origin/main` 2026-08-27):

- **Folder view, empty folder** — `PrivateAgentsList.jsx:224-227` passes
  `customEmptyState` as a ternary whose folder branch is a bare
  `<Typography>No items in this folder yet</Typography>`, **no testid**.
- **Table view** — `entity-card-name` exists ONLY in `Card.jsx:270`;
  `DataTable` has no equivalent, so a fully-loaded non-empty table matches
  neither selector.

Both are settled, non-error states that would raise a raw TimeoutError.
Neither is reachable from a fresh `/agents/all` navigation, so they are nits
rather than blockers — but a docstring calling the disjunction "a genuine
load-completion oracle" without naming the card-view / non-folder-view scope
is broader than its evidence.

**Reviewer move that makes this cheap:** grep the testid across the whole UI
repo (`git grep -n '<testid>' origin/main -- src/`) and read EVERY sibling
branch of the component that gates it. A disjunction is only as strong as the
render it excludes.
