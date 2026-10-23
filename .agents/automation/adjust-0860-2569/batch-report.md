# Batch cost — adjust-0860-2569

Generated: 2026-10-23T04:30:41.159Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-10-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.28  ·  0.3h active (cases 0m · lead 16m · stages 0m)  ·  1 dispatches
- Tokens: total 4,294,280  ·  **real work 39,261** (in 21,574 / out 17,687)  ·  cache 4.0M read / 215k write  ·  **cache hit rate 94.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 31 turns  ·  37 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.88 (69%)
- **Per delivered case (incl. overhead): $1.28**
- Avg direct per case (excl. overhead): $0.40
- Direct cost spread: avg $0.40 · median $0.40 · min $0.40 · max $0.40
- Loaded cost spread (direct + even overhead share): avg $1.28 · median $1.28 · min $1.28 · max $1.28
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 16m · median 16m · min 16m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0860 | automated | $0.40 | $1.28 | 13,373 (in 10k / out 3k) | 0m | 16m | 1 | 4 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 0 | 25,888 (in 11k / out 15k) | 97.1% | 16m | 33 (0) |
| qa-engineer | $0.40 | 1 | 13,373 (in 10k / out 3k) | 71.9% | 0m | 4 (0) |
