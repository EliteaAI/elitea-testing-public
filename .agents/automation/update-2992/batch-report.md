# Batch cost — update-2992

Generated: 2026-11-20T08:59:43.465Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-19 → 2026-11-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.13  ·  0.4h active (cases 8m · lead 16m · stages 0m)  ·  2 dispatches
- Tokens: total 5,033,448  ·  **real work 51,303** (in 31,826 / out 19,477)  ·  cache 4.5M read / 480k write  ·  **cache hit rate 89.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 13 turns  ·  40 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.82 (39%)
- **Per delivered case (incl. overhead): $2.13**
- Avg direct per case (excl. overhead): $1.30
- Direct cost spread: avg $1.30 · median $1.30 · min $1.30 · max $1.30
- Loaded cost spread (direct + even overhead share): avg $2.12 · median $2.12 · min $2.12 · max $2.12
- Active-time spread: avg 8m · median 8m · min 8m · max 8m  ·  loaded: avg 24m · median 24m · min 24m · max 24m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1795 | automated | $1.30 | $2.12 | 35,321 (in 21k / out 14k) | 8m | 24m | 2 | 26 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.92 | 1 | 20,349 (in 10k / out 10k) | 93.1% | 7m | 19 (0) |
| test-automation-lead | $0.82 | 0 | 15,982 (in 11k / out 5k) | 85.9% | 16m | 14 (0) |
| qa-engineer | $0.39 | 1 | 14,972 (in 11k / out 4k) | 85.5% | 1m | 7 (0) |
