# Batch cost — adjust-2802

Generated: 2026-10-31T06:27:50.142Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.84  ·  0.5h active (cases 0m · lead 29m · stages 0m)  ·  1 dispatches
- Tokens: total 5,516,338  ·  **real work 44,267** (in 22,024 / out 22,243)  ·  cache 5.1M read / 356k write  ·  **cache hit rate 93.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 41 turns  ·  46 tool calls (2 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.46 (79%)
- **Per delivered case (incl. overhead): $1.84**
- Avg direct per case (excl. overhead): $0.38
- Direct cost spread: avg $0.38 · median $0.38 · min $0.38 · max $0.38
- Loaded cost spread (direct + even overhead share): avg $1.84 · median $1.84 · min $1.84 · max $1.84
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 29m · median 29m · min 29m · max 29m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2378 | automated | $0.38 | $1.84 | 12,493 (in 10k / out 2k) | 0m | 29m | 1 | 3 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.46 | 0 | 31,774 (in 12k / out 20k) | 95.1% | 29m | 43 (2) |
| qa-engineer | $0.38 | 1 | 12,493 (in 10k / out 2k) | 62.7% | 0m | 3 (0) |
