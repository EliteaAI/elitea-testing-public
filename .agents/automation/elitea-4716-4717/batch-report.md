# Batch cost — elitea-4716-4717

Generated: 2026-11-18T12:49:20.961Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (2 passed 61.9s,2 passed 45.2s,2 passed 44.2s runs)
- Gate record (script-authored): green at 2026-11-18T12:49:19Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 2

## What it cost

- Total: $8.93  ·  1.9h active (cases 52m · lead 63m · stages 0m)  ·  9 dispatches
- Tokens: total 23,857,460  ·  **real work 225,942** (in 83,158 / out 142,784)  ·  cache 21.9M read / 1.7M write  ·  **cache hit rate 92.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 32 turns  ·  175 tool calls (3 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $2.68 (30%)
  - by stage: lead $2.68 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $1.29  ·  2 dispatch(es)  ·  16m
- **Per delivered case (incl. overhead): $4.46**
- Avg direct per case (excl. overhead): $3.12
- Direct cost spread: avg $3.12 · median $3.12 · min $3.12 · max $3.12
- Loaded cost spread (direct + even overhead share): avg $4.46 · median $4.46 · min $4.46 · max $4.46
- Active-time spread: avg 26m · median 26m · min 26m · max 26m  ·  loaded: avg 58m · median 58m · min 58m · max 58m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4716 | automated | $3.12 | $4.46 | 97,046 (in 33k / out 64k) | 26m | 58m | 3.5 | 71 (1) | 1 | 0 |
| ELITEA-4717 | automated | $3.12 | $4.46 | 97,046 (in 33k / out 64k) | 26m | 58m | 3.5 | 71 (1) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.14 | 4 | 92,271 (in 28k / out 65k) | 95.9% | 31m | 73 (0) |
| qa-engineer | $3.11 | 5 | 101,820 (in 38k / out 63k) | 93.6% | 21m | 69 (1) |
| test-automation-lead | $2.68 | 0 | 31,851 (in 17k / out 15k) | 79.6% | 63m | 33 (2) |
