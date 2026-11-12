# Batch cost — adjust-2864

Generated: 2026-11-03T05:18:51.767Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-02 → 2026-11-04 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.46  ·  0.3h active (cases 1m · lead 17m · stages 0m)  ·  2 dispatches
- Tokens: total 3,792,594  ·  **real work 45,382** (in 31,541 / out 13,841)  ·  cache 3.4M read / 312k write  ·  **cache hit rate 90.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 24 turns  ·  34 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.68 (47%)
- Rework (fix rounds — already inside per-case direct): $0.47  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $1.46**
- Avg direct per case (excl. overhead): $0.78
- Direct cost spread: avg $0.78 · median $0.78 · min $0.78 · max $0.78
- Loaded cost spread (direct + even overhead share): avg $1.46 · median $1.46 · min $1.46 · max $1.46
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 18m · median 18m · min 18m · max 18m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2181 | automated | $0.78 | $1.46 | 24,847 (in 21k / out 4k) | 1m | 18m | 2 | 9 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.68 | 0 | 20,535 (in 11k / out 10k) | 96.4% | 17m | 25 (0) |
| test-automation-engineer | $0.47 | 1 | 12,477 (in 10k / out 2k) | 76.8% | 1m | 5 (0) |
| qa-engineer | $0.30 | 1 | 12,370 (in 10k / out 2k) | 71.2% | 0m | 4 (0) |
