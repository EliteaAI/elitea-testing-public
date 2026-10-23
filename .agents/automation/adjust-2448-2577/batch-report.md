# Batch cost — adjust-2448-2577

Generated: 2026-10-23T06:51:05.981Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-10-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (4 passed x3 on DEV (2448 + 3 code_node siblings sharing the helper) runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.04  ·  0.6h active (cases 12m · lead 22m · stages 0m)  ·  2 dispatches
- Tokens: total 5,049,998  ·  **real work 52,566** (in 31,710 / out 20,856)  ·  cache 4.5M read / 450k write  ·  **cache hit rate 90.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  43 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.93 (46%)
- **Per delivered case (incl. overhead): $2.04**
- Avg direct per case (excl. overhead): $1.11
- Direct cost spread: avg $1.11 · median $1.11 · min $1.11 · max $1.11
- Loaded cost spread (direct + even overhead share): avg $2.04 · median $2.04 · min $2.04 · max $2.04
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 34m · median 34m · min 34m · max 34m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2448 | automated | $1.11 | $2.04 | 32,220 (in 21k / out 11k) | 12m | 34m | 2 | 23 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.93 | 0 | 20,346 (in 11k / out 10k) | 89.9% | 22m | 20 (1) |
| test-automation-engineer | $0.78 | 1 | 18,906 (in 10k / out 9k) | 92.7% | 11m | 18 (0) |
| qa-engineer | $0.33 | 1 | 13,314 (in 10k / out 3k) | 83.1% | 1m | 5 (0) |
