# Batch cost — adjust-elitea-2455

Generated: 2026-11-13T12:10:38.740Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-12 → 2026-11-14 (scopes)_

_1 session(s) also served other batches — their session-level figures are split evenly; 14 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3/3 pass (34.0s,33.8s,33.9s) DEV, APP_PREFIX=/app runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $25.44  ·  2.7h active (cases 89m · lead 71m · stages 5m)  ·  12.5 dispatches
- Tokens: total 78,793,306  ·  **real work 403,142** (in 137,338 / out 265,804)  ·  cache 75.4M read / 3.0M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 36 turns  ·  366 tool calls (13 err, 96% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $5.38 (21%)
  - by stage: lead $4.32 · triage $0.18 (1m) · gate $0.33 (3m) · report $0.54 (1m)
- Rework (fix rounds — already inside per-case direct): $0.62  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $25.44**
- Avg direct per case (excl. overhead): $20.06
- Direct cost spread: avg $20.06 · median $20.06 · min $20.06 · max $20.06
- Loaded cost spread (direct + even overhead share): avg $25.44 · median $25.44 · min $25.44 · max $25.44
- Active-time spread: avg 89m · median 89m · min 89m · max 89m  ·  loaded: avg 164m · median 164m · min 164m · max 164m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2455 | automated | $20.06 | $25.44 | 334,695 (in 103k / out 231k) | 89m | 164m | 9 | 313 (10) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $19.70 | 8.5 | 320,051 (in 88k / out 232k) | 97.9% | 90m | 306 (11) |
| test-automation-lead | $4.32 | 0 | 39,427 (in 21k / out 18k) | 81.5% | 71m | 35 (2) |
| qa-engineer | $1.41 | 4 | 43,664 (in 28k / out 16k) | 77.8% | 4m | 25 (1) |
