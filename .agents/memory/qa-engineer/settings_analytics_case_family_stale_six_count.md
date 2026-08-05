---
name: settings-analytics case family — stale "six" counts
description: ELITEA-23xx analytics cases claim 6 tabs/6 KPIs; live product has 7 tabs, 8 KPIs — case text is stale, not the product
type: reference
---

## What

The `settings-analytics` TMS case family (ELITEA-2310..2329, GitHub issues
#818–#837 in `elitea-testing-public`) was authored against an older/planned
version of the Analytics page. Confirmed live (2026-08-05, localhost,
`AnalyticsContainer.jsx` byte-identical on `main` and `automation/testids`):

- **Tabs: 7**, not 6 — `Overview, Costs, Agents & Pipelines, Tools, Users,
  Health, Guide`. Case text usually says "six tabs: Overview, Agents, Tools,
  Users, Health, Guide" — there is no plain "Agents" tab, it's "Agents &
  Pipelines", and "Costs" is missing from the case's list entirely.
- **KPI cards on Overview: 8**, not 6 — `TEAM, AI ACTIVE, LLM CALLS, TOOL
  RUNS, CHAT MSG, AGENT & PIPELINE RUNS, TOKENS, COST`.
- Default date preset is **"Last 24h"** (1-day span), not "Last 7d" — some
  case text says the pickers "reflect the Last 7d range" by default, which
  also contradicts the same case's own "Last 24h/24d is default" step.

**Confirmed the drift extends BELOW the tab/KPI level too** (ELITEA-2320,
2026-08-05): per-tab chart/table titles, subtitles, and column lists carry
the same staleness. Agents & Pipelines tab: "Most Active Agents" →
live "Most Active Agents & Pipelines"; "Top N by events" → live "Top N by
runs"; "Agent Activity" table → live "Agent & Pipeline Activity"; case's
5-column list (incl. non-existent "Events") → live 8–9 columns (Users
column conditional on `isPersonalProject`); search placeholder "Search by
agent name" → live "Search by agent or pipeline name". One exception found:
the "Chat Messages" chart's title+subtitle matched the case exactly — don't
assume EVERY string in a case from this family is stale, verify each one.

**Drift also extends into the row-click DETAIL sub-views** (ELITEA-2313,
ELITEA-2321, 2026-08-05) — same family, one level deeper: user-detail KPI
count 6→10 (case invents nothing, just under-lists), agent-detail KPI count
5→8 (case here INVENTS a KPI, "Error Rate", that doesn't exist in source or
live at all — a step beyond simple omission), chart titles ("Daily Usage"→
"Runs by Day"), and a table-column "Events"→"Runs" rename that recurs at
this deeper level too. Tools-panel columns/empty-state text ("No tool
data") were the one exact match in ELITEA-2321 — again, verify per-string,
don't assume the whole case is uniformly stale.

## What to do

This is case-text drift, not a product defect — reverse-masking guard
applies (`test-case-analysis` SKILL.md § Classify findings). Classify
`ready-for-automation` and assert the LIVE contract (7 tabs, 8 KPIs, Last
24h/1-day default), file a `question`-labelled clarification issue per case
(strict-per-bug is this project's policy — don't try to bundle across the
family), don't file as `bug`.

## Where the ground truth lives

- Full first-case AFS + Concrete Handles + PROVENANCE:
  `test-specs/settings-analytics/l2_analytics-page-default-load_ELITEA-2310.md`
- Surface digest (testid inventory, no pre-existing testids on this page
  except `analytics-export-button`): `test-specs/settings-analytics/_surface.md`
- First clarification filed: elitea-testing-public#1185 (ELITEA-2310) —
  also names the pattern for ELITEA-2311/2320 so it isn't re-discovered from
  scratch each time.
