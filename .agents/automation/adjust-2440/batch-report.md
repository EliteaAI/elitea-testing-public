# Batch cost — adjust-2440

Generated: 2026-10-25T07:44:39.989Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed 38.69s,1 passed 37.91s,1 passed 38.24s runs)
- ⚠️ **OUTCOME DRIFT** (1): ELITEA-2440 receipt=automated declared=verified-non-defect — reconcile report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.46  ·  0.2h active (cases 2m · lead 11m · stages 0m)  ·  2 dispatches
- Tokens: total 3,908,873  ·  **real work 47,104** (in 31,986 / out 15,118)  ·  cache 3.6M read / 304k write  ·  **cache hit rate 91.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 23 turns  ·  35 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.71 (48%)
- Rework (fix rounds — already inside per-case direct): $0.43  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $1.46**
- Avg direct per case (excl. overhead): $0.76
- Direct cost spread: avg $0.76 · median $0.76 · min $0.76 · max $0.76
- Loaded cost spread (direct + even overhead share): avg $1.47 · median $1.47 · min $1.47 · max $1.47
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 13m · median 13m · min 13m · max 13m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2440 | automated | $0.76 | $1.47 | 26,568 (in 21k / out 6k) | 2m | 13m | 2 | 10 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.71 | 0 | 20,536 (in 11k / out 9k) | 96.1% | 11m | 25 (1) |
| test-automation-engineer | $0.43 | 1 | 13,379 (in 10k / out 3k) | 77.7% | 1m | 4 (0) |
| qa-engineer | $0.33 | 1 | 13,189 (in 10k / out 3k) | 78.5% | 1m | 6 (0) |
