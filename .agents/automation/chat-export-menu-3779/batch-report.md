# Batch cost — chat-export-menu-3779

Generated: 2026-10-21T01:58:49.468Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-20 → 2026-10-22 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 18  ·  fix rounds: 1

## What it cost

- Total: $6.80  ·  0.8h active (cases 19m · lead 26m · stages 4m)  ·  15 dispatches
- Tokens: total 12,991,884  ·  **real work 177,860** (in 123,188 / out 54,672)  ·  cache 11.1M read / 1.7M write  ·  **cache hit rate 85.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  117 tool calls (4 err, 97% ok)  ·  skills: workflow-authoring
- Overhead (lead + triage + gate + report, shown once): $2.66 (39%)
  - by stage: lead $1.40 · triage $0.32 (0m) · gate $0.52 (3m) · report $0.41 (1m)
- Rework (fix rounds — already inside per-case direct): $0.37  ·  1 dispatch(es)  ·  2m
- **Per delivered case (incl. overhead): $6.80**
- Avg direct per case (excl. overhead): $4.15
- Direct cost spread: avg $4.15 · median $4.15 · min $4.15 · max $4.15
- Loaded cost spread (direct + even overhead share): avg $6.81 · median $6.81 · min $6.81 · max $6.81
- Active-time spread: avg 19m · median 19m · min 19m · max 19m  ·  loaded: avg 49m · median 49m · min 49m · max 49m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3779 | automated | $4.15 | $6.81 | 119,826 (in 78k / out 41k) | 19m | 49m | 10 | 82 (3) | 1 | 18 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.78 | 8 | 74,698 (in 51k / out 24k) | 89.1% | 10m | 57 (2) |
| qa-engineer | $2.63 | 7 | 79,154 (in 53k / out 26k) | 85.9% | 13m | 45 (2) |
| test-automation-lead | $1.40 | 0 | 24,008 (in 19k / out 5k) | 72.8% | 26m | 15 (0) |
