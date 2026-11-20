# Batch cost — update-2991

Generated: 2026-11-20T08:33:28.388Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: $3.36  ·  0.7h active (cases 18m · lead 24m · stages 0m)  ·  6 dispatches
- Tokens: total 8,230,891  ·  **real work 77,904** (in 41,579 / out 36,325)  ·  cache 7.4M read / 747k write  ·  **cache hit rate 90.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  68 tool calls (3 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $1.21 (36%)
  - by stage: lead $1.21 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $1.68**
- Avg direct per case (excl. overhead): $1.07
- Direct cost spread: avg $1.07 · median $1.07 · min $1.07 · max $1.07
- Loaded cost spread (direct + even overhead share): avg $1.68 · median $1.68 · min $1.68 · max $1.68
- Active-time spread: avg 9m · median 9m · min 9m · max 9m  ·  loaded: avg 21m · median 21m · min 21m · max 21m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1794 | automated | $1.07 | $1.68 | 26,254 (in 13k / out 13k) | 9m | 21m | 2 | 24 (1) | 0 | 1 |
| ELITEA-1896 | automated | $1.07 | $1.68 | 26,254 (in 13k / out 13k) | 9m | 21m | 2 | 24 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $1.54 | 3 | 37,465 (in 17k / out 20k) | 93.3% | 11m | 37 (1) |
| test-automation-lead | $1.21 | 0 | 25,396 (in 16k / out 10k) | 85.4% | 24m | 20 (2) |
| test-automation-engineer | $0.61 | 3 | 15,043 (in 9k / out 7k) | 88.9% | 6m | 11 (0) |
