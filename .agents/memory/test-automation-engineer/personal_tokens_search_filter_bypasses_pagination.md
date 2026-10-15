---
name: Personal Tokens search filters client-side, no Enter — and get_row_by_name is pagination-blind
description: PersonalTokensPage.search() needs no Enter (TokensSection.jsx filters on every keystroke); get_row_by_name() only matches the current page's rendered rows, so live-data growth past DEFAULT_PAGE_SIZE=10 silently breaks name lookups until search() runs first.
type: feedback
---

## Surface

`Settings → Personal Tokens` (`/settings/tokens`), `TokensTable.jsx` built on
the shared `grid-table` components, `TOKENS_TABLE_CONFIG.DEFAULT_PAGE_SIZE =
10`.

## The bug this caused (issue #2441, ELITEA-2284, 2026-10-15)

`PersonalTokensPage.get_row_by_name(name)` does
`self.token_row.filter(has_text=name)` — `token_row` is
`[data-testid="token-row"]`, and Playwright's `.filter()` only resolves
against DOM elements that actually exist, i.e. the CURRENTLY RENDERED page.
This is correct, boring Playwright behaviour — but it is pagination-blind:
nothing about the method name or signature hints that it can't see rows on
page 2+.

The AFS baseline (2026-08-05) had 5 tokens, all on one page. By 2026-10-15
the live project had grown to 14 (accumulated `automation_dev_admin` ×8 +
others), pushing the AFS's target row (`"Marian"`) onto page 2. The test
failed with `Locator expected to have count 1`, actual `0` — looking like a
missing-data or product bug, but the UI was correct the whole time (verified
by filtering the table down to "Marian" via the search box and confirming
`data-expiration-state="expired"` + text `"Expired"` rendered exactly as
expected).

**Lesson: any `get_row_by_name`/`get_row_by_*`-style filter on a GridTable
page is implicitly scoped to ONE page of results.** On a page whose backing
list grows over time (admin/test-utility entities especially — tokens,
credentials, anything created by repeat CI/dev-admin runs), a name-based row
lookup that worked at AFS-authoring time can silently break months later
purely from accumulated unrelated data, with zero product change. Before
trusting a `get_row_by_name` 0-count failure as a real defect or missing
precondition, check the live row count via the list API
(`GET /api/v2/auth/token/` here) against the page size.

## The fix — `PersonalTokensPage.search(term)`

Added a `search()` method: `self.search_input.click()` +
`press_sequentially(term, delay=20)` — **no `.press("Enter")`**. Confirmed
live and in source (`PersonalTokens.jsx`: `searchInput: { onChangeSearch:
setSearch }` → `TokensSection.jsx`'s `filteredTokens` `useMemo` filters the
already-fetched list on every `search` state change, client-side, no new
network request). This is UNLIKE the Credentials list's `SearchBar.jsx`
(ELITEA-1965 — explicit Enter/icon activation required) — don't copy that
pattern onto this page's search box, and don't assume any two "search input"
page objects in this app activate the same way. Check the actual wiring
(`onChangeSearch`/`onChange` straight to state = live-filter; `onSearch`/
`onKeyDown` Enter handler = explicit-activation) before writing the method.

Call `search(name)` before `get_row_by_name(name)` whenever the row might not
be on page 1 — which, for any page object with pagination and no "search
first" discipline, is "always, defensively," once the surface has any
real/growing data behind it.
