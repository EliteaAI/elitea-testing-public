# Batch cost — adjust-elitea-0143

Generated: 2026-11-18T09:12:02.911Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-16 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 3

## What it cost

- Total: $4.79  ·  1.1h active (cases 10m · lead 54m · stages 0m)  ·  6 dispatches
- Tokens: total 10,853,981  ·  **real work 123,215** (in 76,762 / out 46,453)  ·  cache 9.6M read / 1.1M write  ·  **cache hit rate 89.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 50 turns  ·  79 tool calls (4 err, 95% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $2.33 (49%)
- Rework (fix rounds — already inside per-case direct): $1.19  ·  3 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $4.79**
- Avg direct per case (excl. overhead): $2.45
- Direct cost spread: avg $2.45 · median $2.45 · min $2.45 · max $2.45
- Loaded cost spread (direct + even overhead share): avg $4.78 · median $4.78 · min $4.78 · max $4.78
- Active-time spread: avg 10m · median 10m · min 10m · max 10m  ·  loaded: avg 64m · median 64m · min 64m · max 64m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0143 | automated | $2.45 | $4.78 | 88,046 (in 65k / out 23k) | 10m | 64m | 6 | 33 (0) | 3 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $2.33 | 0 | 35,169 (in 12k / out 23k) | 92.2% | 54m | 46 (4) |
| test-automation-engineer | $1.37 | 3 | 43,768 (in 31k / out 13k) | 88.1% | 8m | 21 (0) |
| qa-engineer | $1.08 | 3 | 44,278 (in 34k / out 11k) | 74.8% | 2m | 12 (0) |
