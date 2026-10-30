# Batch cost — chat-export-3784

Generated: 2026-10-20T19:54:28.784Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-20T19:54:27Z (1 run record(s))
- Findings reported: 14  ·  fix rounds: 0

## What it cost

- Total: $4.13  ·  0.5h active (cases 12m · lead 16m · stages 3m)  ·  6 dispatches
- Tokens: total 7,788,212  ·  **real work 104,491** (in 67,530 / out 36,961)  ·  cache 6.7M read / 1.0M write  ·  **cache hit rate 85.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 17 turns  ·  69 tool calls (3 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $1.93 (47%)
  - by stage: lead $1.07 · gate $0.44 (2m) · report $0.43 (1m)
- **Per delivered case (incl. overhead): $4.13**
- Avg direct per case (excl. overhead): $2.20
- Direct cost spread: avg $2.20 · median $2.20 · min $2.20 · max $2.20
- Loaded cost spread (direct + even overhead share): avg $4.13 · median $4.13 · min $4.13 · max $4.13
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 31m · median 31m · min 31m · max 31m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3784 | automated | $2.20 | $4.13 | 59,675 (in 36k / out 23k) | 12m | 31m | 4 | 39 (1) | 0 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.93 | 4 | 53,619 (in 36k / out 18k) | 85.9% | 11m | 31 (2) |
| qa-engineer | $1.13 | 2 | 30,592 (in 17k / out 13k) | 87.9% | 4m | 21 (1) |
| test-automation-lead | $1.07 | 0 | 20,280 (in 14k / out 6k) | 83.4% | 16m | 17 (0) |
