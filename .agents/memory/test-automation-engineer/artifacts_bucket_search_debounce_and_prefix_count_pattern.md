---
name: Artifacts bucket-search debounce-on-clear + testid-prefix count pattern
description: BucketsPanel.jsx's search-clear button unmounts the input synchronously but the filtered list itself still lags a 300ms debounce even when clearing to empty; plus a reusable `[data-testid^="..."]` prefix-count technique for "total count" observables that have no dedicated testid.
type: feedback
---

## The bug (ELITEA-1809, R1 local failure)

`BucketsPanel.jsx`'s bucket list is `filteredBuckets`, computed from
`debouncedSearchQuery = useDebounceValue(searchQuery, 300)` — **not** from
`searchQuery` directly. `handleSearchClear` does two things:

```js
const handleSearchClear = useCallback(() => {
  setSearchQuery('');
  setIsSearchActive(false);
}, []);
```

`setIsSearchActive(false)` unmounts the search input **synchronously** (the
`{isSearchActive && !collapsed && (...)}` guard). But `setSearchQuery('')`
still has to flow through the SAME 300ms debounce hook before
`filteredBuckets` recomputes to the full unfiltered list. A page-object
`close_bucket_search()` that waits only for the input to become hidden
returns control to the caller ~300ms too early — the caller reads a stale,
still-filtered bucket count.

**Symptom observed live:** asserting `get_visible_bucket_count() ==
baseline_bucket_count` immediately after the clear-button click and
input-hidden wait caught `32 == 178` (the "buck"-filtered count) instead of
the expected full 178.

**Fix:** `close_bucket_search()` waits for the input to become hidden AND
THEN applies the same `BUCKET_SEARCH_DEBOUNCE_WAIT_MS` (500ms, matches the
`search_buckets()` fill-and-debounce wait) before returning.

**Generalizes to:** any MUI/React debounced-filter UI where a "clear" action
resets multiple pieces of state at different speeds (one synchronous —
visibility/mount — one debounced — the derived filtered data). Don't assume
a debounced input's "clear" path skips the debounce just because it's going
to an empty string; read the `useMemo`/`useEffect` dependency array, not
just the visible DOM change, before picking a wait condition. Same family as
`save_networkidle_race_quirk.md`'s "the visible signal and the load-bearing
signal are not always the same event."

## The reusable technique: `[data-testid^="…"]` prefix-count for untested "total" observables

The AFS's original ask was a raw DOM-text read of `BucketFooter.jsx`'s
"Buckets: N" label — which has no testid, and this project's locator policy
forbids both (a) adding a testid to an element no case step reads directly
(the "scope is load-bearing" ruling) and (b) chaining a raw CSS selector off
an existing testid'd field (`page-objects.md`'s anti-pattern).

Instead: define a PREFIX variant of an existing per-item dynamic testid
template and count matches. Already-established elsewhere in this codebase
(confirmed via grep before use, not invented fresh):
`agent_detail_page.py`'s `SKILL_CARD_ANY_SELECTOR`/`VARIABLE_ROW_ANY_SELECTOR`/
`MODEL_SELECTOR_OPTION_ANY_SELECTOR`, `chat_page.py`'s
`MENTION_SKILL_ITEM_PREFIX`, `mcp_form_page.py`'s `TOOL_CHIP_PREFIX`,
`pipeline_detail_page.py`'s `SELECT_OPTION_PREFIX`. Added
`ArtifactsPage.BUCKET_ROW_ANY_SELECTOR = '[data-testid^="artifacts-bucket-row-"]'`
+ `get_visible_bucket_count()` to the same family — used for narrows-on-filter,
restores-on-clear, and unchanged-across-an-attempt proofs, all without a
hardcoded/environment-fragile literal count (the AFS's own proposed "175"
was already stale by the time of implementation, since other tests'
leaked `autotest-*` buckets keep incrementing it).

**Note for reviewers:** this pattern uses `[data-testid^="…"]` (prefix
match), not a literal `[data-testid="…"]`. The mechanical locator-policy
grep's stated compliance rule only names a literal `=` — flag `^=` hits
explicitly in the PR body so the reviewer does the one-hop check
(constant's own definition is still testid-based) rather than reflexively
blocking on the letter of the rule.
