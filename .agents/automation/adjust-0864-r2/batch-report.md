# Batch cost — adjust-0864-r2

Generated: 2026-10-25T04:10:57.372Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.77  ·  0.4h active (cases 0m · lead 25m · stages 0m)  ·  1 dispatches
- Tokens: total 5,306,913  ·  **real work 41,420** (in 21,551 / out 19,869)  ·  cache 4.9M read / 350k write  ·  **cache hit rate 93.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 40 turns  ·  45 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.37 (77%)
- **Per delivered case (incl. overhead): $1.77**
- Avg direct per case (excl. overhead): $0.40
- Direct cost spread: avg $0.40 · median $0.40 · min $0.40 · max $0.40
- Loaded cost spread (direct + even overhead share): avg $1.77 · median $1.77 · min $1.77 · max $1.77
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 25m · median 25m · min 25m · max 25m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0864 | automated | $0.40 | $1.77 | 13,275 (in 11k / out 3k) | 0m | 25m | 1 | 4 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.37 | 0 | 28,145 (in 11k / out 17k) | 94.9% | 25m | 41 (1) |
| qa-engineer | $0.40 | 1 | 13,275 (in 11k / out 3k) | 71.9% | 0m | 4 (0) |
