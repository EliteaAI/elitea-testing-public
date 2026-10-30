# Batch cost — chat-json-export-3762

Generated: 2026-10-22T05:46:43.609Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-20 → 2026-10-23 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (6 run record(s))
- Findings reported: 14  ·  fix rounds: 0

## What it cost

- Total: $5.86  ·  0.6h active (cases 11m · lead 21m · stages 6m)  ·  7 dispatches
- Tokens: total 9,243,205  ·  **real work 114,941** (in 74,526 / out 40,415)  ·  cache 7.5M read / 1.6M write  ·  **cache hit rate 81.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  80 tool calls (3 err, 96% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $3.56 (61%)
  - by stage: lead $2.20 · triage $0.33 (0m) · gate $0.61 (5m) · report $0.42 (1m)
- **Per delivered case (incl. overhead): $5.86**
- Avg direct per case (excl. overhead): $2.30
- Direct cost spread: avg $2.30 · median $2.30 · min $2.30 · max $2.30
- Loaded cost spread (direct + even overhead share): avg $5.86 · median $5.86 · min $5.86 · max $5.86
- Active-time spread: avg 11m · median 11m · min 11m · max 11m  ·  loaded: avg 38m · median 38m · min 38m · max 38m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3762 | automated | $2.30 | $5.86 | 54,015 (in 34k / out 20k) | 11m | 38m | 4 | 34 (0) | 0 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.29 | 4 | 52,023 (in 34k / out 18k) | 84.7% | 14m | 37 (2) |
| test-automation-lead | $2.20 | 0 | 24,566 (in 15k / out 10k) | 77.4% | 21m | 22 (1) |
| qa-engineer | $1.37 | 3 | 38,352 (in 26k / out 13k) | 81.9% | 3m | 21 (0) |
