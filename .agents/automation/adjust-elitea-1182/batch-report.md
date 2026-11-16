# Batch cost — adjust-elitea-1182

Generated: 2026-11-16T14:39:28.191Z  ·  sessions: 3 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-11-17 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (48.61s,50.15s,48.98s runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $4.29  ·  0.8h active (cases 6m · lead 33m · stages 6m)  ·  3 dispatches
- Tokens: total 13,239,909  ·  **real work 118,539** (in 66,802 / out 51,737)  ·  cache 12.3M read / 807k write  ·  **cache hit rate 93.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 75 turns  ·  109 tool calls (3 err, 97% ok)  ·  skills: adjust-automated-test, memory, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $3.41 (79%)
  - by stage: lead $2.71 · triage $0.70 (6m)
- Rework (fix rounds — already inside per-case direct): $0.53  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $4.29**
- Avg direct per case (excl. overhead): $0.88
- Direct cost spread: avg $0.88 · median $0.88 · min $0.88 · max $0.88
- Loaded cost spread (direct + even overhead share): avg $4.29 · median $4.29 · min $4.29 · max $4.29
- Active-time spread: avg 6m · median 6m · min 6m · max 6m  ·  loaded: avg 45m · median 45m · min 45m · max 45m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1182 | automated | $0.88 | $4.29 | 28,914 (in 21k / out 8k) | 6m | 45m | 2 | 14 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $2.71 | 0 | 68,187 (in 35k / out 33k) | 94.8% | 33m | 79 (2) |
| qa-engineer | $1.06 | 2 | 35,552 (in 21k / out 14k) | 90.2% | 7m | 21 (1) |
| test-automation-engineer | $0.53 | 1 | 14,800 (in 10k / out 4k) | 88.8% | 5m | 9 (0) |
