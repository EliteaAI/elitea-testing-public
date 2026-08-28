# Guide tab — static metric documentation

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Session context for the 2026-08-28 entries: project "Elitea Testing Team", preset `Last 30d` unless stated; zero console errors across the whole Overview -> Tools -> Users -> Health -> Guide walk._

### Guide tab (`AnalyticsGuide.jsx`, ELITEA-2325)
- **ZERO testids**, and **ZERO network** — the tab is a pure render of
  `AnalyticsCommonConstants.GUIDE_SECTIONS`, project- and date-independent. Never write an
  `expect_response` wait for it; wait on the first section instead.
- **9 sections**: `Overview Tab, Overview Charts, Costs Tab, Tokens Tab, Agents & Pipelines Tab,
  Tools Tab, Users Tab, Health Tab, General Concepts`; **43 metric entries** total.
- `Calculation:` renders on **14 of 43** metrics, `Data source:` on **7 of 43** — both are
  `{m.x && ...}` conditionals. Even `COST` inside the `Overview Tab` section has neither. The
  case's "each metric section shows Calculation and Data source" is stale: filed
  elitea-testing-public#1950.
- The blue `#58A6FF` (`rgb(88, 166, 255)`) is on the **value**, not the label — exactly 21 blue
  elements = 14 + 7.
- Descriptions are `white-space: pre-line`, `overflow: visible`, `text-overflow: clip`, never
  clipped -> "not truncated" is assertable as `scrollHeight <= clientHeight` + not-`ellipsis`.
