# Batch cost — adjust-2805

Generated: 2026-10-31T07:16:10.343Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations; an earlier attempt had run 3 red on a Step-1 navigation precondition timeout (known networkidle flake class), full 3x re-gate then 3/3 green runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 1

## What it cost

- Total: $3.15  ·  0.8h active (cases 10m · lead 37m · stages 0m)  ·  2 dispatches
- Tokens: total 10,972,646  ·  **real work 78,332** (in 34,845 / out 43,487)  ·  cache 10.4M read / 530k write  ·  **cache hit rate 94.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 49 turns  ·  77 tool calls (1 err, 99% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.79 (57%)
- Rework (fix rounds — already inside per-case direct): $0.90  ·  1 dispatch(es)  ·  9m
- **Per delivered case (incl. overhead): $3.15**
- Avg direct per case (excl. overhead): $1.37
- Direct cost spread: avg $1.37 · median $1.37 · min $1.37 · max $1.37
- Loaded cost spread (direct + even overhead share): avg $3.16 · median $3.16 · min $3.16 · max $3.16
- Active-time spread: avg 10m · median 10m · min 10m · max 10m  ·  loaded: avg 47m · median 47m · min 47m · max 47m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1866 | automated | $1.37 | $3.16 | 38,996 (in 21k / out 18k) | 10m | 47m | 2 | 26 (0) | 1 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.79 | 0 | 39,336 (in 14k / out 25k) | 96.2% | 37m | 51 (1) |
| test-automation-engineer | $0.90 | 1 | 22,976 (in 10k / out 13k) | 94.1% | 9m | 19 (0) |
| qa-engineer | $0.47 | 1 | 16,020 (in 10k / out 6k) | 85.8% | 1m | 7 (0) |
