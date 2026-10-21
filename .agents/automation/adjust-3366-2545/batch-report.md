# Batch cost — adjust-3366-2545

Generated: 2026-10-21T13:43:54.846Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-20 → 2026-10-22 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (41.07s,39.05s,40.67s runs)
- Gate record (script-authored): green at 2026-10-21T13:43:53Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.06  ·  0.4h active (cases 6m · lead 16m · stages 0m)  ·  2 dispatches
- Tokens: total 5,872,231  ·  **real work 81,988** (in 60,040 / out 21,948)  ·  cache 5.4M read / 399k write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 27 turns  ·  51 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.92 (45%)
- Rework (fix rounds — already inside per-case direct): $0.73  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $2.06**
- Avg direct per case (excl. overhead): $1.14
- Direct cost spread: avg $1.14 · median $1.14 · min $1.14 · max $1.14
- Loaded cost spread (direct + even overhead share): avg $2.06 · median $2.06 · min $2.06 · max $2.06
- Active-time spread: avg 6m · median 6m · min 6m · max 6m  ·  loaded: avg 22m · median 22m · min 22m · max 22m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3366 | automated | $1.14 | $2.06 | 57,016 (in 47k / out 10k) | 6m | 22m | 2 | 22 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.92 | 0 | 24,972 (in 13k / out 12k) | 95.4% | 16m | 29 (1) |
| test-automation-engineer | $0.73 | 1 | 42,355 (in 36k / out 6k) | 88.8% | 5m | 13 (0) |
| qa-engineer | $0.41 | 1 | 14,661 (in 11k / out 4k) | 84.7% | 1m | 9 (0) |
