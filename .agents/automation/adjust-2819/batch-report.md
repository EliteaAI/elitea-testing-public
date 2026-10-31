# Batch cost — adjust-2819

Generated: 2026-10-31T10:19:49.413Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: sanctioned-red (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `sanctioned-red` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.63  ·  0.3h active (cases 5m · lead 15m · stages 0m)  ·  2 dispatches
- Tokens: total 4,226,142  ·  **real work 52,766** (in 33,500 / out 19,266)  ·  cache 3.8M read / 334k write  ·  **cache hit rate 91.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  37 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.74 (46%)
- Rework (fix rounds — already inside per-case direct): $0.53  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $1.63**
- Avg direct per case (excl. overhead): $0.88
- Direct cost spread: avg $0.88 · median $0.88 · min $0.88 · max $0.88
- Loaded cost spread (direct + even overhead share): avg $1.62 · median $1.62 · min $1.62 · max $1.62
- Active-time spread: avg 5m · median 5m · min 5m · max 5m  ·  loaded: avg 20m · median 20m · min 20m · max 20m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2357 | automated | $0.88 | $1.62 | 29,133 (in 23k / out 6k) | 5m | 20m | 2 | 11 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.74 | 0 | 23,633 (in 11k / out 13k) | 96.3% | 15m | 26 (1) |
| test-automation-engineer | $0.53 | 1 | 14,168 (in 10k / out 4k) | 83.7% | 5m | 7 (0) |
| qa-engineer | $0.35 | 1 | 14,965 (in 12k / out 3k) | 69.1% | 0m | 4 (0) |
