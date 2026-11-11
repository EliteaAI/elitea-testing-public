# Batch cost — adjust-2876-midturn-precondition

Generated: 2026-11-11T18:44:20.361Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: PASS (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `PASS` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $2.72  ·  0.4h active (cases 7m · lead 19m · stages 0m)  ·  4 dispatches
- Tokens: total 7,824,317  ·  **real work 91,678** (in 52,943 / out 38,735)  ·  cache 7.2M read / 504k write  ·  **cache hit rate 92.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 31 turns  ·  66 tool calls (2 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.94 (35%)
- Rework (fix rounds — already inside per-case direct): $0.37  ·  1 dispatch(es)  ·  2m
- **Per delivered case (incl. overhead): $2.72**
- Avg direct per case (excl. overhead): $1.78
- Direct cost spread: avg $1.78 · median $1.78 · min $1.78 · max $1.78
- Loaded cost spread (direct + even overhead share): avg $2.72 · median $2.72 · min $2.72 · max $2.72
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 26m · median 26m · min 26m · max 26m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2876 | automated | $1.78 | $2.72 | 62,818 (in 42k / out 21k) | 7m | 26m | 4 | 33 (1) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.03 | 2 | 33,723 (in 21k / out 13k) | 90.3% | 5m | 19 (1) |
| test-automation-lead | $0.94 | 0 | 28,860 (in 11k / out 18k) | 96.9% | 19m | 33 (1) |
| qa-engineer | $0.76 | 2 | 29,095 (in 21k / out 8k) | 86.0% | 2m | 14 (0) |
