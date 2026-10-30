# Batch cost — fix-2759-delete-node

Generated: 2026-10-30T07:23:46.467Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.04  ·  0.3h active (cases 2m · lead 13m · stages 0m)  ·  2 dispatches
- Tokens: total 7,374,296  ·  **real work 56,339** (in 32,070 / out 24,269)  ·  cache 7.0M read / 340k write  ·  **cache hit rate 94.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 43 turns  ·  52 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.29 (63%)
- **Per delivered case (incl. overhead): $2.04**
- Avg direct per case (excl. overhead): $0.75
- Direct cost spread: avg $0.75 · median $0.75 · min $0.75 · max $0.75
- Loaded cost spread (direct + even overhead share): avg $2.04 · median $2.04 · min $2.04 · max $2.04
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 15m · median 15m · min 15m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2060 | automated | $0.75 | $2.04 | 26,311 (in 21k / out 5k) | 2m | 15m | 2 | 8 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.29 | 0 | 30,028 (in 11k / out 19k) | 97.7% | 13m | 44 (0) |
| qa-engineer | $0.40 | 1 | 13,543 (in 10k / out 3k) | 72.0% | 1m | 4 (0) |
| test-automation-engineer | $0.35 | 1 | 12,768 (in 10k / out 2k) | 82.9% | 1m | 4 (0) |
