# Batch cost — adjust-code-node-timeline-label

Generated: 2026-11-12T15:15:14.633Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-10 → 2026-11-13 (scopes)_

## What happened

- Cases: 4  ·  **delivered: 4**  ·  automated 4
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $3.47  ·  0.7h active (cases 15m · lead 28m · stages 0m)  ·  4 dispatches
- Tokens: total 8,731,577  ·  **real work 93,461** (in 53,956 / out 39,505)  ·  cache 7.9M read / 734k write  ·  **cache hit rate 90.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 34 turns  ·  69 tool calls (4 err, 94% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $2.00 (58%)
  - by stage: lead $1.69 · other $0.31 (0m)
- Rework (fix rounds — already inside per-case direct): $0.34  ·  1 dispatch(es)  ·  2m
- **Per delivered case (incl. overhead): $0.87**
- Avg direct per case (excl. overhead): $0.74
- Direct cost spread: avg $0.74 · median $0.74 · min $0.35 · max $1.12
- Loaded cost spread (direct + even overhead share): avg $0.87 · median $0.68 · min $0.50 · max $1.62
- Active-time spread: avg 8m · median 8m · min 6m · max 9m  ·  loaded: avg 11m · median 10m · min 7m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2448 | automated | $1.12 | $1.62 | 37,004 (in 26k / out 11k) | 9m | 16m | 2.5 | 18 (0) | 1 | 0 |
| ELITEA-2449 | automated | $0.35 | $0.85 | 10,569 (in 5k / out 5k) | 6m | 13m | 0.5 | 10 (0) | 0 | 0 |
| ELITEA-2446 | automated | n/a | $0.50 | 0 (incl. cache) | 0m | 7m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2447 | automated | n/a | $0.50 | 0 (incl. cache) | 0m | 7m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.69 | 0 | 32,816 (in 12k / out 21k) | 92.6% | 28m | 38 (4) |
| test-automation-engineer | $1.05 | 2 | 33,700 (in 21k / out 13k) | 93.3% | 14m | 23 (0) |
| qa-engineer | $0.74 | 2 | 26,945 (in 21k / out 6k) | 71.6% | 1m | 8 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2446, ELITEA-2447
