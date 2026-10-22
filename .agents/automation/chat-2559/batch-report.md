# Batch cost — chat-2559

Generated: 2026-10-22T21:43:07.521Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-21 → 2026-10-23 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 1**  ·  automated 1  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 18  ·  fix rounds: 0

## What it cost

- Total: $11.33  ·  1.8h active (cases 22m · lead 58m · stages 31m)  ·  19 dispatches
- Tokens: total 23,472,173  ·  **real work 256,049** (in 159,703 / out 96,346)  ·  cache 20.4M read / 2.8M write  ·  **cache hit rate 87.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 28 turns  ·  196 tool calls (7 err, 96% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $6.72 (59%)
  - by stage: lead $2.92 · triage $0.35 (0m) · gate $0.44 (2m) · report $0.46 (1m) · other $2.55 (28m)
- **Per delivered case (incl. overhead): $11.33**
- Avg direct per case (excl. overhead): $2.31
- Direct cost spread: avg $2.31 · median $2.31 · min $0.82 · max $3.79
- Loaded cost spread (direct + even overhead share): avg $5.67 · median $5.67 · min $4.18 · max $7.15
- Active-time spread: avg 11m · median 11m · min 6m · max 16m  ·  loaded: avg 56m · median 56m · min 51m · max 61m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3775 | automated | $3.79 | $7.15 | 102,166 (in 60k / out 43k) | 16m | 61m | 8 | 78 (2) | 0 | 14 |
| ELITEA-3786 | blocked | $0.82 | $4.18 | 21,746 (in 9k / out 13k) | 6m | 51m | 1 | 20 (1) | 0 | 4 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $5.65 | 13 | 143,760 (in 93k / out 51k) | 89.3% | 39m | 111 (3) |
| test-automation-lead | $2.92 | 0 | 35,569 (in 24k / out 12k) | 74.9% | 58m | 30 (2) |
| qa-engineer | $2.75 | 6 | 76,720 (in 43k / out 34k) | 90.5% | 13m | 55 (2) |
