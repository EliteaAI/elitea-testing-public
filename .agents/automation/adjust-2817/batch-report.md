# Batch cost — adjust-2817

Generated: 2026-10-31T09:41:21.623Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations, ~41s each runs)
- Gate record (script-authored): green at 2026-10-31T09:41:20Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.48  ·  0.2h active (cases 1m · lead 10m · stages 0m)  ·  2 dispatches
- Tokens: total 3,429,564  ·  **real work 46,031** (in 31,648 / out 14,383)  ·  cache 3.1M read / 322k write  ·  **cache hit rate 89.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  32 tool calls (2 err, 94% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.65 (44%)
- **Per delivered case (incl. overhead): $1.48**
- Avg direct per case (excl. overhead): $0.82
- Direct cost spread: avg $0.82 · median $0.82 · min $0.82 · max $0.82
- Loaded cost spread (direct + even overhead share): avg $1.47 · median $1.47 · min $1.47 · max $1.47
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | automated | $0.82 | $1.47 | 26,380 (in 21k / out 6k) | 1m | 11m | 2 | 10 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.65 | 0 | 19,651 (in 11k / out 9k) | 95.8% | 10m | 22 (2) |
| test-automation-engineer | $0.51 | 1 | 13,521 (in 10k / out 3k) | 76.3% | 1m | 7 (0) |
| qa-engineer | $0.31 | 1 | 12,859 (in 10k / out 2k) | 71.3% | 0m | 3 (0) |
