# Batch cost — elitea-4655-web-search-default-modules

Generated: 2026-11-11T20:42:54.851Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-11T20:43:00Z (3 run record(s))
- Findings reported: 20  ·  fix rounds: 2

## What it cost

- Total: $11.99  ·  2.7h active (cases 70m · lead 86m · stages 6m)  ·  17 dispatches
- Tokens: total 23,560,551  ·  **real work 239,041** (in 139,586 / out 99,455)  ·  cache 20.3M read / 3.0M write  ·  **cache hit rate 86.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 24 turns  ·  199 tool calls (7 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $4.52 (38%)
  - by stage: lead $3.26 · triage $0.33 (0m) · gate $0.52 (5m) · report $0.42 (1m)
- Rework (fix rounds — already inside per-case direct): $0.97  ·  2 dispatch(es)  ·  16m
- **Per delivered case (incl. overhead): $11.99**
- Avg direct per case (excl. overhead): $7.47
- Direct cost spread: avg $7.47 · median $7.47 · min $7.47 · max $7.47
- Loaded cost spread (direct + even overhead share): avg $11.99 · median $11.99 · min $11.99 · max $11.99
- Active-time spread: avg 70m · median 70m · min 70m · max 70m  ·  loaded: avg 162m · median 162m · min 162m · max 162m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4655 | automated | $7.47 | $11.99 | 178,151 (in 94k / out 84k) | 70m | 162m | 12 | 156 (4) | 2 | 20 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $5.00 | 9 | 110,145 (in 60k / out 51k) | 90.7% | 63m | 102 (4) |
| qa-engineer | $3.73 | 8 | 102,197 (in 60k / out 42k) | 88.8% | 13m | 73 (3) |
| test-automation-lead | $3.26 | 0 | 26,699 (in 20k / out 7k) | 59.7% | 86m | 24 (0) |
