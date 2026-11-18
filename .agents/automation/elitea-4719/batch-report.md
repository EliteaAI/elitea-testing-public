# Batch cost — elitea-4719

Generated: 2026-11-18T14:26:32.961Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 3  ·  fix rounds: 1

## What it cost

- Total: $4.50  ·  0.7h active (cases 18m · lead 21m · stages 0m)  ·  8 dispatches
- Tokens: total 10,551,173  ·  **real work 115,389** (in 58,389 / out 57,000)  ·  cache 9.5M read / 973k write  ·  **cache hit rate 90.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 15 turns  ·  86 tool calls (2 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $1.08 (24%)
  - by stage: lead $1.08 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.62  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $4.50**
- Avg direct per case (excl. overhead): $3.42
- Direct cost spread: avg $3.42 · median $3.42 · min $3.42 · max $3.42
- Loaded cost spread (direct + even overhead share): avg $4.50 · median $4.50 · min $4.50 · max $4.50
- Active-time spread: avg 18m · median 18m · min 18m · max 18m  ·  loaded: avg 39m · median 39m · min 39m · max 39m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4719 | automated | $3.42 | $4.50 | 93,875 (in 43k / out 51k) | 18m | 39m | 6 | 71 (1) | 1 | 3 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $1.99 | 4 | 54,822 (in 26k / out 29k) | 90.2% | 8m | 38 (0) |
| test-automation-engineer | $1.43 | 4 | 39,053 (in 17k / out 22k) | 93.6% | 10m | 33 (1) |
| test-automation-lead | $1.08 | 0 | 21,514 (in 15k / out 6k) | 80.9% | 21m | 15 (1) |
