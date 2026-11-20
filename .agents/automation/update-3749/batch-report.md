# Batch cost — update-3749

Generated: 2026-11-20T08:07:59.479Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: $3.20  ·  0.6h active (cases 15m · lead 19m · stages 0m)  ·  2 dispatches
- Tokens: total 9,672,163  ·  **real work 80,304** (in 31,930 / out 48,374)  ·  cache 9.0M read / 583k write  ·  **cache hit rate 93.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  63 tool calls (2 err, 97% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.03 (32%)
- **Per delivered case (incl. overhead): $3.20**
- Avg direct per case (excl. overhead): $2.17
- Direct cost spread: avg $2.17 · median $2.17 · min $2.17 · max $2.17
- Loaded cost spread (direct + even overhead share): avg $3.20 · median $3.20 · min $3.20 · max $3.20
- Active-time spread: avg 15m · median 15m · min 15m · max 15m  ·  loaded: avg 34m · median 34m · min 34m · max 34m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | automated | $2.17 | $3.20 | 61,729 (in 21k / out 41k) | 15m | 34m | 2 | 46 (2) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.77 | 1 | 45,712 (in 10k / out 35k) | 96.8% | 14m | 41 (2) |
| test-automation-lead | $1.03 | 0 | 18,575 (in 11k / out 8k) | 85.4% | 19m | 17 (0) |
| qa-engineer | $0.40 | 1 | 16,017 (in 11k / out 5k) | 82.2% | 1m | 5 (0) |
