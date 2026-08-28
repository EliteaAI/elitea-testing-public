# Surface digest — settings-analytics

> Handle cache from live exploration, not a source of truth. Verify a handle
> as you use it. One writer at a time (analyst, whoever is active this
> session) — see `test-case-analysis` § 2b.

## Index — this digest is split by subarea

It outgrew a single comfortable read (410 lines) on 2026-08-28 and was split. Read the
file for the subarea you are touching; each one is self-contained.

| File | Covers |
|---|---|
| [`_surface/page-shell.md`](_surface/page-shell.md) | Route, source layout, the 8-tab bar, project badge, page-level testids, page object |
| [`_surface/date-filter.md`](_surface/date-filter.md) | Presets, From/To pickers, the MUI popper internals, cross-tab persistence |
| [`_surface/overview-tab.md`](_surface/overview-tab.md) | The 8 KPI cards, conditional adoption badge, `KpiCard` prop wiring |
| [`_surface/tools-tab.md`](_surface/tools-tab.md) | Most Popular Tools chart, Tool Details table, search, pagination |
| [`_surface/users-tab.md`](_surface/users-tab.md) | User Activity table, columns, errors colour, search-filter behaviour |
| [`_surface/agents-tab.md`](_surface/agents-tab.md) | Agents & Pipelines charts + activity table, personal-project column branch |
| [`_surface/health-tab.md`](_surface/health-tab.md) | Requests vs Errors chart (no legend — names live in the tooltip), event-type table |
| [`_surface/guide-tab.md`](_surface/guide-tab.md) | Static metric documentation — 9 sections, 43 metrics, no network |
| [`_surface/detail-views.md`](_surface/detail-views.md) | User-detail and agent/pipeline-detail drill-downs (same-page state swaps) |
| [`_surface/chart-tooltips.md`](_surface/chart-tooltips.md) | The shared `ChartTooltip` on every chart — testid inventory, honest hover technique, per-chart series contracts, traps |
| [`_surface/known-issues.md`](_surface/known-issues.md) | Every case-text clarification and product defect filed from this surface |

## Cross-cutting facts (true everywhere on this surface)

- **The whole Analytics feature is on `main`** — only the testids the automation team added sit on
  `automation/testids` awaiting a human cherry-pick. Re-verify with a fresh `git fetch origin` and
  the two-stage grep in `.agents/workflow.md` § Closure record before writing a provenance row.
- **Never wait on `networkidle`** — this app holds a persistent Socket.IO polling transport open,
  so it is a race (see `.agents/testing.md` § Known issues, #1847). Wait on the tab's own response
  or on its settled spinner.
- **Table headers are title-case in the DOM**; the uppercase look is `text-transform: uppercase`.
  Case texts write them upper-cased — assert the DOM text, and the CSS if the visual matters.
- **Case-text staleness is the norm on this surface**, not the exception: counts of tabs, cards,
  columns and rows have drifted in every case analysed so far. Check `_surface/known-issues.md`
  before filing a new clarification — file a sibling, never a duplicate.
- **Dev-server gotcha:** Vite's watcher can miss edits to the OneDrive-backed `../EliteaUI/src`.
  If a new testid is invisible in the browser, `curl` the module URL to confirm it is on disk, then
  restart the dev server (cost ~15 min once).
