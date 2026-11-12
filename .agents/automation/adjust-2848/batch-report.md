# Batch cost — adjust-2848

Generated: 2026-11-12T07:26:47.413Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-01 → 2026-11-13 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.86  ·  0.3h active (cases 3m · lead 12m · stages 0m)  ·  2 dispatches
- Tokens: total 8,246,914  ·  **real work 66,609** (in 32,903 / out 33,706)  ·  cache 7.6M read / 576k write  ·  **cache hit rate 92.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 41 turns  ·  60 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.84 (64%)
- **Per delivered case (incl. overhead): $2.86**
- Avg direct per case (excl. overhead): $1.03
- Direct cost spread: avg $1.03 · median $1.03 · min $1.03 · max $1.03
- Loaded cost spread (direct + even overhead share): avg $2.87 · median $2.87 · min $2.87 · max $2.87
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 15m · median 15m · min 15m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1954 | automated | $1.03 | $2.87 | 32,189 (in 21k / out 11k) | 3m | 15m | 2 | 18 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.84 | 0 | 34,420 (in 12k / out 22k) | 94.3% | 12m | 42 (0) |
| test-automation-engineer | $0.63 | 1 | 17,534 (in 10k / out 7k) | 88.6% | 2m | 11 (0) |
| qa-engineer | $0.39 | 1 | 14,655 (in 11k / out 4k) | 85.3% | 1m | 7 (0) |
