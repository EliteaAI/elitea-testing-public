# Batch cost — elitea-4718

Generated: 2026-11-18T13:56:34.791Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 14  ·  fix rounds: 1

## What it cost

- Total: $10.56  ·  1.8h active (cases 45m · lead 58m · stages 3m)  ·  15 dispatches
- Tokens: total 22,937,660  ·  **real work 253,228** (in 122,428 / out 130,800)  ·  cache 20.3M read / 2.4M write  ·  **cache hit rate 88.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  180 tool calls (6 err, 97% ok)  ·  skills: workflow-authoring
- Overhead (lead + triage + gate + report, shown once): $3.79 (36%)
  - by stage: lead $2.53 · triage $0.34 (0m) · gate $0.49 (2m) · report $0.43 (1m)
- Rework (fix rounds — already inside per-case direct): $0.55  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $10.56**
- Avg direct per case (excl. overhead): $6.77
- Direct cost spread: avg $6.77 · median $6.77 · min $6.77 · max $6.77
- Loaded cost spread (direct + even overhead share): avg $10.56 · median $10.56 · min $10.56 · max $10.56
- Active-time spread: avg 45m · median 45m · min 45m · max 45m  ·  loaded: avg 106m · median 106m · min 106m · max 106m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4718 | automated | $6.77 | $10.56 | 190,616 (in 77k / out 113k) | 45m | 106m | 10 | 142 (3) | 1 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $4.15 | 7 | 116,725 (in 52k / out 65k) | 91.6% | 22m | 83 (2) |
| test-automation-engineer | $3.88 | 8 | 109,124 (in 51k / out 58k) | 91.7% | 26m | 75 (3) |
| test-automation-lead | $2.53 | 0 | 27,379 (in 19k / out 8k) | 66.7% | 58m | 22 (1) |
