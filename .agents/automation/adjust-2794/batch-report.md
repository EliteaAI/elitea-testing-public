# Batch cost — adjust-2794

Generated: 2026-10-31T03:51:34.220Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app) runs)
- Gate record (script-authored): green at 2026-10-31T03:52:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.06  ·  0.3h active (cases 1m · lead 15m · stages 0m)  ·  1 dispatches
- Tokens: total 7,720,600  ·  **real work 50,814** (in 21,746 / out 29,068)  ·  cache 7.3M read / 322k write  ·  **cache hit rate 95.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 49 turns  ·  57 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.59 (77%)
- **Per delivered case (incl. overhead): $2.06**
- Avg direct per case (excl. overhead): $0.47
- Direct cost spread: avg $0.47 · median $0.47 · min $0.47 · max $0.47
- Loaded cost spread (direct + even overhead share): avg $2.06 · median $2.06 · min $2.06 · max $2.06
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 16m · median 16m · min 16m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2038 | automated | $0.47 | $2.06 | 15,040 (in 10k / out 5k) | 1m | 16m | 1 | 6 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.59 | 0 | 35,774 (in 11k / out 25k) | 97.1% | 15m | 51 (1) |
| qa-engineer | $0.47 | 1 | 15,040 (in 10k / out 5k) | 77.0% | 1m | 6 (0) |
