# Batch cost — chat-zip-export-3764

Generated: 2026-10-21T01:31:30.090Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-20 → 2026-10-22 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 19  ·  fix rounds: 1

## What it cost

- Total: $7.63  ·  1.1h active (cases 22m · lead 37m · stages 5m)  ·  15 dispatches
- Tokens: total 13,431,065  ·  **real work 204,072** (in 142,358 / out 61,714)  ·  cache 11.3M read / 2.0M write  ·  **cache hit rate 84.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  119 tool calls (6 err, 95% ok)
- Overhead (lead + triage + gate + report, shown once): $2.95 (39%)
  - by stage: lead $1.67 · triage $0.34 (0m) · gate $0.50 (4m) · report $0.44 (1m)
- Rework (fix rounds — already inside per-case direct): $0.73  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $7.63**
- Avg direct per case (excl. overhead): $4.69
- Direct cost spread: avg $4.69 · median $4.69 · min $4.69 · max $4.69
- Loaded cost spread (direct + even overhead share): avg $7.64 · median $7.64 · min $7.64 · max $7.64
- Active-time spread: avg 22m · median 22m · min 22m · max 22m  ·  loaded: avg 64m · median 64m · min 64m · max 64m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3764 | automated | $4.69 | $7.64 | 142,901 (in 98k / out 45k) | 22m | 64m | 10 | 86 (2) | 1 | 19 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.11 | 8 | 100,434 (in 70k / out 31k) | 88.6% | 16m | 57 (4) |
| qa-engineer | $2.86 | 7 | 79,083 (in 54k / out 25k) | 84.1% | 11m | 47 (1) |
| test-automation-lead | $1.67 | 0 | 24,555 (in 19k / out 6k) | 66.6% | 37m | 15 (1) |
