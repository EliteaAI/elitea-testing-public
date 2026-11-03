# Batch cost — adjust-2866

Generated: 2026-11-03T06:11:56.032Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-02 → 2026-11-04 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-03T06:11:54Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $3.00  ·  0.8h active (cases 14m · lead 31m · stages 0m)  ·  2 dispatches
- Tokens: total 6,223,341  ·  **real work 54,381** (in 31,835 / out 22,546)  ·  cache 5.4M read / 760k write  ·  **cache hit rate 87.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 29 turns  ·  46 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.41 (47%)
- Rework (fix rounds — already inside per-case direct): $1.25  ·  1 dispatch(es)  ·  13m
- **Per delivered case (incl. overhead): $1.50**
- Avg direct per case (excl. overhead): $0.79
- Direct cost spread: avg $0.79 · median $0.79 · min $0.79 · max $0.79
- Loaded cost spread (direct + even overhead share): avg $1.50 · median $1.50 · min $1.50 · max $1.50
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 23m · median 23m · min 23m · max 23m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1891 | automated | $0.79 | $1.50 | 15,335 (in 10k / out 5k) | 7m | 23m | 1 | 8 (0) | 0.5 | 0 |
| ELITEA-1892 | automated | $0.79 | $1.50 | 15,335 (in 10k / out 5k) | 7m | 23m | 1 | 8 (0) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.41 | 0 | 23,712 (in 11k / out 13k) | 92.6% | 31m | 30 (0) |
| test-automation-engineer | $1.25 | 1 | 17,301 (in 10k / out 7k) | 73.4% | 13m | 11 (0) |
| qa-engineer | $0.34 | 1 | 13,368 (in 10k / out 3k) | 83.0% | 1m | 5 (0) |
