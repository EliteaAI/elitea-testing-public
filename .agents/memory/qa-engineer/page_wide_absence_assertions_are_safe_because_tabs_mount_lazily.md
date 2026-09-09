---
name: Page-wide absence assertions on a shared testid are safe in EliteaUI — inactive tabs mount nothing
description: How to verify a generic shared testid (empty-state-title) can't be double-mounted on a list page
type: reference
aliases: [empty-state-title, shared testid absence, CustomTabPanel, showEmptyOrError]
tags: [area/ui, type/review-check]
created: 2026-09-10
updated: 2026-09-10
---

## The check

When a spec asserts `count() == 0` on a GENERIC shared testid (`empty-state-title`,
rendered by `src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx:49` and consumed
by 6+ list pages), the reviewer's job is to prove no OTHER instance can mount on the
same route. Three greps settle it, no execution needed:

1. `git grep -ln EmptyStatePage origin/automation/testids -- src/` — which pages consume it.
2. The route's page container (`src/pages/<Area>/<Area>.jsx`) — how many list components it renders.
3. `src/components/StickyTabs.jsx:20` — `CustomTabPanel` is `value === index ? (...) : null`,
   so **inactive tabs mount nothing at all**. Not `hidden`, not `display:none` — unmounted,
   and `Locator.count()` therefore cannot see them.

On a private project the Pipelines page has exactly ONE tab ("All" → one
`PrivatePipelinesList` → one `CardList`), so a page-wide absence assertion is unambiguous.
On the PUBLIC project (`PUBLIC_PROJECT_ID`) that page has four tabs — still one mounted.

## Why the assertion matters at all

`CardList.jsx:40-44`: `showEmptyOrError` short-circuits **both** `showTable` and
`showCards`. So on an empty list, "zero cards" is true in table view *and* card view —
an absence-only layout assertion is vacuous. Pair it with `empty-state-title` absence.

⚠️ Residual hole: the `isError` branch renders `EmptyListBox`, which carries NO
`empty-state-title`. Only a POSITIVE precondition assertion earlier in the test
(a known entity name in the list) closes that one.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
