# Batch cost — chat-regenerate-2187

Generated: 2026-10-21T00:51:46.008Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-20 → 2026-10-22 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 12  ·  fix rounds: 2

## What it cost

- Total: $8.20  ·  1.5h active (cases 31m · lead 50m · stages 8m)  ·  16 dispatches
- Tokens: total 13,785,188  ·  **real work 187,105** (in 129,951 / out 57,154)  ·  cache 11.4M read / 2.2M write  ·  **cache hit rate 83.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  131 tool calls (2 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $3.28 (40%)
  - by stage: lead $2.01 · triage $0.32 (0m) · gate $0.52 (7m) · report $0.43 (1m)
- Rework (fix rounds — already inside per-case direct): $1.00  ·  2 dispatch(es)  ·  11m
- **Per delivered case (incl. overhead): $8.20**
- Avg direct per case (excl. overhead): $4.92
- Direct cost spread: avg $4.92 · median $4.92 · min $4.92 · max $4.92
- Loaded cost spread (direct + even overhead share): avg $8.20 · median $8.20 · min $8.20 · max $8.20
- Active-time spread: avg 31m · median 31m · min 31m · max 31m  ·  loaded: avg 89m · median 89m · min 89m · max 89m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2187 | automated | $4.92 | $8.20 | 124,175 (in 85k / out 39k) | 31m | 89m | 11 | 93 (1) | 2 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.81 | 9 | 90,513 (in 59k / out 31k) | 88.7% | 36m | 78 (2) |
| qa-engineer | $2.38 | 7 | 69,701 (in 52k / out 18k) | 77.3% | 3m | 33 (0) |
| test-automation-lead | $2.01 | 0 | 26,891 (in 19k / out 8k) | 68.8% | 50m | 20 (0) |
