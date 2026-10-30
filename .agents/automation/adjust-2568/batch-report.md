# Batch cost — adjust-2568

Generated: 2026-10-23T04:05:14.285Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-10-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.52  ·  0.3h active (cases 1m · lead 15m · stages 0m)  ·  1 dispatches
- Tokens: total 5,647,110  ·  **real work 41,922** (in 21,624 / out 20,298)  ·  cache 5.4M read / 239k write  ·  **cache hit rate 95.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 38 turns  ·  44 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.11 (73%)
- **Per delivered case (incl. overhead): $1.52**
- Avg direct per case (excl. overhead): $0.41
- Direct cost spread: avg $0.41 · median $0.41 · min $0.41 · max $0.41
- Loaded cost spread (direct + even overhead share): avg $1.52 · median $1.52 · min $1.52 · max $1.52
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 16m · median 16m · min 16m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2030 | automated | $0.41 | $1.52 | 13,204 (in 10k / out 3k) | 1m | 16m | 1 | 4 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.11 | 0 | 28,718 (in 11k / out 18k) | 97.4% | 15m | 40 (1) |
| qa-engineer | $0.41 | 1 | 13,204 (in 10k / out 3k) | 71.8% | 1m | 4 (0) |
