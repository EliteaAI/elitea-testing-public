# Batch cost — agent-modules-persist-4790

Generated: 2026-11-23T18:48:47.108Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-22 → 2026-11-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-23T18:48:45Z (1 run record(s))
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: $9.11  ·  1.4h active (cases 28m · lead 42m · stages 14m)  ·  16 dispatches
- Tokens: total 22,892,723  ·  **real work 206,990** (in 121,944 / out 85,046)  ·  cache 20.3M read / 2.4M write  ·  **cache hit rate 89.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 37 turns  ·  196 tool calls (14 err, 93% ok)
- Overhead (lead + triage + gate + report, shown once): $5.20 (57%)
  - by stage: lead $2.73 · triage $0.31 (0m) · gate $1.80 (13m) · report $0.37 (1m)
- **Per delivered case (incl. overhead): $9.11**
- Avg direct per case (excl. overhead): $3.90
- Direct cost spread: avg $3.90 · median $3.90 · min $3.90 · max $3.90
- Loaded cost spread (direct + even overhead share): avg $9.10 · median $9.10 · min $9.10 · max $9.10
- Active-time spread: avg 28m · median 28m · min 28m · max 28m  ·  loaded: avg 84m · median 84m · min 84m · max 84m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4790 | automated | $3.90 | $9.10 | 113,602 (in 60k / out 53k) | 28m | 84m | 8 | 95 (4) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.78 | 9 | 96,007 (in 60k / out 36k) | 92.1% | 22m | 101 (5) |
| test-automation-lead | $2.73 | 0 | 29,321 (in 19k / out 11k) | 78.0% | 42m | 36 (6) |
| qa-engineer | $2.60 | 7 | 81,662 (in 43k / out 38k) | 90.4% | 20m | 59 (3) |
