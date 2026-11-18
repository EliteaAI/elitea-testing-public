# Batch cost — schedule-ui-2981

Generated: 2026-11-18T17:53:24.844Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: sanctioned-red
- Gate record (script-authored): sanctioned-red at 2026-11-18T17:50:00Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $7.57  ·  1.6h active (cases 42m · lead 55m · stages 0m)  ·  8 dispatches
- Tokens: total 22,096,816  ·  **real work 177,227** (in 58,892 / out 118,335)  ·  cache 20.5M read / 1.4M write  ·  **cache hit rate 93.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  164 tool calls (4 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $2.27 (30%)
  - by stage: lead $2.27 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.67  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $3.78**
- Avg direct per case (excl. overhead): $2.65
- Direct cost spread: avg $2.65 · median $2.65 · min $2.65 · max $2.65
- Loaded cost spread (direct + even overhead share): avg $3.78 · median $3.78 · min $3.78 · max $3.78
- Active-time spread: avg 21m · median 21m · min 21m · max 21m  ·  loaded: avg 49m · median 49m · min 49m · max 49m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2007 | automated | $2.65 | $3.78 | 74,798 (in 22k / out 53k) | 21m | 49m | 3 | 69 (1) | 0.5 | 0 |
| ELITEA-2008 | automated | $2.65 | $3.78 | 74,798 (in 22k / out 53k) | 21m | 49m | 3 | 69 (1) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $3.32 | 4 | 96,001 (in 26k / out 70k) | 95.9% | 24m | 84 (1) |
| test-automation-lead | $2.27 | 0 | 27,633 (in 16k / out 12k) | 76.7% | 55m | 26 (2) |
| test-automation-engineer | $1.98 | 4 | 53,593 (in 17k / out 36k) | 95.9% | 17m | 54 (1) |
