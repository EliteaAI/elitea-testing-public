# Batch cost — adjust-2801

Generated: 2026-10-31T05:46:03.857Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations, reruns {} each. An earlier gate set was discarded: run 3 passed only after a rerun (transient 15s wait_for_function timeout at detail-page load); re-gated 3/3 clean. runs)
- Gate record (script-authored): green at 2026-10-31T05:46:01Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.34  ·  0.4h active (cases 7m · lead 15m · stages 0m)  ·  2 dispatches
- Tokens: total 5,542,737  ·  **real work 56,967** (in 31,728 / out 25,239)  ·  cache 5.0M read / 526k write  ·  **cache hit rate 89.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 23 turns  ·  41 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.20 (51%)
- Rework (fix rounds — already inside per-case direct): $0.80  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $2.34**
- Avg direct per case (excl. overhead): $1.14
- Direct cost spread: avg $1.14 · median $1.14 · min $1.14 · max $1.14
- Loaded cost spread (direct + even overhead share): avg $2.34 · median $2.34 · min $2.34 · max $2.34
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 22m · median 22m · min 22m · max 22m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2014 | automated | $1.14 | $2.34 | 34,366 (in 21k / out 13k) | 7m | 22m | 2 | 18 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.20 | 0 | 22,601 (in 11k / out 12k) | 90.2% | 15m | 23 (1) |
| test-automation-engineer | $0.80 | 1 | 21,124 (in 10k / out 11k) | 92.0% | 7m | 14 (0) |
| qa-engineer | $0.34 | 1 | 13,242 (in 10k / out 3k) | 78.4% | 0m | 4 (0) |
