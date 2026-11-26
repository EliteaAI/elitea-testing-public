# Batch cost — update-3045

Generated: 2026-11-26T17:01:07.992Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-25 → 2026-11-27 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-26 (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.44  ·  0.3h active (cases 2m · lead 15m · stages 0m)  ·  2 dispatches
- Tokens: total 4,409,803  ·  **real work 49,944** (in 32,492 / out 17,452)  ·  cache 4.0M read / 320k write  ·  **cache hit rate 92.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 24 turns  ·  39 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.66 (46%)
- **Per delivered case (incl. overhead): $1.44**
- Avg direct per case (excl. overhead): $0.78
- Direct cost spread: avg $0.78 · median $0.78 · min $0.78 · max $0.78
- Loaded cost spread (direct + even overhead share): avg $1.44 · median $1.44 · min $1.44 · max $1.44
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 17m · median 17m · min 17m · max 17m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | automated | $0.78 | $1.44 | 27,639 (in 21k / out 6k) | 2m | 17m | 2 | 13 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.66 | 0 | 22,305 (in 11k / out 11k) | 96.3% | 15m | 26 (1) |
| test-automation-engineer | $0.43 | 1 | 14,406 (in 11k / out 4k) | 84.1% | 2m | 6 (0) |
| qa-engineer | $0.34 | 1 | 13,233 (in 11k / out 2k) | 82.0% | 0m | 7 (0) |
