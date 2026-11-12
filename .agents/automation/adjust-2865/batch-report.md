# Batch cost — adjust-2865

Generated: 2026-11-03T05:39:42.246Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-02 → 2026-11-04 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-03T05:39:40Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.83  ·  0.3h active (cases 4m · lead 12m · stages 0m)  ·  2 dispatches
- Tokens: total 5,396,584  ·  **real work 55,613** (in 31,970 / out 23,643)  ·  cache 5.0M read / 338k write  ·  **cache hit rate 93.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  49 tool calls (2 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.91 (50%)
- Rework (fix rounds — already inside per-case direct): $0.52  ·  1 dispatch(es)  ·  3m
- **Per delivered case (incl. overhead): $1.83**
- Avg direct per case (excl. overhead): $0.92
- Direct cost spread: avg $0.92 · median $0.92 · min $0.92 · max $0.92
- Loaded cost spread (direct + even overhead share): avg $1.83 · median $1.83 · min $1.83 · max $1.83
- Active-time spread: avg 4m · median 4m · min 4m · max 4m  ·  loaded: avg 16m · median 16m · min 16m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0062 | automated | $0.92 | $1.83 | 31,219 (in 21k / out 10k) | 4m | 16m | 2 | 16 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.91 | 0 | 24,394 (in 11k / out 13k) | 96.7% | 12m | 33 (2) |
| test-automation-engineer | $0.52 | 1 | 14,745 (in 10k / out 4k) | 83.5% | 3m | 8 (0) |
| qa-engineer | $0.40 | 1 | 16,474 (in 10k / out 6k) | 85.5% | 1m | 8 (0) |
