# Batch cost — adjust-2800

Generated: 2026-10-31T05:25:24.646Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations runs)
- Gate record (script-authored): green at 2026-10-31T05:25:23Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.39  ·  0.4h active (cases 7m · lead 17m · stages 0m)  ·  2 dispatches
- Tokens: total 5,830,795  ·  **real work 59,896** (in 31,671 / out 28,225)  ·  cache 5.2M read / 522k write  ·  **cache hit rate 90.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 23 turns  ·  47 tool calls (2 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.26 (53%)
- **Per delivered case (incl. overhead): $2.39**
- Avg direct per case (excl. overhead): $1.13
- Direct cost spread: avg $1.13 · median $1.13 · min $1.13 · max $1.13
- Loaded cost spread (direct + even overhead share): avg $2.39 · median $2.39 · min $2.39 · max $2.39
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 24m · median 24m · min 24m · max 24m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2041 | automated | $1.13 | $2.39 | 37,060 (in 21k / out 16k) | 7m | 24m | 2 | 22 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.26 | 0 | 22,836 (in 11k / out 12k) | 90.3% | 17m | 25 (1) |
| test-automation-engineer | $0.78 | 1 | 22,190 (in 10k / out 12k) | 93.1% | 6m | 17 (1) |
| qa-engineer | $0.35 | 1 | 14,870 (in 10k / out 4k) | 78.3% | 1m | 5 (0) |
