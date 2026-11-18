# Batch cost — pipelines-router-node-2033

Generated: 2026-11-18T16:56:26.609Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at 2026-11-18T17:00:00Z (1 run record(s))
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: $3.50  ·  0.6h active (cases 12m · lead 21m · stages 0m)  ·  6 dispatches
- Tokens: total 8,041,790  ·  **real work 76,693** (in 40,371 / out 36,322)  ·  cache 7.2M read / 803k write  ·  **cache hit rate 89.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 23 turns  ·  67 tool calls (5 err, 93% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.43 (41%)
  - by stage: lead $1.43 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $3.50**
- Avg direct per case (excl. overhead): $2.07
- Direct cost spread: avg $2.07 · median $2.07 · min $2.07 · max $2.07
- Loaded cost spread (direct + even overhead share): avg $3.50 · median $3.50 · min $3.50 · max $3.50
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 33m · median 33m · min 33m · max 33m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2033 | automated | $2.07 | $3.50 | 52,257 (in 26k / out 26k) | 12m | 33m | 4 | 42 (3) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.43 | 0 | 24,436 (in 15k / out 10k) | 86.1% | 21m | 25 (2) |
| qa-engineer | $1.37 | 3 | 35,401 (in 17k / out 18k) | 90.9% | 4m | 27 (2) |
| test-automation-engineer | $0.70 | 3 | 16,856 (in 9k / out 8k) | 91.9% | 8m | 15 (1) |
