# Batch cost — mcp-copy-4759

Generated: 2026-11-20T13:47:30.886Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: $6.70  ·  1.1h active (cases 28m · lead 38m · stages 2m)  ·  12 dispatches
- Tokens: total 12,087,325  ·  **real work 140,707** (in 94,736 / out 45,971)  ·  cache 10.2M read / 1.8M write  ·  **cache hit rate 84.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  110 tool calls (5 err, 95% ok)
- Overhead (lead + triage + gate + report, shown once): $2.99 (45%)
  - by stage: lead $1.77 · triage $0.33 (0m) · gate $0.48 (1m) · report $0.41 (1m)
- **Per delivered case (incl. overhead): $6.70**
- Avg direct per case (excl. overhead): $3.71
- Direct cost spread: avg $3.71 · median $3.71 · min $3.71 · max $3.71
- Loaded cost spread (direct + even overhead share): avg $6.70 · median $6.70 · min $6.70 · max $6.70
- Active-time spread: avg 28m · median 28m · min 28m · max 28m  ·  loaded: avg 68m · median 68m · min 68m · max 68m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4759 | automated | $3.71 | $6.70 | 82,756 (in 52k / out 31k) | 28m | 68m | 7 | 74 (3) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.77 | 7 | 61,990 (in 43k / out 19k) | 85.3% | 21m | 46 (0) |
| qa-engineer | $2.16 | 5 | 54,706 (in 35k / out 20k) | 88.1% | 9m | 44 (3) |
| test-automation-lead | $1.77 | 0 | 24,011 (in 18k / out 6k) | 75.5% | 38m | 20 (2) |
