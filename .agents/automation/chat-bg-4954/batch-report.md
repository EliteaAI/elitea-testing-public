# Batch cost — chat-bg-4954

Generated: 2026-11-27T19:51:25.854Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 13  ·  fix rounds: 1

## What it cost

- Total: $22.53  ·  5.2h active (cases 141m · lead 167m · stages 5m)  ·  16 dispatches
- Tokens: total 53,484,344  ·  **real work 382,591** (in 158,720 / out 223,871)  ·  cache 47.0M read / 6.1M write  ·  **cache hit rate 88.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 84 turns  ·  372 tool calls (11 err, 97% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.05 (53%)
  - by stage: lead $10.62 · triage $0.61 (0m) · gate $0.42 (4m) · report $0.40 (1m)
- Rework (fix rounds — already inside per-case direct): $0.36  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $22.53**
- Avg direct per case (excl. overhead): $10.48
- Direct cost spread: avg $10.48 · median $10.48 · min $10.48 · max $10.48
- Loaded cost spread (direct + even overhead share): avg $22.53 · median $22.53 · min $22.53 · max $22.53
- Active-time spread: avg 141m · median 141m · min 141m · max 141m  ·  loaded: avg 313m · median 313m · min 313m · max 313m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4954 | automated | $10.48 | $22.53 | 287,415 (in 107k / out 180k) | 141m | 313m | 12 | 273 (4) | 1 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $10.62 | 0 | 51,511 (in 16k / out 35k) | 71.0% | 167m | 83 (7) |
| test-automation-engineer | $9.24 | 11 | 252,636 (in 98k / out 155k) | 94.5% | 123m | 233 (4) |
| qa-engineer | $2.67 | 5 | 78,444 (in 44k / out 34k) | 90.3% | 23m | 56 (0) |
