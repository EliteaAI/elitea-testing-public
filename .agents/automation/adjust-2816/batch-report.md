# Batch cost — adjust-2816

Generated: 2026-10-31T09:29:25.182Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations, reruns {}; known defect #2415 (still OPEN) soft-check did not fire in any run runs)
- Gate record (script-authored): green at 2026-10-31T09:29:22Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.74  ·  0.1h active (cases 1m · lead 8m · stages 0m)  ·  2 dispatches
- Tokens: total 5,058,020  ·  **real work 49,032** (in 31,725 / out 17,307)  ·  cache 4.7M read / 353k write  ·  **cache hit rate 92.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 26 turns  ·  42 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.76 (44%)
- **Per delivered case (incl. overhead): $1.74**
- Avg direct per case (excl. overhead): $0.98
- Direct cost spread: avg $0.98 · median $0.98 · min $0.98 · max $0.98
- Loaded cost spread (direct + even overhead share): avg $1.74 · median $1.74 · min $1.74 · max $1.74
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 9m · median 9m · min 9m · max 9m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2006 | automated | $0.98 | $1.74 | 28,132 (in 21k / out 7k) | 1m | 9m | 2 | 16 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.76 | 0 | 20,900 (in 11k / out 10k) | 96.4% | 8m | 26 (0) |
| test-automation-engineer | $0.62 | 1 | 14,984 (in 10k / out 5k) | 88.5% | 1m | 11 (1) |
| qa-engineer | $0.36 | 1 | 13,148 (in 10k / out 3k) | 76.8% | 0m | 5 (0) |
