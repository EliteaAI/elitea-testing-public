# Batch cost — adjust-2685

Generated: 2026-10-25T09:26:00.714Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (11.97s,12.01s,12.19s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.32  ·  0.4h active (cases 9m · lead 16m · stages 0m)  ·  2 dispatches
- Tokens: total 5,780,048  ·  **real work 57,393** (in 33,631 / out 23,762)  ·  cache 5.2M read / 514k write  ·  **cache hit rate 90.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 18 turns  ·  47 tool calls (3 err, 94% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.11 (48%)
- Rework (fix rounds — already inside per-case direct): $0.77  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $2.32**
- Avg direct per case (excl. overhead): $1.21
- Direct cost spread: avg $1.21 · median $1.21 · min $1.21 · max $1.21
- Loaded cost spread (direct + even overhead share): avg $2.32 · median $2.32 · min $2.32 · max $2.32
- Active-time spread: avg 9m · median 9m · min 9m · max 9m  ·  loaded: avg 25m · median 25m · min 25m · max 25m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2377 | automated | $1.21 | $2.32 | 35,925 (in 23k / out 13k) | 9m | 25m | 2 | 28 (1) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.11 | 0 | 21,468 (in 11k / out 11k) | 88.0% | 16m | 19 (2) |
| test-automation-engineer | $0.77 | 1 | 19,483 (in 10k / out 9k) | 94.4% | 8m | 21 (1) |
| qa-engineer | $0.43 | 1 | 16,442 (in 12k / out 4k) | 84.5% | 1m | 7 (0) |
