# Batch cost — attachments-switch-4791

Generated: 2026-11-23T19:43:46.839Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-22 → 2026-11-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-23T19:40:00Z (1 run record(s))
- Findings reported: 14  ·  fix rounds: 0

## What it cost

- Total: $7.20  ·  1.3h active (cases 29m · lead 45m · stages 6m)  ·  13 dispatches
- Tokens: total 18,184,484  ·  **real work 183,102** (in 105,090 / out 78,012)  ·  cache 16.2M read / 1.8M write  ·  **cache hit rate 89.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 26 turns  ·  149 tool calls (7 err, 95% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $3.10 (43%)
  - by stage: lead $1.90 · triage $0.31 (0m) · gate $0.53 (5m) · report $0.37 (1m)
- **Per delivered case (incl. overhead): $7.20**
- Avg direct per case (excl. overhead): $4.10
- Direct cost spread: avg $4.10 · median $4.10 · min $4.10 · max $4.10
- Loaded cost spread (direct + even overhead share): avg $7.20 · median $7.20 · min $7.20 · max $7.20
- Active-time spread: avg 29m · median 29m · min 29m · max 29m  ·  loaded: avg 80m · median 80m · min 80m · max 80m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4791 | automated | $4.10 | $7.20 | 121,002 (in 60k / out 61k) | 29m | 80m | 8 | 101 (4) | 0 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $2.82 | 6 | 86,366 (in 43k / out 43k) | 91.8% | 19m | 66 (3) |
| test-automation-engineer | $2.48 | 7 | 69,169 (in 43k / out 26k) | 90.4% | 16m | 56 (2) |
| test-automation-lead | $1.90 | 0 | 27,567 (in 19k / out 9k) | 80.9% | 45m | 27 (2) |
