# Batch cost — adjust-3749

Generated: 2026-10-25T07:01:48.690Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-25T07:01:47Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.05  ·  0.3h active (cases 5m · lead 14m · stages 0m)  ·  2 dispatches
- Tokens: total 7,149,502  ·  **real work 56,630** (in 33,235 / out 23,395)  ·  cache 6.7M read / 345k write  ·  **cache hit rate 94.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 38 turns  ·  54 tool calls (3 err, 94% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.17 (57%)
- Rework (fix rounds — already inside per-case direct): $0.54  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $2.05**
- Avg direct per case (excl. overhead): $0.88
- Direct cost spread: avg $0.88 · median $0.88 · min $0.88 · max $0.88
- Loaded cost spread (direct + even overhead share): avg $2.05 · median $2.05 · min $2.05 · max $2.05
- Active-time spread: avg 5m · median 5m · min 5m · max 5m  ·  loaded: avg 19m · median 19m · min 19m · max 19m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | automated | $0.88 | $2.05 | 27,857 (in 21k / out 7k) | 5m | 19m | 2 | 14 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.17 | 0 | 28,773 (in 12k / out 16k) | 97.3% | 14m | 40 (3) |
| test-automation-engineer | $0.54 | 1 | 14,912 (in 10k / out 5k) | 89.8% | 5m | 9 (0) |
| qa-engineer | $0.34 | 1 | 12,945 (in 10k / out 2k) | 78.3% | 0m | 5 (0) |
