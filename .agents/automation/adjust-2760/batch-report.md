# Batch cost — adjust-2760

Generated: 2026-10-30T08:04:09.558Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 1  ·  merged-sanctioned-red 1  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: $2.53  ·  0.6h active (cases 3m · lead 30m · stages 0m)  ·  2 dispatches
- Tokens: total 6,799,712  ·  **real work 60,961** (in 32,111 / out 28,850)  ·  cache 6.2M read / 532k write  ·  **cache hit rate 91.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 36 turns  ·  52 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.67 (66%)
- **Per delivered case (incl. overhead): $1.27**
- Avg direct per case (excl. overhead): $0.29
- Direct cost spread: avg $0.29 · median $0.29 · min $0.29 · max $0.29
- Loaded cost spread (direct + even overhead share): avg $0.85 · median $0.85 · min $0.85 · max $0.85
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2019 | automated | $0.29 | $0.85 | 9,472 (in 7k / out 3k) | 1m | 11m | 0.67 | 4 (0) | 0 | 0 |
| ELITEA-2045 | merged-sanctioned-red | $0.29 | $0.85 | 9,472 (in 7k / out 3k) | 1m | 11m | 0.67 | 4 (0) | 0 | 0 |
| ELITEA-2057 | blocked | $0.29 | $0.85 | 9,472 (in 7k / out 3k) | 1m | 11m | 0.67 | 4 (0) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.67 | 0 | 32,544 (in 11k / out 21k) | 93.8% | 30m | 39 (0) |
| test-automation-engineer | $0.50 | 1 | 14,422 (in 10k / out 4k) | 87.6% | 2m | 9 (0) |
| qa-engineer | $0.36 | 1 | 13,995 (in 11k / out 3k) | 77.0% | 1m | 4 (0) |
