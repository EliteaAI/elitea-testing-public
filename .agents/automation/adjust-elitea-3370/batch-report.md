# Batch cost — adjust-elitea-3370

Generated: 2026-11-17T17:01:09.123Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-16 → 2026-11-18 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3/3 pass (59.3s,59.7s,58.8s) DEV, APP_PREFIX=/app runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.40  ·  0.2h active (cases 0m · lead 14m · stages 0m)  ·  1 dispatches
- Tokens: total 4,199,800  ·  **real work 35,801** (in 21,443 / out 14,358)  ·  cache 3.9M read / 269k write  ·  **cache hit rate 93.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  36 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.01 (72%)
- **Per delivered case (incl. overhead): $1.40**
- Avg direct per case (excl. overhead): $0.40
- Direct cost spread: avg $0.40 · median $0.40 · min $0.40 · max $0.40
- Loaded cost spread (direct + even overhead share): avg $1.41 · median $1.41 · min $1.41 · max $1.41
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 14m · median 14m · min 14m · max 14m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3370 | automated | $0.40 | $1.41 | 13,576 (in 11k / out 3k) | 0m | 14m | 1 | 3 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.01 | 0 | 22,225 (in 11k / out 11k) | 95.7% | 14m | 33 (1) |
| qa-engineer | $0.40 | 1 | 13,576 (in 11k / out 3k) | 62.4% | 0m | 3 (0) |
