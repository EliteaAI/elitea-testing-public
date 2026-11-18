# Batch cost — elitea-4720

Generated: 2026-11-18T15:21:04.079Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-18T15:21:00Z (1 run record(s))
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: $8.73  ·  1.3h active (cases 31m · lead 45m · stages 3m)  ·  13 dispatches
- Tokens: total 18,801,386  ·  **real work 214,703** (in 104,588 / out 110,115)  ·  cache 16.6M read / 2.0M write  ·  **cache hit rate 88.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  146 tool calls (0 err, 100% ok)
- Overhead (lead + triage + gate + report, shown once): $3.24 (37%)
  - by stage: lead $2.05 · triage $0.34 (0m) · gate $0.44 (2m) · report $0.42 (1m)
- **Per delivered case (incl. overhead): $8.73**
- Avg direct per case (excl. overhead): $5.49
- Direct cost spread: avg $5.49 · median $5.49 · min $5.49 · max $5.49
- Loaded cost spread (direct + even overhead share): avg $8.73 · median $8.73 · min $8.73 · max $8.73
- Active-time spread: avg 31m · median 31m · min 31m · max 31m  ·  loaded: avg 79m · median 79m · min 79m · max 79m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4720 | automated | $5.49 | $8.73 | 157,085 (in 60k / out 97k) | 31m | 79m | 8 | 112 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.38 | 7 | 85,212 (in 43k / out 43k) | 92.0% | 20m | 66 (0) |
| qa-engineer | $3.30 | 6 | 104,432 (in 43k / out 61k) | 90.4% | 14m | 60 (0) |
| test-automation-lead | $2.05 | 0 | 25,059 (in 19k / out 6k) | 70.9% | 45m | 20 (0) |
