# Batch cost — adjust-2008

Generated: 2026-10-24T06:39:40.477Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-23 → 2026-10-25 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined (3 runs)
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.75  ·  0.2h active (cases 1m · lead 13m · stages 0m)  ·  1 dispatches
- Tokens: total 6,618,368  ·  **real work 47,543** (in 21,583 / out 25,960)  ·  cache 6.3M read / 264k write  ·  **cache hit rate 95.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 42 turns  ·  52 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.25 (71%)
- **Per delivered case (incl. overhead): $1.75**
- Avg direct per case (excl. overhead): $0.50
- Direct cost spread: avg $0.50 · median $0.50 · min $0.50 · max $0.50
- Loaded cost spread (direct + even overhead share): avg $1.75 · median $1.75 · min $1.75 · max $1.75
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 14m · median 14m · min 14m · max 14m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2008 | automated | $0.50 | $1.75 | 14,929 (in 10k / out 4k) | 1m | 14m | 1 | 9 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.25 | 0 | 32,614 (in 11k / out 22k) | 97.6% | 13m | 43 (0) |
| qa-engineer | $0.50 | 1 | 14,929 (in 10k / out 4k) | 80.6% | 1m | 9 (0) |
