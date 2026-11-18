# Batch cost — adjust-2835b

Generated: 2026-11-18T16:25:36.287Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-31 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (6 runs)
- Gate record (script-authored): undefined at ? (6 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $6.32  ·  1.5h active (cases 48m · lead 40m · stages 0m)  ·  5 dispatches
- Tokens: total 13,906,219  ·  **real work 127,019** (in 67,499 / out 59,520)  ·  cache 12.3M read / 1.5M write  ·  **cache hit rate 88.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 56 turns  ·  101 tool calls (4 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $2.58 (41%)
- Rework (fix rounds — already inside per-case direct): $0.64  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $6.32**
- Avg direct per case (excl. overhead): $3.74
- Direct cost spread: avg $3.74 · median $3.74 · min $3.74 · max $3.74
- Loaded cost spread (direct + even overhead share): avg $6.32 · median $6.32 · min $6.32 · max $6.32
- Active-time spread: avg 48m · median 48m · min 48m · max 48m  ·  loaded: avg 88m · median 88m · min 88m · max 88m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2016 | automated | $3.74 | $6.32 | 87,259 (in 53k / out 34k) | 48m | 88m | 5 | 43 (2) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.70 | 2 | 43,472 (in 22k / out 22k) | 81.3% | 47m | 29 (2) |
| test-automation-lead | $2.58 | 0 | 39,760 (in 14k / out 25k) | 93.5% | 40m | 58 (2) |
| qa-engineer | $1.04 | 3 | 43,787 (in 32k / out 12k) | 82.0% | 1m | 14 (0) |
