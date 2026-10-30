# Batch cost — chat-project-context-3369

Generated: 2026-10-30T10:40:05.665Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-31 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (6 run record(s))
- Findings reported: 18  ·  fix rounds: 1

## What it cost

- Total: $10.61  ·  1.6h active (cases 38m · lead 57m · stages 4m)  ·  15 dispatches
- Tokens: total 20,277,057  ·  **real work 209,587** (in 124,631 / out 84,956)  ·  cache 17.4M read / 2.7M write  ·  **cache hit rate 85.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 41 turns  ·  166 tool calls (8 err, 95% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $5.56 (52%)
  - by stage: lead $4.30 · triage $0.33 (0m) · gate $0.49 (3m) · report $0.44 (1m)
- Rework (fix rounds — already inside per-case direct): $0.56  ·  1 dispatch(es)  ·  11m
- **Per delivered case (incl. overhead): $10.61**
- Avg direct per case (excl. overhead): $5.05
- Direct cost spread: avg $5.05 · median $5.05 · min $5.05 · max $5.05
- Loaded cost spread (direct + even overhead share): avg $10.61 · median $10.61 · min $10.61 · max $10.61
- Active-time spread: avg 38m · median 38m · min 38m · max 38m  ·  loaded: avg 99m · median 99m · min 99m · max 99m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3369 | automated | $5.05 | $10.61 | 132,977 (in 77k / out 56k) | 38m | 99m | 10 | 109 (5) | 1 | 18 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $4.30 | 0 | 41,180 (in 22k / out 19k) | 79.8% | 57m | 39 (0) |
| test-automation-engineer | $3.21 | 8 | 81,187 (in 51k / out 30k) | 90.9% | 32m | 72 (5) |
| qa-engineer | $3.09 | 7 | 87,220 (in 52k / out 36k) | 85.6% | 10m | 55 (3) |
