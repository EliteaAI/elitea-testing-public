# Batch cost — chat-regenerate-2184

Generated: 2026-10-20T22:31:38.380Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 2

## What it cost

- Total: $5.08  ·  1.3h active (cases 35m · lead 40m · stages 0m)  ·  8 dispatches
- Tokens: total 9,015,112  ·  **real work 108,776** (in 71,646 / out 37,130)  ·  cache 7.6M read / 1.3M write  ·  **cache hit rate 84.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  79 tool calls (3 err, 96% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.80 (35%)
  - by stage: lead $1.80 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $1.25  ·  2 dispatch(es)  ·  19m
- **Per delivered case (incl. overhead): $5.08**
- Avg direct per case (excl. overhead): $3.27
- Direct cost spread: avg $3.27 · median $3.27 · min $3.27 · max $3.27
- Loaded cost spread (direct + even overhead share): avg $5.07 · median $5.07 · min $5.07 · max $5.07
- Active-time spread: avg 35m · median 35m · min 35m · max 35m  ·  loaded: avg 75m · median 75m · min 75m · max 75m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2184 | automated | $3.27 | $5.07 | 86,223 (in 57k / out 29k) | 35m | 75m | 6 | 58 (1) | 2 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.82 | 4 | 43,147 (in 30k / out 14k) | 86.8% | 26m | 30 (0) |
| test-automation-lead | $1.80 | 0 | 22,553 (in 14k / out 8k) | 75.9% | 40m | 21 (2) |
| qa-engineer | $1.46 | 4 | 43,076 (in 28k / out 15k) | 87.7% | 9m | 28 (1) |
