# Batch cost — adjust-2812

Generated: 2026-10-31T08:46:17.857Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations, reruns {} runs)
- Gate record (script-authored): green at 2026-10-31T08:46:16Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.66  ·  0.2h active (cases 1m · lead 10m · stages 0m)  ·  2 dispatches
- Tokens: total 4,612,787  ·  **real work 50,329** (in 31,759 / out 18,570)  ·  cache 4.2M read / 325k write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 28 turns  ·  38 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.88 (53%)
- **Per delivered case (incl. overhead): $1.66**
- Avg direct per case (excl. overhead): $0.78
- Direct cost spread: avg $0.78 · median $0.78 · min $0.78 · max $0.78
- Loaded cost spread (direct + even overhead share): avg $1.66 · median $1.66 · min $1.66 · max $1.66
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2046 | automated | $0.78 | $1.66 | 27,156 (in 21k / out 6k) | 1m | 11m | 2 | 8 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 0 | 23,173 (in 11k / out 12k) | 96.7% | 10m | 30 (0) |
| test-automation-engineer | $0.46 | 1 | 14,520 (in 10k / out 4k) | 77.6% | 1m | 4 (0) |
| qa-engineer | $0.32 | 1 | 12,636 (in 10k / out 2k) | 70.3% | 0m | 4 (0) |
