# Batch cost — elitea-4714

Generated: 2026-11-18T10:55:28.410Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (passed 24.61s,passed 23.73s,passed 24.84s runs)
- Gate record (script-authored): green at 2026-11-18T10:55:27Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 4

## What it cost

- Total: $10.35  ·  2.6h active (cases 64m · lead 94m · stages 0m)  ·  13 dispatches
- Tokens: total 24,357,968  ·  **real work 229,125** (in 112,734 / out 116,391)  ·  cache 21.8M read / 2.3M write  ·  **cache hit rate 89.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 43 turns  ·  195 tool calls (4 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $3.49 (34%)
  - by stage: lead $3.49 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $2.27  ·  4 dispatch(es)  ·  37m
- **Per delivered case (incl. overhead): $10.35**
- Avg direct per case (excl. overhead): $6.86
- Direct cost spread: avg $6.86 · median $6.86 · min $6.86 · max $6.86
- Loaded cost spread (direct + even overhead share): avg $10.35 · median $10.35 · min $10.35 · max $10.35
- Active-time spread: avg 64m · median 64m · min 64m · max 64m  ·  loaded: avg 158m · median 158m · min 158m · max 158m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4714 | automated | $6.86 | $10.35 | 195,726 (in 98k / out 98k) | 64m | 158m | 11 | 150 (2) | 4 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $4.54 | 9 | 125,985 (in 70k / out 56k) | 91.7% | 49m | 97 (0) |
| test-automation-lead | $3.49 | 0 | 33,399 (in 15k / out 19k) | 82.8% | 94m | 45 (2) |
| qa-engineer | $2.31 | 4 | 69,741 (in 28k / out 42k) | 93.1% | 15m | 53 (2) |
