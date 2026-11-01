# Batch cost — adjust-2835

Generated: 2026-11-01T04:11:14.774Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-31 → 2026-11-02 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.87  ·  0.3h active (cases 4m · lead 15m · stages 0m)  ·  2 dispatches
- Tokens: total 4,972,611  ·  **real work 52,666** (in 32,042 / out 20,624)  ·  cache 4.5M read / 383k write  ·  **cache hit rate 91.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 26 turns  ·  43 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.89 (47%)
- Rework (fix rounds — already inside per-case direct): $0.64  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $1.87**
- Avg direct per case (excl. overhead): $0.99
- Direct cost spread: avg $0.99 · median $0.99 · min $0.99 · max $0.99
- Loaded cost spread (direct + even overhead share): avg $1.88 · median $1.88 · min $1.88 · max $1.88
- Active-time spread: avg 4m · median 4m · min 4m · max 4m  ·  loaded: avg 19m · median 19m · min 19m · max 19m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2016 | automated | $0.99 | $1.88 | 30,836 (in 21k / out 10k) | 4m | 19m | 2 | 14 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.89 | 0 | 21,830 (in 11k / out 11k) | 95.1% | 15m | 29 (0) |
| test-automation-engineer | $0.64 | 1 | 17,223 (in 10k / out 7k) | 87.9% | 4m | 10 (0) |
| qa-engineer | $0.34 | 1 | 13,613 (in 10k / out 3k) | 78.2% | 0m | 4 (0) |
