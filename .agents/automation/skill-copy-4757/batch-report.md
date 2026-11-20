# Batch cost — skill-copy-4757

Generated: 2026-11-20T12:27:03.349Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (pass 32.27s,pass 31.12s,pass 32.10s runs)
- Gate record (script-authored): green at 2026-11-20 (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $3.71  ·  0.6h active (cases 12m · lead 25m · stages 0m)  ·  7 dispatches
- Tokens: total 8,427,983  ·  **real work 85,073** (in 50,840 / out 34,233)  ·  cache 7.5M read / 871k write  ·  **cache hit rate 89.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  72 tool calls (4 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.25 (34%)
  - by stage: lead $1.25 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.55  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $3.71**
- Avg direct per case (excl. overhead): $2.45
- Direct cost spread: avg $2.45 · median $2.45 · min $2.45 · max $2.45
- Loaded cost spread (direct + even overhead share): avg $3.70 · median $3.70 · min $3.70 · max $3.70
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 37m · median 37m · min 37m · max 37m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4757 | automated | $2.45 | $3.70 | 62,347 (in 36k / out 26k) | 12m | 37m | 5 | 49 (2) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.38 | 4 | 32,728 (in 19k / out 14k) | 91.6% | 9m | 31 (1) |
| test-automation-lead | $1.25 | 0 | 22,726 (in 15k / out 8k) | 87.2% | 25m | 23 (2) |
| qa-engineer | $1.08 | 3 | 29,619 (in 17k / out 12k) | 86.6% | 3m | 18 (1) |
