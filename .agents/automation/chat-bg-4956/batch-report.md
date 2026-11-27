# Batch cost — chat-bg-4956

Generated: 2026-11-27T12:48:48.435Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 15  ·  fix rounds: 0

## What it cost

- Total: $6.02  ·  1.1h active (cases 19m · lead 36m · stages 14m)  ·  7 dispatches
- Tokens: total 11,942,021  ·  **real work 133,826** (in 76,615 / out 57,211)  ·  cache 10.1M read / 1.7M write  ·  **cache hit rate 85.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  98 tool calls (1 err, 99% ok)
- Overhead (lead + triage + gate + report, shown once): $3.55 (59%)
  - by stage: lead $1.98 · triage $0.30 (0m) · gate $0.89 (14m) · report $0.37 (0m)
- **Per delivered case (incl. overhead): $6.02**
- Avg direct per case (excl. overhead): $2.47
- Direct cost spread: avg $2.47 · median $2.47 · min $2.47 · max $2.47
- Loaded cost spread (direct + even overhead share): avg $6.02 · median $6.02 · min $6.02 · max $6.02
- Active-time spread: avg 19m · median 19m · min 19m · max 19m  ·  loaded: avg 69m · median 69m · min 69m · max 69m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4956 | automated | $2.47 | $6.02 | 75,185 (in 35k / out 40k) | 19m | 69m | 4 | 56 (0) | 0 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.41 | 4 | 63,435 (in 35k / out 29k) | 87.6% | 21m | 44 (1) |
| test-automation-lead | $1.98 | 0 | 21,948 (in 15k / out 7k) | 69.4% | 36m | 19 (0) |
| qa-engineer | $1.63 | 3 | 48,443 (in 27k / out 22k) | 90.0% | 12m | 35 (0) |
