---
name: Skills search bar quirks (implementer)
description: SearchBar.jsx is shared across Agents/Skills/Pipelines pages via RightPanel.jsx; MIN_SEARCH_KEYWORD_LENGTH=3 blocks both activation modes below 3 chars; clear_search() must not press Enter after the native-setter clear; grid responses need a settle wait after resolving (from ELITEA-1739)
type: feedback
---

## SearchBar.jsx is one shared component, not per-page

`EliteaUI/src/components/SearchBar.jsx`, rendered once from `RightPanel.jsx`,
powers the search box on Agents, Skills, AND Pipelines list pages. The
`testId` prop only varies for Pipelines (`pipeline-search-input`) — Agents
and Skills both get `agent-search-input` (a known naming quirk, not a bug).
Any testid added to the send-icon or other SearchBar internals is likewise
shared across all these pages — don't assume a "Skills-only" testid is
actually scoped to Skills.

## MIN_SEARCH_KEYWORD_LENGTH = 3 blocks BOTH activation modes below 3 chars

`EliteaUI/src/common/constants.js` — `MIN_SEARCH_KEYWORD_LENGTH = 3`.
`SearchBar.jsx`'s `onSearch()` (shared by Enter's `onKeyDown` AND the
send-icon's `onClick`) checks `trimmedSearchString.length >=
MIN_SEARCH_KEYWORD_LENGTH` before dispatching a query — below that, it
shows a "must be at least 3 letters" toast and does **not** fetch the grid.
Confirmed live via network capture: a 9-char term ("formatter") and a
3-char term ("cod") both correctly fire
`GET .../elitea_core/skills/prompt_lib/{project}?...&query=<text>`; a
2-char term ("Co") never does. This directly invalidated an ELITEA-1739 AFS
claim that "Co" narrows the grid to 2 results — a genuine case-text drift,
not discoverable without live network verification (the popover-only
`search_options` endpoint has NO length gate, so it's easy to mistake its
firing for the grid's).

**If a future case's partial-search term is < 3 characters, flag it before
implementing** — it cannot activate the grid filter, full stop, regardless
of activation mode.

## clear_search(): do NOT press Enter after the native-setter clear

The documented "unreliable `.fill('')`" workaround (native
`HTMLInputElement` value-setter + bubbling `input` event) is correct, but
stop there — do not press Enter afterward. `handleInputChange` (SearchBar's
`onChange`) calls `onClear()` directly whenever the value becomes empty
with no active tag filters; `onClear()` dispatches `resetQuery()` and
that alone re-fetches the grid. A trailing Enter re-runs `onSearch()` with
an empty (sub-minimum-length) string, which only produces the "3 letters"
toast — and if the Redux `query` state was already `""` (e.g. clearing
right after a blocked sub-3-char attempt that never actually dispatched),
waiting for a network response after that Enter will **hang** until
timeout, since no request fires at all in that scenario. Wrap the clear's
`expect_response` in a try/except and tolerate the no-fetch case — it's a
legitimate state, not a bug.

## Settle wait after every grid-fetching response

Same lag documented for `filter_by_tag()`/`clear_tag_filter()`: the
response resolving doesn't guarantee the grid has re-rendered
(`entity-card-name` cards) yet — RTK Query → Redux → React re-render is one
more tick. Add `wait_for_network(timeout=5000)` + `wait_for_timeout(300)`
after every `expect_response` context exits for search/clear methods, or
assertions immediately after can read the pre-filter card set.
