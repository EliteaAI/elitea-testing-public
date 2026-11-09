# Batch cost — adjust-2897

Generated: 2026-11-09T13:56:52.073Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-08 → 2026-11-10 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3x6 passed on DEV, reruns 0 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $3.27  ·  0.9h active (cases 23m · lead 32m · stages 0m)  ·  2 dispatches
- Tokens: total 9,156,200  ·  **real work 66,663** (in 31,779 / out 34,884)  ·  cache 8.4M read / 679k write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  68 tool calls (3 err, 96% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.11 (34%)
- **Per delivered case (incl. overhead): $1.63**
- Avg direct per case (excl. overhead): $1.08
- Direct cost spread: avg $1.08 · median $1.08 · min $0.90 · max $1.26
- Loaded cost spread (direct + even overhead share): avg $1.64 · median $1.64 · min $1.46 · max $1.82
- Active-time spread: avg 12m · median 12m · min 11m · max 12m  ·  loaded: avg 28m · median 28m · min 27m · max 28m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2440 | automated | $0.90 | $1.46 | 16,626 (in 5k / out 11k) | 11m | 27m | 0.5 | 21 (1) | 0 | 0 |
| ELITEA-2442 | automated | $1.26 | $1.82 | 30,828 (in 16k / out 15k) | 12m | 28m | 1.5 | 26 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.80 | 1 | 33,252 (in 10k / out 23k) | 94.6% | 21m | 42 (2) |
| test-automation-lead | $1.11 | 0 | 19,209 (in 11k / out 8k) | 88.4% | 32m | 21 (1) |
| qa-engineer | $0.36 | 1 | 14,202 (in 10k / out 4k) | 82.7% | 1m | 5 (0) |
