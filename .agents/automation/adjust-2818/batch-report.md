# Batch cost — adjust-2818

Generated: 2026-10-31T09:55:05.671Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations, ~54s each runs)
- Gate record (script-authored): green at 2026-10-31T09:55:04Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.79  ·  0.3h active (cases 7m · lead 12m · stages 0m)  ·  2 dispatches
- Tokens: total 3,990,362  ·  **real work 46,358** (in 31,651 / out 14,707)  ·  cache 3.5M read / 427k write  ·  **cache hit rate 88.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 11 turns  ·  35 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.78 (44%)
- **Per delivered case (incl. overhead): $1.79**
- Avg direct per case (excl. overhead): $1.01
- Direct cost spread: avg $1.01 · median $1.01 · min $1.01 · max $1.01
- Loaded cost spread (direct + even overhead share): avg $1.79 · median $1.79 · min $1.79 · max $1.79
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 19m · median 19m · min 19m · max 19m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | automated | $1.01 | $1.79 | 30,573 (in 21k / out 10k) | 7m | 19m | 2 | 23 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.78 | 0 | 15,785 (in 11k / out 5k) | 82.9% | 12m | 12 (0) |
| test-automation-engineer | $0.71 | 1 | 18,088 (in 10k / out 8k) | 94.0% | 7m | 19 (0) |
| qa-engineer | $0.30 | 1 | 12,485 (in 10k / out 2k) | 71.4% | 0m | 4 (0) |
