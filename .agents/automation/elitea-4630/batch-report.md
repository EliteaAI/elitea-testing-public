# Batch cost — elitea-4630

Generated: 2026-11-11T12:56:05.402Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined (gate-runs.jsonl runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `not-run` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $5.07  ·  1.3h active (cases 37m · lead 43m · stages 0m)  ·  8 dispatches
- Tokens: total 9,569,740  ·  **real work 98,539** (in 58,949 / out 39,590)  ·  cache 8.2M read / 1.3M write  ·  **cache hit rate 85.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 17 turns  ·  82 tool calls (5 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.77 (35%)
  - by stage: lead $1.77 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.42  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $5.07**
- Avg direct per case (excl. overhead): $3.30
- Direct cost spread: avg $3.30 · median $3.30 · min $3.30 · max $3.30
- Loaded cost spread (direct + even overhead share): avg $5.07 · median $5.07 · min $5.07 · max $5.07
- Active-time spread: avg 37m · median 37m · min 37m · max 37m  ·  loaded: avg 80m · median 80m · min 80m · max 80m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4630 | automated | $3.30 | $5.07 | 77,862 (in 44k / out 34k) | 37m | 80m | 6 | 64 (2) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $2.22 | 4 | 49,009 (in 27k / out 22k) | 87.2% | 20m | 36 (2) |
| test-automation-lead | $1.77 | 0 | 20,677 (in 15k / out 5k) | 71.3% | 43m | 18 (3) |
| test-automation-engineer | $1.08 | 4 | 28,853 (in 17k / out 12k) | 92.6% | 17m | 28 (0) |
