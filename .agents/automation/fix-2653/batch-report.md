# Batch cost — fix-2653

Generated: 2026-10-24T05:52:47.641Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-23 → 2026-10-25 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 1**  ·  automated 1  ·  blocked 1
- Gate: green
- Gate record (script-authored): green at 2026-10-24T06:10:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.48  ·  0.4h active (cases 6m · lead 20m · stages 0m)  ·  2 dispatches
- Tokens: total 6,595,378  ·  **real work 59,710** (in 31,791 / out 27,919)  ·  cache 6.0M read / 524k write  ·  **cache hit rate 91.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 33 turns  ·  56 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.31 (53%)
- **Per delivered case (incl. overhead): $2.48**
- Avg direct per case (excl. overhead): $0.59
- Direct cost spread: avg $0.59 · median $0.59 · min $0.59 · max $0.59
- Loaded cost spread (direct + even overhead share): avg $1.24 · median $1.24 · min $1.24 · max $1.24
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 13m · median 13m · min 13m · max 13m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2014 | automated | $0.59 | $1.24 | 16,526 (in 10k / out 6k) | 3m | 13m | 1 | 11 (0) | 0 | 0 |
| ELITEA-2036 | blocked | $0.59 | $1.24 | 16,526 (in 10k / out 6k) | 3m | 13m | 1 | 11 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.31 | 0 | 26,659 (in 11k / out 16k) | 93.5% | 20m | 35 (1) |
| test-automation-engineer | $0.77 | 1 | 18,768 (in 10k / out 8k) | 91.4% | 5m | 15 (0) |
| qa-engineer | $0.41 | 1 | 14,283 (in 10k / out 4k) | 76.7% | 1m | 6 (0) |
