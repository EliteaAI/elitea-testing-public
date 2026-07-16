---
name: Skills search bar quirks (implementer)
description: SearchBar.jsx is shared across Agents/Skills/Pipelines/Credentials pages via RightPanel.jsx / CredentialsList.jsx; MIN_SEARCH_KEYWORD_LENGTH=3 blocks both activation modes below 3 chars; clear_search() must not press Enter after the native-setter clear; grid/list responses need a settle wait (auto-retrying expect(), not a bare wait_for_network) after resolving; console-message resource URLs live in msg.location not msg.text; shared-dev-project leftover test data can collide with substring search terms (from ELITEA-1739, ELITEA-1965)
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

## Grid search matches on DESCRIPTION text too, not just NAME

Discovered during the ELITEA-1739 analyst rerun (Known Defects Clarification
#5): the grid-fetching endpoint (`GET .../elitea_core/skills/prompt_lib/
{project_id}?...&query=<text>`) matches the query substring against BOTH the
skill's name and its free-text description. A short/common substring like
`ter` collided with unrelated skills purely via description text (e.g.
`automated-test-explainer`'s description contains "interaction", and stray
`elitea-1793-ghost-skill` fixtures matched via "after-remove"). **When
picking a partial-search test term, verify it's clean against every OTHER
skill's description in the target environment, not just its name** — a
short/common trigram is a high-collision choice in any shared or long-lived
test environment; prefer a distinctive, low-collision full word instead
(e.g. `content` over `ter`).

## Settle wait after every grid-fetching response

Same lag documented for `filter_by_tag()`/`clear_tag_filter()`: the
response resolving doesn't guarantee the grid has re-rendered
(`entity-card-name` cards) yet — RTK Query → Redux → React re-render is one
more tick. Add `wait_for_network(timeout=5000)` + `wait_for_timeout(300)`
after every `expect_response` context exits for search/clear methods, or
assertions immediately after can read the pre-filter card set.

## Also used by Credentials — same component, `CredentialsList.jsx` this time (ELITEA-1965)

`SearchBar.jsx` powers the Credentials list search box too (default
`agent-search-input` testid, same as Agents/Skills — Pipelines remains the
only page-scoped override). Same explicit-activation behavior (Enter/send-
icon only, never live-filter-as-you-type) and the same settle-wait race
apply. Two NEW findings from this case, generalizable to any future
SearchBar consumer:

**A bare `wait_for_network()` is not enough — use an auto-retrying
`expect()` before reading card state.** `page.expect_response(...)`
resolves as soon as the response *headers/body* arrive, which is BEFORE the
Redux dispatch → React re-render commits. `wait_for_network()`
(`networkidle`) doesn't reliably close that gap either (no further network
activity is generated by the render itself). The only robust fix: put an
auto-retrying Playwright assertion — `expect(locator).to_have_count(n)` or
`.to_be_visible()` — immediately before the first manual `.text_content()`
/ list-comprehension read of card state. A raw manual read right after
`search()`/`clear_search()` returns will intermittently see `set()`/stale
data (observed directly: screenshot taken moments later showed the correct
final state, proving it was a pure timing race, not a functional bug).

**Credentials adds a redirect-on-empty-list guard NOT present on
Skills/Agents/Pipelines** — `CredentialsList.jsx`'s `useEffect` navigates
away to `/credentials/create-credential` when `!hasQuery && total === 0`
(intended for a genuinely empty *project*). `onClear()` flips `hasQuery` to
`false` a render-tick before the unfiltered re-fetch resolves `total`, so
clearing a **zero-results** search briefly satisfies that guard and
incorrectly redirects. Filed as `elitea-testing-public#551`. Scoped
precisely: clearing after a **non-empty**-result search never triggers it
(`total` is already non-zero when `hasQuery` flips). If a future SearchBar
consumer page has a similar "redirect when list is empty" effect, check its
guard condition for the same one-render race.

## Console-message resource-load errors: the URL lives in `msg.location`, not `msg.text`

Playwright's `page.on("console", ...)` for a browser-generated "Failed to
load resource: the server responded with a status of 404 (Not Found)"
message carries a GENERIC `msg.text` with no URL — the failing resource's
URL is in `msg.location['url']` instead (`{'url': ..., 'line': 0, 'column':
0, ...}`). A filter predicate written as `"some/path" in msg.text` will
NEVER match this class of message; check `msg.location.get("url", "")`
instead. Cost real debugging time on ELITEA-1965 (filed
`elitea-testing-public#554`, an intermittent 404 from an RTK-Query
project-id race in `EliteaUI/src/api/toolkits.js`'s `toolkitTypes` endpoint
— `GET /elitea_core/toolkits/prompt_lib/{projectId}` fires before
`useSelectedProjectId()` resolves, collapsing to a trailing-slash URL with
no id segment; unrelated to Credentials search specifically, likely
reproducible on any page rendering the "TYPES" filter panel) before
realizing the text/location split.

## Shared-dev-project leftover test data can silently poison exact-count search assertions

If an earlier local run's cleanup (`finally` block, best-effort
`credential_api.delete_credential`) doesn't fully complete — e.g. the
process gets killed mid-run during debugging — its seeded credentials
persist in the shared DEV project. A later run's `search("alpha")`-style
substring assertion (`to_have_count(1)`) then intermittently sees 2+ matches
because a stale `autotest_cred_alpha_<old-ts>` from a prior aborted run
still exists (digits-only timestamp suffixes never collide with each other,
but the substring predicate itself doesn't care about timestamps). Before
trusting an exact-count search assertion is genuinely broken versus
poisoned by leftover data, verify directly:
`credential_api.list_all_credentials()` filtered for the test's name
prefix — should be empty between runs. Killed background test runs are a
known orphaning risk (see `killed_background_run_orphans_test_data.md`);
this is the same failure class surfacing through a different symptom
(false test failure instead of visible clutter).
