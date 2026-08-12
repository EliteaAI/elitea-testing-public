---
name: settings-analytics case family — stale case text, brand-new surface
description: ELITEA-2310..2329 (GH #818-#837) describe a settings/analytics page whose case text (tab counts, tab names, default preset labels) is stale vs. the live product; zero pre-existing testids on the whole surface as of ELITEA-2310.
type: project
---

## What's true as of 2026-08-05 (ELITEA-2310)

- `settings-analytics` was a **brand-new automation surface** before ELITEA-2310:
  zero pre-existing testids on anything the case touches. First case added 17
  (`analytics-page-title`, `analytics-project-badge`, `analytics-date-preset-{1,7,30,90}`,
  `analytics-date-{from,to}-input`, `analytics-loading-indicator`,
  `analytics-tab-{overview,costs,agents-pipelines,tools,users,health,guide}`,
  `analytics-overview-kpi-row`) — all on `automation/testids`, none yet on `main`
  (EliteaAI/EliteaUI@4ee69fc2 + @bc31aa7c).
- The case family **ELITEA-2310..2329** (GH issues **#818-#837**) covers this same
  page. ELITEA-2310's case text was stale on three separate points: claimed
  **6 tabs**, live has **7** (adds "Costs"; "Agents" → "Agents & Pipelines");
  claimed default preset label **"Last 24d"**, live shows **"Last 24h"**; claimed
  default range **"Last 7d"**, live defaults to **1 day**. Filed as clarification
  elitea-testing-public#1185.
- Spot-checked two siblings and found the SAME pattern: **#819/ELITEA-2311**
  ("six KPI cards" vs live **8**: TEAM / AI ACTIVE / LLM CALLS / TOOL RUNS /
  CHAT MSG / AGENT & PIPELINE RUNS / TOKENS / COST) and **#828/ELITEA-2320**
  ("Agents tab" naming, same as the #2310 drift).

## What this means for future batches on this family

- Expect the analyst to file a `question`-labelled clarification on most/all of
  ELITEA-2311..2329 — this is the case-text-drift pattern recurring, not a new
  surprise each time. Don't second-guess a `ready-for-automation` verdict that
  cites this pattern; it is the correct reverse-masking-guard response (assert
  the live contract, flag the stale text, keep going).
  See `.agents/testing.md` / `test-case-analysis` for the reverse-masking rule.
- Once a `settings-analytics/_surface.md` digest exists (it does, from ELITEA-2310),
  later cases in this family are eligible for the workflow's triage → combined
  analyse+build routing (`tiering: 'auto'`) rather than a standalone analyst —
  check the digest is still current before trusting that routing.
