# Batch cost — fix-2654

Generated: 2026-10-24T06:16:58.324Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-23 → 2026-10-25 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at 2026-10-24T06:16:57Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.04  ·  0.3h active (cases 1m · lead 17m · stages 0m)  ·  1 dispatches
- Tokens: total 8,876,770  ·  **real work 51,032** (in 21,625 / out 29,407)  ·  cache 8.6M read / 265k write  ·  **cache hit rate 96.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 55 turns  ·  65 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.56 (76%)
- **Per delivered case (incl. overhead): $2.04**
- Avg direct per case (excl. overhead): $0.48
- Direct cost spread: avg $0.48 · median $0.48 · min $0.48 · max $0.48
- Loaded cost spread (direct + even overhead share): avg $2.04 · median $2.04 · min $2.04 · max $2.04
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 18m · median 18m · min 18m · max 18m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2034 | automated | $0.48 | $2.04 | 14,987 (in 10k / out 4k) | 1m | 18m | 1 | 7 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.56 | 0 | 36,045 (in 11k / out 25k) | 98.1% | 17m | 58 (1) |
| qa-engineer | $0.48 | 1 | 14,987 (in 10k / out 4k) | 83.8% | 1m | 7 (0) |
