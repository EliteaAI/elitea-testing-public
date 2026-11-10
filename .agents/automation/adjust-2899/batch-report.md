# Batch cost — adjust-2899

Generated: 2026-11-10T13:56:16.222Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-09 → 2026-11-11 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3x per-spec processes over 15 specs (45 invocations), all passed on DEV; combined single-process runs were flaky from DEV 429 rate limits / intermittent icon 404 and were not used runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $10.31  ·  3.0h active (cases 30m · lead 138m · stages 11m)  ·  4 dispatches
- Tokens: total 17,451,148  ·  **real work 118,311** (in 54,429 / out 63,882)  ·  cache 14.5M read / 2.9M write  ·  **cache hit rate 83.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  126 tool calls (4 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $8.18 (79%)
  - by stage: lead $7.12 · triage $0.65 (5m) · other $0.41 (6m)
- **Per delivered case (incl. overhead): $5.16**
- Avg direct per case (excl. overhead): $2.14
- Direct cost spread: avg $2.14 · median $2.14 · min $2.14 · max $2.14
- Loaded cost spread (direct + even overhead share): avg $5.16 · median $5.16 · min $4.09 · max $6.23
- Active-time spread: avg 30m · median 30m · min 30m · max 30m  ·  loaded: avg 90m · median 90m · min 75m · max 105m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2352 | automated | $2.14 | $6.23 | 46,777 (in 22k / out 25k) | 30m | 105m | 2 | 48 (2) | 0 | 0 |
| ELITEA-2353 | automated | n/a | $4.09 | 0 (incl. cache) | 0m | 75m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $7.12 | 0 | 39,892 (in 12k / out 28k) | 73.1% | 138m | 57 (2) |
| test-automation-engineer | $2.73 | 3 | 63,000 (in 32k / out 31k) | 92.8% | 40m | 58 (2) |
| qa-engineer | $0.47 | 1 | 15,419 (in 10k / out 5k) | 89.9% | 1m | 11 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2353
