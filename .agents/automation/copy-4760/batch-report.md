# Batch cost — copy-4760

Generated: 2026-11-20T14:07:43.955Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: $5.26  ·  0.5h active (cases 8m · lead 18m · stages 4m)  ·  12 dispatches
- Tokens: total 9,173,673  ·  **real work 133,792** (in 94,702 / out 39,090)  ·  cache 7.7M read / 1.4M write  ·  **cache hit rate 83.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 17 turns  ·  84 tool calls (5 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $2.49 (47%)
  - by stage: lead $1.19 · triage $0.33 (0m) · gate $0.55 (3m) · report $0.41 (1m)
- **Per delivered case (incl. overhead): $5.26**
- Avg direct per case (excl. overhead): $2.77
- Direct cost spread: avg $2.77 · median $2.77 · min $2.77 · max $2.77
- Loaded cost spread (direct + even overhead share): avg $5.26 · median $5.26 · min $5.26 · max $5.26
- Active-time spread: avg 8m · median 8m · min 8m · max 8m  ·  loaded: avg 30m · median 30m · min 30m · max 30m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4760 | automated | $2.77 | $5.26 | 74,962 (in 51k / out 23k) | 8m | 30m | 7 | 46 (3) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.41 | 7 | 62,334 (in 43k / out 20k) | 86.5% | 10m | 42 (4) |
| qa-engineer | $1.66 | 5 | 48,092 (in 35k / out 13k) | 79.4% | 2m | 24 (1) |
| test-automation-lead | $1.19 | 0 | 23,366 (in 18k / out 6k) | 83.0% | 18m | 18 (0) |
