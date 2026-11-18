# Batch cost — adjust-2982

Generated: 2026-11-18T18:22:25.222Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.48  ·  0.5h active (cases 10m · lead 19m · stages 0m)  ·  2 dispatches
- Tokens: total 6,686,913  ·  **real work 58,360** (in 34,236 / out 24,124)  ·  cache 6.1M read / 536k write  ·  **cache hit rate 91.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 28 turns  ·  53 tool calls (2 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $1.29 (52%)
- Rework (fix rounds — already inside per-case direct): $0.90  ·  1 dispatch(es)  ·  10m
- **Per delivered case (incl. overhead): $1.24**
- Avg direct per case (excl. overhead): $0.60
- Direct cost spread: avg $0.60 · median $0.60 · min $0.60 · max $0.60
- Loaded cost spread (direct + even overhead share): avg $1.24 · median $1.24 · min $1.24 · max $1.24
- Active-time spread: avg 5m · median 5m · min 5m · max 5m  ·  loaded: avg 15m · median 15m · min 15m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2017 | automated | $0.60 | $1.24 | 16,727 (in 11k / out 6k) | 5m | 15m | 1 | 13 (1) | 0.5 | 0 |
| ELITEA-2058 | automated | $0.60 | $1.24 | 16,727 (in 11k / out 6k) | 5m | 15m | 1 | 13 (1) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.29 | 0 | 24,906 (in 13k / out 12k) | 90.3% | 19m | 28 (0) |
| test-automation-engineer | $0.90 | 1 | 20,963 (in 10k / out 10k) | 94.7% | 10m | 22 (2) |
| qa-engineer | $0.30 | 1 | 12,491 (in 11k / out 2k) | 72.0% | 0m | 3 (0) |
