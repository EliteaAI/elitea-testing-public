---
name: A MUI Select with a search field swallows Escape — never fire-and-forget a close
description: SimpleSearchBar stops Escape propagation, so the menu never closes; confirm every close via aria-expanded
type: feedback
aliases: [escape does not close version dropdown, close_versions_menu, stopPropagation escape, SimpleSearchBar, version dropdown stuck open, withSearch select]
tags: [area/ui, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## Symptom

A step *long after* the dropdown work fails with `Locator.click: Timeout 10000ms
exceeded`, blocked by `MuiBackdrop-root … from <div id="menu-" …> subtree intercepts
pointer events`. The backdrop belongs to a menu an *earlier* step thought it had closed.

## Cause — the Escape never reached the Modal

Any `SingleSelect` rendered with `withSearch` (the agent/pipeline VERSION dropdown since
EliteaAI/EliteaUI@cf648e9a, PR #857) mounts
`src/[fsd]/shared/ui/select/SingleSelectDropdown.jsx`'s search row as:

```jsx
<SimpleSearchBar … onKeyDown={e => e.stopPropagation()} />
```

`SimpleSearchBar` **autofocuses itself** (`autoFocus = true` plus a 100 ms `setTimeout`
re-focus) and maps Escape to *clear the search box* before calling that external handler.
So while focus sits in the search field, Escape is consumed **and stopped** — MUI's
`Modal` never sees it and the menu stays open forever.

Verified live 2026-09-08 (localhost, agent VERSION dropdown):

| Focus | page-level Escape | Result |
|---|---|---|
| menu Paper | 1× | closes |
| **search field** | 1× | stays open |
| **search field** | 2× | **still open** — retrying a page-level Escape is not a fix |
| an option (focus + press) | 1× | closes, URL unchanged, nothing selected |

## Two rules this buys

1. **Press Escape on an element inside the list, not on the page.** `Locator.press()`
   focuses the element first, so the keydown originates on the `MenuItem` and bubbles to
   the `Modal`. `page.keyboard.press("Escape")` goes wherever focus happens to be.
2. **A close helper must CONFIRM — with TWO terms, not one.** `aria-expanded` on the
   `{testId}-combobox` node (`SingleSelect.jsx`'s `SelectDisplayProps`, present on `main`)
   is always rendered and flips `"true"`/`"false"` — a real two-state oracle, and a testid
   + state-attribute filter, so it is policy-compliant. But MUI binds it to React `open`
   state, which flips at the **start** of the `Grow` exit transition, while
   `MuiBackdrop-root` survives it (~200-300 ms) and keeps eating clicks. So
   `aria-expanded="false"` alone is a **leading indicator** — it narrows the failure window
   from unbounded to one transition, it does not close it. AND it with
   `expect(options).to_have_count(0)`: the option nodes unmount with the Menu subtree
   (verified: options / backdrops / `.MuiMenu-root` all read 0 after a close — not
   `keepMounted`), so their absence is what proves the backdrop is gone. Two gotchas:
   `expect(...).to_have_count()` raises `AssertionError`, **not** `PlaywrightTimeoutError`,
   so a retry loop must catch both; and a search box filtered to zero makes the count term
   trivially true — harmless, because the conjunction still needs the `aria-expanded` flip.
   A fire-and-forget close moves the failure to an unrelated later step, which is exactly
   how #2052 reached the nightly instead of the author.
3. **An early-return guard must test the SAME conjunction as the post-condition — or, better,
   don't have one.** The trap (caught in review, #2058 round 2): a loop that returns early on
   `aria-expanded == "false"` alone turns attempt N's `to_have_count(0)` timeout into attempt
   N+1's **silent success**, so the raise is reachable only on the weaker term and the strong
   term becomes decorative. Widening the guard to `collapsed and options == 0` fixes the
   verdict but falls through to `options.first.press("Escape")` in the closing window —
   pressing into a *detaching* subtree, outside the try. The shape that works: **press only
   while the state says still-open, otherwise wait; never return except through both waits.**
   Then the conjunction gates every exit, not just the guarded path.

Worked example: `AgentDetailPage.close_version_selector()` (issue #2052, PR #2058).
Note `close_versions_menu()` is a DIFFERENT menu (the skill card's Versions menu, no
search field) — do not fold them.

Still carrying the bare-Escape shape: `PipelineDetailPage.close_versions_menu()`
(`pages/pipeline_detail_page.py`) — the mechanism behind the pipelines half of #2039.

Related: [[mui_select_backdrop_blocks_second_combobox_click]] ·
[[participants_popper_escape_does_not_close_it]]
