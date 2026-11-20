# Batch cost — pipe-copy-4756

Generated: 2026-11-20T12:00:32.779Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-20T11:59:00Z (3 run record(s))
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: $7.33  ·  1.1h active (cases 25m · lead 38m · stages 3m)  ·  13 dispatches
- Tokens: total 12,073,606  ·  **real work 154,443** (in 103,720 / out 50,723)  ·  cache 9.9M read / 2.0M write  ·  **cache hit rate 82.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  99 tool calls (3 err, 97% ok)  ·  skills: test-automation-workflow, workflow-authoring
- Overhead (lead + triage + gate + report, shown once): $3.30 (45%)
  - by stage: lead $2.04 · triage $0.35 (0m) · gate $0.51 (3m) · report $0.40 (0m)
- **Per delivered case (incl. overhead): $7.33**
- Avg direct per case (excl. overhead): $4.03
- Direct cost spread: avg $4.03 · median $4.03 · min $4.03 · max $4.03
- Loaded cost spread (direct + even overhead share): avg $7.33 · median $7.33 · min $7.33 · max $7.33
- Active-time spread: avg 25m · median 25m · min 25m · max 25m  ·  loaded: avg 66m · median 66m · min 66m · max 66m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4756 | automated | $4.03 | $7.33 | 95,440 (in 60k / out 35k) | 25m | 66m | 8 | 59 (1) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.71 | 7 | 68,430 (in 43k / out 26k) | 88.9% | 12m | 48 (2) |
| qa-engineer | $2.58 | 6 | 60,673 (in 43k / out 17k) | 75.8% | 16m | 28 (0) |
| test-automation-lead | $2.04 | 0 | 25,340 (in 18k / out 7k) | 77.3% | 38m | 23 (1) |
