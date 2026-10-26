# Batch cost — adjust-2706

Generated: 2026-10-26T06:03:05.957Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-25 → 2026-10-27 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3/3 passed, separate invocations, DEV, APP_PREFIX=/app runs)
- Gate record (script-authored): green at ? (1 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.59  ·  0.2h active (cases 2m · lead 11m · stages 0m)  ·  2 dispatches
- Tokens: total 4,492,786  ·  **real work 47,262** (in 31,889 / out 15,373)  ·  cache 4.1M read / 318k write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 27 turns  ·  38 tool calls (2 err, 95% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.78 (49%)
- Rework (fix rounds — already inside per-case direct): $0.51  ·  1 dispatch(es)  ·  2m
- **Per delivered case (incl. overhead): $1.59**
- Avg direct per case (excl. overhead): $0.81
- Direct cost spread: avg $0.81 · median $0.81 · min $0.81 · max $0.81
- Loaded cost spread (direct + even overhead share): avg $1.59 · median $1.59 · min $1.59 · max $1.59
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 13m · median 13m · min 13m · max 13m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0858 | automated | $0.81 | $1.59 | 25,425 (in 21k / out 5k) | 2m | 13m | 2 | 10 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.78 | 0 | 21,837 (in 11k / out 11k) | 96.6% | 11m | 28 (2) |
| test-automation-engineer | $0.51 | 1 | 13,075 (in 10k / out 3k) | 83.7% | 2m | 7 (0) |
| qa-engineer | $0.30 | 1 | 12,350 (in 10k / out 2k) | 71.7% | 0m | 3 (0) |
