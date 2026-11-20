# Batch cost — toolkit-copy-4758

Generated: 2026-11-20T12:59:22.653Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: $5.91  ·  0.8h active (cases 16m · lead 30m · stages 3m)  ·  12 dispatches
- Tokens: total 10,803,859  ·  **real work 138,555** (in 94,546 / out 44,009)  ·  cache 9.1M read / 1.5M write  ·  **cache hit rate 84.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  100 tool calls (3 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $2.71 (46%)
  - by stage: lead $1.46 · triage $0.33 (0m) · gate $0.49 (2m) · report $0.42 (1m)
- **Per delivered case (incl. overhead): $5.91**
- Avg direct per case (excl. overhead): $3.20
- Direct cost spread: avg $3.20 · median $3.20 · min $3.20 · max $3.20
- Loaded cost spread (direct + even overhead share): avg $5.91 · median $5.91 · min $5.91 · max $5.91
- Active-time spread: avg 16m · median 16m · min 16m · max 16m  ·  loaded: avg 49m · median 49m · min 49m · max 49m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4758 | automated | $3.20 | $5.91 | 80,530 (in 51k / out 29k) | 16m | 49m | 7 | 61 (2) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.68 | 7 | 66,195 (in 43k / out 24k) | 89.4% | 16m | 55 (1) |
| qa-engineer | $1.77 | 5 | 48,097 (in 35k / out 14k) | 77.9% | 3m | 24 (2) |
| test-automation-lead | $1.46 | 0 | 24,263 (in 17k / out 7k) | 79.6% | 30m | 21 (0) |
