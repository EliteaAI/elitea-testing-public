---
name: Shared list-page search empty-state and clear-redirect bug class
description: CardList.jsx's customEmptyState always wins over the query-aware placeholder; clearing a zero-match search redirects to the entity's create page (cross-page defect class, #551 Credentials + #585 MCP)
type: feedback
---

Affects every list page built on the shared `CardList.jsx` (Credentials,
MCP, Toolkits, Applications, Skills, Pipelines, PersonalTokens — anything
using `RightPanel`'s `SearchBar` + `CardList`'s `customEmptyState` /
`emptyListPlaceHolder` props).

## Trap 1 — the query-aware empty placeholder is dead code

`CardList.jsx`:
```js
const showCustomEmptyState = showEmptyOrError && customEmptyState && !isError;
const showDefaultEmptyState = showEmptyOrError && !showCustomEmptyState;
```
`showCustomEmptyState` fires on **any** `cardList.length === 0`, regardless
of whether it's a genuine zero-items-in-project state or a zero-match
search. Whenever a caller passes BOTH `customEmptyState` (e.g.
`ToolkitsList.jsx`'s `<EmptyStatePage title="No MCPs yet" .../>`) AND
`emptyListPlaceHolder` (e.g. `ToolkitsEmptyListPlaceHolder`'s
query-branching "Nothing found. Create yours now!"), `customEmptyState`
always wins — the query-aware placeholder never renders. **Don't add a
testid to the query-aware placeholder without first confirming it's
actually reachable** (I did this wrong once on ELITEA-1941 before catching
it — reverted, added the testid to `EmptyStatePage.jsx`'s title
`Typography` instead, since that's what genuinely renders). Check
`CardList.jsx`'s call site for whether BOTH props are passed before trusting
either one is live.

## Trap 2 — clearing a zero-match search redirects to the create page

Confirmed on **two** pages so far, same root-cause shape, different files:
- Credentials (`CredentialsList.jsx`) — elitea-testing-public#551 (ELITEA-1965)
- MCP (`ToolkitsList.jsx` `isMCP` branch) — elitea-testing-public#585 (ELITEA-1941)

Root cause (read from `CredentialsList.jsx`, generalizes): each page has an
"empty project → redirect to create" `useEffect` guard shaped like
`if (!loading && !hasQuery && !hasTypeFilter && total === 0) navigate(createRoute)`.
`onClear()` synchronously resets the query (`hasQuery` flips false
immediately) on the SAME render where `total` is still the stale zero-match
count from the just-cleared search, before the unfiltered list has
re-fetched. The guard's "project is genuinely empty" intent fires
incorrectly for "was just viewing a zero-match filtered view."

**Reproduction recipe (any CardList-based list page):** seed ≥1 item →
search a term that matches nothing → confirm empty state shows → click the
search Clear (X) icon (`data-testid="search-clear-button"`) → observe the
URL, not just the DOM (a real Playwright `locator().click()`, not
JS-evaluate — verify with a real click to rule out synthetic-input
artifacts). **Control check that isolates the trigger:** clearing a search
that still has ≥1 match does NOT redirect (this is what proves it's
specifically the zero-match→clear sequence, not "clearing" in general).

**Before filing a fresh one on a new page**, check for the sibling guard in
that page's own list component first — likely present on Toolkits/Skills/
Applications/Pipelines too (untested as of 2026-07-16), and cross-link any
new issue to #551/#585 for shared triage rather than treating as novel.
