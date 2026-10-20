# Batch cost — chat-project-context-3368

Generated: 2026-10-20T16:33:08.249Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- ⚠️ **OUTCOME DRIFT** (1): ELITEA-3315 receipt=automated declared=blocked — reconcile report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $5.92  ·  1.2h active (cases 6m · lead 59m · stages 5m)  ·  6 dispatches
- Tokens: total 12,610,429  ·  **real work 214,007** (in 163,195 / out 50,812)  ·  cache 11.0M read / 1.4M write  ·  **cache hit rate 87.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 53 turns  ·  101 tool calls (2 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $3.74 (63%)
  - by stage: lead $2.77 · other $0.97 (5m)
- Rework (fix rounds — already inside per-case direct): $0.60  ·  1 dispatch(es)  ·  2m
- **Per delivered case (incl. overhead): $2.96**
- Avg direct per case (excl. overhead): $1.10
- Direct cost spread: avg $1.10 · median $1.10 · min $0.58 · max $1.61
- Loaded cost spread (direct + even overhead share): avg $1.98 · median $1.83 · min $1.25 · max $2.86
- Active-time spread: avg 3m · median 3m · min 2m · max 4m  ·  loaded: avg 23m · median 23m · min 21m · max 25m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3368 | automated | $1.61 | $2.86 | 90,138 (in 80k / out 10k) | 4m | 25m | 3 | 23 (0) | 1 | 0 |
| ELITEA-3315 | automated | $0.58 | $1.83 | 21,718 (in 11k / out 11k) | 2m | 23m | 1 | 11 (0) | 0 | 0 |
| ELITEA-3369 | blocked | n/a | $1.25 | 0 (incl. cache) | 0m | 21m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $2.77 | 0 | 38,958 (in 14k / out 25k) | 90.4% | 59m | 52 (2) |
| test-automation-engineer | $2.09 | 4 | 124,515 (in 113k / out 11k) | 83.3% | 8m | 32 (0) |
| qa-engineer | $1.07 | 2 | 50,534 (in 36k / out 15k) | 86.6% | 3m | 17 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-3369
