# Batch cost — adjust-2811

Generated: 2026-10-31T08:26:24.539Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations runs)
- Gate record (script-authored): green at 2026-10-31T08:26:23Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.15  ·  0.1h active (cases 0m · lead 8m · stages 0m)  ·  1 dispatches
- Tokens: total 2,990,729  ·  **real work 34,252** (in 21,299 / out 12,953)  ·  cache 2.7M read / 241k write  ·  **cache hit rate 91.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  28 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.73 (64%)
- **Per delivered case (incl. overhead): $1.15**
- Avg direct per case (excl. overhead): $0.42
- Direct cost spread: avg $0.42 · median $0.42 · min $0.42 · max $0.42
- Loaded cost spread (direct + even overhead share): avg $1.15 · median $1.15 · min $1.15 · max $1.15
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 8m · median 8m · min 8m · max 8m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2035 | automated | $0.42 | $1.15 | 13,267 (in 10k / out 3k) | 0m | 8m | 1 | 5 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.73 | 0 | 20,985 (in 11k / out 10k) | 94.7% | 8m | 23 (0) |
| qa-engineer | $0.42 | 1 | 13,267 (in 10k / out 3k) | 71.6% | 0m | 5 (0) |
