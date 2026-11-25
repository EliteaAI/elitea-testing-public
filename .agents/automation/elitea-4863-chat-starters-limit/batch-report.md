# Batch cost — elitea-4863-chat-starters-limit

Generated: 2026-11-25T11:48:42.196Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-24 → 2026-11-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-25T11:48:40Z (1 run record(s))
- Findings reported: 15  ·  fix rounds: 0

## What it cost

- Total: $6.96  ·  1.2h active (cases 14m · lead 41m · stages 17m)  ·  13 dispatches
- Tokens: total 14,489,487  ·  **real work 164,222** (in 106,531 / out 57,691)  ·  cache 12.4M read / 2.0M write  ·  **cache hit rate 85.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  126 tool calls (7 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $3.38 (49%)
  - by stage: lead $1.80 · triage $0.30 (0m) · gate $0.62 (4m) · report $0.66 (13m)
- **Per delivered case (incl. overhead): $6.96**
- Avg direct per case (excl. overhead): $3.58
- Direct cost spread: avg $3.58 · median $3.58 · min $3.58 · max $3.58
- Loaded cost spread (direct + even overhead share): avg $6.96 · median $6.96 · min $6.96 · max $6.96
- Active-time spread: avg 14m · median 14m · min 14m · max 14m  ·  loaded: avg 72m · median 72m · min 72m · max 72m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4863 | automated | $3.58 | $6.96 | 102,448 (in 62k / out 41k) | 14m | 72m | 8 | 80 (2) | 0 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.98 | 7 | 72,797 (in 44k / out 29k) | 90.1% | 23m | 65 (2) |
| qa-engineer | $2.18 | 6 | 67,028 (in 44k / out 23k) | 84.3% | 8m | 41 (3) |
| test-automation-lead | $1.80 | 0 | 24,397 (in 19k / out 6k) | 72.5% | 41m | 20 (2) |
