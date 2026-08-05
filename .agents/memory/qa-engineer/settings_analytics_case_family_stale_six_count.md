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
