# Batch cost — chat-regenerate-2185

Generated: 2026-10-20T23:40:31.985Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 8  ·  fix rounds: 1

## What it cost

- Total: $8.30  ·  2.1h active (cases 45m · lead 68m · stages 14m)  ·  14 dispatches
- Tokens: total 13,498,087  ·  **real work 170,752** (in 114,445 / out 56,307)  ·  cache 11.1M read / 2.3M write  ·  **cache hit rate 82.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  123 tool calls (6 err, 95% ok)
- Overhead (lead + triage + gate + report, shown once): $4.09 (49%)
  - by stage: lead $2.58 · triage $0.32 (0m) · gate $0.78 (13m) · report $0.40 (1m)
- Rework (fix rounds — already inside per-case direct): $0.48  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $8.30**
- Avg direct per case (excl. overhead): $4.20
- Direct cost spread: avg $4.20 · median $4.20 · min $4.20 · max $4.20
- Loaded cost spread (direct + even overhead share): avg $8.29 · median $8.29 · min $8.29 · max $8.29
- Active-time spread: avg 45m · median 45m · min 45m · max 45m  ·  loaded: avg 127m · median 127m · min 127m · max 127m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2185 | automated | $4.20 | $8.29 | 111,207 (in 71k / out 41k) | 45m | 127m | 9 | 83 (4) | 1 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.11 | 8 | 75,337 (in 51k / out 25k) | 85.3% | 34m | 51 (3) |
| qa-engineer | $2.61 | 6 | 69,650 (in 45k / out 24k) | 87.3% | 25m | 49 (2) |
| test-automation-lead | $2.58 | 0 | 25,765 (in 18k / out 7k) | 64.4% | 68m | 23 (1) |
