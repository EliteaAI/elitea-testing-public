# Batch cost — elitea-4629

Generated: 2026-11-11T10:43:52.839Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: pass (3 runs)
- Gate record (script-authored): pass at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 2

## What it cost

- Total: $8.68  ·  2.1h active (cases 52m · lead 72m · stages 0m)  ·  15 dispatches
- Tokens: total 15,566,519  ·  **real work 181,468** (in 105,850 / out 75,618)  ·  cache 13.1M read / 2.2M write  ·  **cache hit rate 84.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  136 tool calls (1 err, 99% ok)
- Overhead (lead + triage + gate + report, shown once): $2.60 (30%)
  - by stage: lead $2.60 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.90  ·  2 dispatch(es)  ·  19m
- **Per delivered case (incl. overhead): $8.68**
- Avg direct per case (excl. overhead): $6.08
- Direct cost spread: avg $6.08 · median $6.08 · min $6.08 · max $6.08
- Loaded cost spread (direct + even overhead share): avg $8.68 · median $8.68 · min $8.68 · max $8.68
- Active-time spread: avg 52m · median 52m · min 52m · max 52m  ·  loaded: avg 124m · median 124m · min 124m · max 124m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4629 | automated | $6.08 | $8.68 | 155,440 (in 87k / out 68k) | 52m | 124m | 11 | 116 (1) | 2 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $3.28 | 8 | 93,784 (in 53k / out 40k) | 85.4% | 10m | 54 (1) |
| test-automation-engineer | $2.80 | 7 | 61,656 (in 34k / out 28k) | 91.5% | 42m | 62 (0) |
| test-automation-lead | $2.60 | 0 | 26,028 (in 18k / out 8k) | 60.7% | 72m | 20 (0) |
