# Users tab — User Activity table + search

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Session context for the 2026-08-28 entries: project "Elitea Testing Team", preset `Last 30d` unless stated; zero console errors across the whole Overview -> Tools -> Users -> Health -> Guide walk._

## Users tab (`AnalyticsUsers.jsx`) — confirmed live 2026-08-05, ELITEA-2312

- **Confirmed (fresh `git fetch origin`): `AnalyticsUsers.jsx` is byte-identical
  on `main` and `automation/testids`** (blob `c7b6ff4b68aec5e6f8b72e433cbe8c62126e5d04`
  on both) — like the rest of the Analytics feature, already fully on `main`.
- **Zero pre-existing testids** on `AnalyticsUsers.jsx` or the shared
  `src/components/SearchInput.jsx` it renders — every element this tab's cases
  touch needs `add-data-testid` work (10 new testids specced in ELITEA-2312's
  AFS: title, count, search input via a new `testId` prop on the shared
  component, table-header row, repeated row/errors-cell testids, and 4
  `TablePagination` `slotProps` wirings).
- **Table has 9 columns**, not the 8 several sibling case texts describe:
  `User, Active Days, LLM Calls, Tool Calls, Agent/Pipeline Runs, Chat Msg,
  Errors, Total Tokens, Total Cost` — no "Events" column exists. Same
  stale-case-text family as the tab/KPI counts above. Filed
  elitea-testing-public#1188.
- **Errors column color rule** (`AnalyticsUsers.jsx:144-151`):
  `color: u.errors > 0 ? palette.status.rejected : undefined` — red only when
  `errors > 0`; `errors === 0` renders default text color (confirmed live:
  `rgb(255, 255, 255)`). Case texts describing "red when ≥ 0" are stale — same
  issue #1188.
- **Search input live-filters** on every keystroke (`onChange` → `search`
  state → query param), no debounce/Enter/blur needed — confirmed live
  (typing "testbot" narrowed 3→1 row, updated count + pagination label).
- **Pagination**: MUI `TablePagination`, `rowsPerPageOptions=[10,20,50]`,
  default `rowsPerPage=20`. With ≤20 total users it's a single page — both
  prev/next arrows disabled, range label `"1–{total} of {total}"`.
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_users/prompt_lib/
  {project_id}?date_from=...&date_to=...&limit=...&offset=...&sort_by=total_events&sort_order=desc`
  — distinct from the Overview/Health endpoint (`.../analytics/prompt_lib/...`,
  no `_users`); fires on tab mount and on every search-input change. 200 OK,
  no console errors, in both cases observed.
- **No positive-case (`errors > 0`) live data available** in the "UI Testing"
  exploration project — all 3 users observed have `errors: 0`. The red-color
  branch is source-confirmed but not live-exercised; ELITEA-2312's AFS
  documents this as a Blocked Step, not a defect. **Resolved during ELITEA-2312
  implementation**: the `auth_state` fixture's actual default project is
  **"Private" (project id `399`)**, distinct from the analyst's exploration
  project "UI Testing" — "Private" has real `errors > 0` rows (`User 6250`:
  errors=78, `testbot@elitea.ai`: errors=75, live in the default "Last 24h"
  range) so the positive branch is live-exercisable with no seeding. Confirmed
  again during ELITEA-2313 exploration (2026-08-05) — switch the project
  selector to "Private" (`select-option-399` — no dedicated testid on the
  option itself, MUI Select generates it) for any future case in this feature
  needing `errors > 0` fixture data.

### Users tab search (ELITEA-2323)
- Live-verified filtering: 18 rows -> `samvel` 1 row -> `aliaksandr` 2 rows -> cleared 18 rows in
  the original order. Server-side on the email field, per keystroke, no debounce/Enter/blur, and
  there is **no clear (X) button** — "clear the search" means emptying the input.
- `User 6250` (no email) never matches any term and reappears on clear.
- ELITEA-2312's merged spec already covers the narrowing smoke check; what it does NOT prove is
  exclusivity (`>= 1` passes even if nothing was filtered) and restoration (its clear is in
  `finally`, unasserted) — that is exactly ELITEA-2323's `lextend_` scope.


**Resolved/added during ELITEA-2323 implementation (2026-08-28):** the User Activity table now
renders **17** columns, not 9 — the UI team added INPUT/OUTPUT TOKENS, INPUT/OUTPUT TOKEN COST,
CACHE READ/WRITE TOKENS and CACHE READ/WRITE COST. The merged ELITEA-2312 spec was RED on
`automation/base` because of it; its expected tuple is repaired in the ELITEA-2323 PR and the
occurrence recorded on #1188. Also: `AnalyticsPage.search_users()` now RETURNS the captured
`analytics_users/prompt_lib/` body (additive) — re-searching the same term later cannot capture it,
because RTK-Query serves the repeat from cache with no new request.

**Resolved/added during ELITEA-2318 implementation (2026-08-28):** the Users tab renders **NO
chart** (`AnalyticsUsers.jsx` is table + pagination only) — so a case step saying "repeat the chart
steps on the Users tab" has no counterpart here. Worth stating explicitly in an AFS rather than
leaving the absence implicit.
