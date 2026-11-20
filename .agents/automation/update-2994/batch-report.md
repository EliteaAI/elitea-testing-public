# Batch cost — update-2994

Generated: 2026-11-20T11:20:35.333Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 1

## What it cost

- Total: $4.23  ·  0.8h active (cases 15m · lead 31m · stages 0m)  ·  8 dispatches
- Tokens: total 7,947,220  ·  **real work 90,263** (in 57,597 / out 32,666)  ·  cache 6.8M read / 1.1M write  ·  **cache hit rate 85.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 18 turns  ·  70 tool calls (4 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.63 (39%)
  - by stage: lead $1.63 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.44  ·  1 dispatch(es)  ·  6m
- **Per delivered case (incl. overhead): $4.23**
- Avg direct per case (excl. overhead): $2.60
- Direct cost spread: avg $2.60 · median $2.60 · min $2.60 · max $2.60
- Loaded cost spread (direct + even overhead share): avg $4.23 · median $4.23 · min $4.23 · max $4.23
- Active-time spread: avg 15m · median 15m · min 15m · max 15m  ·  loaded: avg 46m · median 46m · min 46m · max 46m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4755 | automated | $2.60 | $4.23 | 69,590 (in 43k / out 27k) | 15m | 46m | 6 | 51 (2) | 1 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.63 | 0 | 20,673 (in 15k / out 6k) | 76.8% | 31m | 19 (2) |
| qa-engineer | $1.60 | 4 | 42,153 (in 26k / out 16k) | 88.0% | 8m | 30 (1) |
| test-automation-engineer | $1.00 | 4 | 27,437 (in 17k / out 10k) | 90.1% | 7m | 21 (1) |
