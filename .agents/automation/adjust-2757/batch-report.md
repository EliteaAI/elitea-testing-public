# Batch cost — adjust-2757

Generated: 2026-10-30T06:06:01.596Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.45  ·  0.4h active (cases 1m · lead 23m · stages 0m)  ·  2 dispatches
- Tokens: total 9,499,335  ·  **real work 64,886** (in 32,287 / out 32,599)  ·  cache 9.1M read / 371k write  ·  **cache hit rate 95.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 56 turns  ·  68 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.63 (66%)
- **Per delivered case (incl. overhead): $2.45**
- Avg direct per case (excl. overhead): $0.82
- Direct cost spread: avg $0.82 · median $0.82 · min $0.82 · max $0.82
- Loaded cost spread (direct + even overhead share): avg $2.45 · median $2.45 · min $2.45 · max $2.45
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 24m · median 24m · min 24m · max 24m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2059 | automated | $0.82 | $2.45 | 27,992 (in 21k / out 7k) | 1m | 24m | 2 | 11 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.63 | 0 | 36,894 (in 11k / out 26k) | 98.1% | 23m | 57 (0) |
| qa-engineer | $0.82 | 2 | 27,992 (in 21k / out 7k) | 77.5% | 1m | 11 (0) |
