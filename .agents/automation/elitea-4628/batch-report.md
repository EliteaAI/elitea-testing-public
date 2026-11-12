# Batch cost — elitea-4628

Generated: 2026-11-11T09:21:15.218Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: pass (3 runs)
- Gate record (script-authored): pass at ? (3 run record(s))
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: $6.68  ·  1.1h active (cases 22m · lead 40m · stages 6m)  ·  12 dispatches
- Tokens: total 12,637,920  ·  **real work 150,998** (in 94,007 / out 56,991)  ·  cache 10.8M read / 1.7M write  ·  **cache hit rate 85.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  114 tool calls (6 err, 95% ok)
- Overhead (lead + triage + gate + report, shown once): $3.11 (47%)
  - by stage: lead $1.86 · triage $0.33 (0m) · gate $0.49 (5m) · report $0.43 (1m)
- **Per delivered case (incl. overhead): $6.68**
- Avg direct per case (excl. overhead): $3.57
- Direct cost spread: avg $3.57 · median $3.57 · min $3.57 · max $3.57
- Loaded cost spread (direct + even overhead share): avg $6.68 · median $6.68 · min $6.68 · max $6.68
- Active-time spread: avg 22m · median 22m · min 22m · max 22m  ·  loaded: avg 68m · median 68m · min 68m · max 68m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4628 | automated | $3.57 | $6.68 | 92,990 (in 51k / out 42k) | 22m | 68m | 7 | 75 (3) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.76 | 7 | 67,610 (in 42k / out 25k) | 90.2% | 23m | 59 (3) |
| qa-engineer | $2.06 | 5 | 59,550 (in 34k / out 25k) | 84.7% | 5m | 34 (1) |
| test-automation-lead | $1.86 | 0 | 23,838 (in 17k / out 7k) | 74.6% | 40m | 21 (2) |
