# Batch cost — adjust-3750

Generated: 2026-10-25T07:31:28.019Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-25T07:35:00Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.32  ·  0.2h active (cases 0m · lead 11m · stages 0m)  ·  1 dispatches
- Tokens: total 4,436,505  ·  **real work 39,951** (in 23,634 / out 16,317)  ·  cache 4.2M read / 230k write  ·  **cache hit rate 94.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 32 turns  ·  40 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.88 (66%)
- **Per delivered case (incl. overhead): $1.32**
- Avg direct per case (excl. overhead): $0.45
- Direct cost spread: avg $0.45 · median $0.45 · min $0.45 · max $0.45
- Loaded cost spread (direct + even overhead share): avg $1.33 · median $1.33 · min $1.33 · max $1.33
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | automated | $0.45 | $1.33 | 15,245 (in 12k / out 3k) | 0m | 11m | 1 | 5 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 0 | 24,706 (in 11k / out 13k) | 97.1% | 11m | 35 (1) |
| qa-engineer | $0.45 | 1 | 15,245 (in 12k / out 3k) | 70.8% | 0m | 5 (0) |
