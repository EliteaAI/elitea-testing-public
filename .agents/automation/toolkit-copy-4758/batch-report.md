# Batch cost — toolkit-copy-4758

Generated: 2026-11-20T12:59:11.936Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): pass at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `pass` — write the verdict back into report.json
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: $5.87  ·  0.8h active (cases 16m · lead 30m · stages 3m)  ·  12 dispatches
- Tokens: total 10,680,457  ·  **real work 138,103** (in 94,487 / out 43,616)  ·  cache 9.0M read / 1.5M write  ·  **cache hit rate 84.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 18 turns  ·  99 tool calls (3 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $2.67 (46%)
  - by stage: lead $1.42 · triage $0.33 (0m) · gate $0.49 (2m) · report $0.42 (1m)
- **Per delivered case (incl. overhead): $5.87**
- Avg direct per case (excl. overhead): $3.20
- Direct cost spread: avg $3.20 · median $3.20 · min $3.20 · max $3.20
- Loaded cost spread (direct + even overhead share): avg $5.87 · median $5.87 · min $5.87 · max $5.87
- Active-time spread: avg 16m · median 16m · min 16m · max 16m  ·  loaded: avg 49m · median 49m · min 49m · max 49m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4758 | automated | $3.20 | $5.87 | 80,530 (in 51k / out 29k) | 16m | 49m | 7 | 61 (2) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.68 | 7 | 66,195 (in 43k / out 24k) | 89.4% | 16m | 55 (1) |
| qa-engineer | $1.77 | 5 | 48,097 (in 35k / out 14k) | 77.9% | 3m | 24 (2) |
| test-automation-lead | $1.42 | 0 | 23,811 (in 17k / out 6k) | 78.4% | 30m | 20 (0) |
