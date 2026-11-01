# Batch cost — adjust-2836

Generated: 2026-11-01T04:28:02.685Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-31 → 2026-11-02 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.36  ·  0.4h active (cases 7m · lead 15m · stages 0m)  ·  3 dispatches
- Tokens: total 6,829,499  ·  **real work 73,539** (in 43,614 / out 29,925)  ·  cache 6.3M read / 450k write  ·  **cache hit rate 92.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 33 turns  ·  50 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.07 (45%)
- Rework (fix rounds — already inside per-case direct): $0.41  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $1.18**
- Avg direct per case (excl. overhead): $1.29
- Direct cost spread: avg $1.29 · median $1.29 · min $1.29 · max $1.29
- Loaded cost spread (direct + even overhead share): avg $1.18 · median $1.18 · min $0.53 · max $1.82
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 12m · median 12m · min 8m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2005 | automated | $1.29 | $1.82 | 41,133 (in 31k / out 10k) | 7m | 15m | 3 | 17 (1) | 1 | 0 |
| ELITEA-2041 | automated | n/a | $0.53 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.07 | 0 | 32,406 (in 12k / out 20k) | 97.0% | 15m | 33 (0) |
| qa-engineer | $0.88 | 2 | 28,643 (in 21k / out 8k) | 85.6% | 6m | 13 (1) |
| test-automation-engineer | $0.41 | 1 | 12,490 (in 10k / out 2k) | 81.3% | 1m | 4 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2041
