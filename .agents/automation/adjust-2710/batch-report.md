# Batch cost — adjust-2710

Generated: 2026-10-26T07:49:50.829Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-25 → 2026-10-27 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (22.39s,21.88s,22.28s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.49  ·  0.1h active (cases 3m · lead 6m · stages 0m)  ·  2 dispatches
- Tokens: total 3,718,871  ·  **real work 45,832** (in 31,733 / out 14,099)  ·  cache 3.3M read / 326k write  ·  **cache hit rate 90.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  33 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.54 (36%)
- **Per delivered case (incl. overhead): $1.49**
- Avg direct per case (excl. overhead): $0.95
- Direct cost spread: avg $0.95 · median $0.95 · min $0.95 · max $0.95
- Loaded cost spread (direct + even overhead share): avg $1.49 · median $1.49 · min $1.49 · max $1.49
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 9m · median 9m · min 9m · max 9m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2058 | automated | $0.95 | $1.49 | 28,713 (in 21k / out 8k) | 3m | 9m | 2 | 16 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.64 | 1 | 15,969 (in 11k / out 5k) | 89.5% | 3m | 12 (0) |
| test-automation-lead | $0.54 | 0 | 17,119 (in 11k / out 6k) | 94.0% | 6m | 17 (0) |
| qa-engineer | $0.32 | 1 | 12,744 (in 10k / out 2k) | 78.7% | 0m | 4 (0) |
