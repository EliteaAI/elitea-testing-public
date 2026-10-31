# Batch cost — adjust-2798

Generated: 2026-10-31T04:34:00.317Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), 0 reruns runs)
- Gate record (script-authored): green at 2026-10-31T04:33:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.45  ·  0.3h active (cases 2m · lead 18m · stages 0m)  ·  2 dispatches
- Tokens: total 9,118,526  ·  **real work 68,746** (in 32,095 / out 36,651)  ·  cache 8.7M read / 371k write  ·  **cache hit rate 95.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 50 turns  ·  65 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.55 (63%)
- **Per delivered case (incl. overhead): $2.45**
- Avg direct per case (excl. overhead): $0.90
- Direct cost spread: avg $0.90 · median $0.90 · min $0.90 · max $0.90
- Loaded cost spread (direct + even overhead share): avg $2.45 · median $2.45 · min $2.45 · max $2.45
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 20m · median 20m · min 20m · max 20m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2034 | automated | $0.90 | $2.45 | 29,358 (in 21k / out 9k) | 2m | 20m | 2 | 12 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.55 | 0 | 39,388 (in 11k / out 28k) | 97.9% | 18m | 53 (1) |
| test-automation-engineer | $0.48 | 1 | 14,283 (in 10k / out 4k) | 81.0% | 1m | 5 (0) |
| qa-engineer | $0.43 | 1 | 15,075 (in 10k / out 5k) | 87.2% | 1m | 7 (0) |
