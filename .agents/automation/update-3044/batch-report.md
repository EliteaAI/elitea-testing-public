# Batch cost — update-3044

Generated: 2026-11-26T16:44:19.687Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-25 → 2026-11-27 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-26 (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.25  ·  0.2h active (cases 3m · lead 9m · stages 0m)  ·  2 dispatches
- Tokens: total 3,467,952  ·  **real work 46,007** (in 32,436 / out 13,571)  ·  cache 3.1M read / 294k write  ·  **cache hit rate 90.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  33 tool calls (3 err, 91% ok)
- Overhead (lead + triage + gate + report, shown once): $0.43 (34%)
- Rework (fix rounds — already inside per-case direct): $0.51  ·  1 dispatch(es)  ·  3m
- **Per delivered case (incl. overhead): $1.25**
- Avg direct per case (excl. overhead): $0.82
- Direct cost spread: avg $0.82 · median $0.82 · min $0.82 · max $0.82
- Loaded cost spread (direct + even overhead share): avg $1.25 · median $1.25 · min $1.25 · max $1.25
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 12m · median 12m · min 12m · max 12m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | automated | $0.82 | $1.25 | 28,957 (in 21k / out 8k) | 3m | 12m | 2 | 18 (2) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.51 | 1 | 15,233 (in 11k / out 5k) | 89.8% | 3m | 12 (2) |
| test-automation-lead | $0.43 | 0 | 17,050 (in 11k / out 6k) | 94.6% | 9m | 15 (1) |
| qa-engineer | $0.31 | 1 | 13,724 (in 11k / out 3k) | 78.5% | 0m | 6 (0) |
