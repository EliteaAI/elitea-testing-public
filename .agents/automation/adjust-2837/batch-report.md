# Batch cost — adjust-2837

Generated: 2026-11-01T04:53:13.245Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-31 → 2026-11-02 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.53  ·  0.4h active (cases 8m · lead 16m · stages 0m)  ·  2 dispatches
- Tokens: total 7,533,800  ·  **real work 62,000** (in 31,839 / out 30,161)  ·  cache 7.0M read / 487k write  ·  **cache hit rate 93.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 28 turns  ·  58 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.25 (49%)
- Rework (fix rounds — already inside per-case direct): $0.94  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $2.53**
- Avg direct per case (excl. overhead): $1.28
- Direct cost spread: avg $1.28 · median $1.28 · min $1.28 · max $1.28
- Loaded cost spread (direct + even overhead share): avg $2.53 · median $2.53 · min $2.53 · max $2.53
- Active-time spread: avg 8m · median 8m · min 8m · max 8m  ·  loaded: avg 24m · median 24m · min 24m · max 24m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0852 | automated | $1.28 | $2.53 | 38,124 (in 21k / out 17k) | 8m | 24m | 2 | 29 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.25 | 0 | 23,876 (in 11k / out 13k) | 92.9% | 16m | 29 (0) |
| test-automation-engineer | $0.94 | 1 | 24,374 (in 10k / out 14k) | 95.4% | 7m | 25 (0) |
| qa-engineer | $0.35 | 1 | 13,750 (in 10k / out 3k) | 78.1% | 1m | 4 (0) |
