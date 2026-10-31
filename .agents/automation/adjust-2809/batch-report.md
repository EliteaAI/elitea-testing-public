# Batch cost — adjust-2809

Generated: 2026-10-31T08:10:45.691Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app), separate invocations runs)
- Gate record (script-authored): green at 2026-10-31T08:10:44Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.63  ·  0.2h active (cases 2m · lead 9m · stages 0m)  ·  2 dispatches
- Tokens: total 4,122,692  ·  **real work 53,846** (in 33,719 / out 20,127)  ·  cache 3.7M read / 336k write  ·  **cache hit rate 91.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  35 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.65 (40%)
- **Per delivered case (incl. overhead): $1.63**
- Avg direct per case (excl. overhead): $0.98
- Direct cost spread: avg $0.98 · median $0.98 · min $0.98 · max $0.98
- Loaded cost spread (direct + even overhead share): avg $1.63 · median $1.63 · min $1.63 · max $1.63
- Active-time spread: avg 2m · median 2m · min 2m · max 2m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2039 | automated | $0.98 | $1.63 | 32,974 (in 23k / out 10k) | 2m | 11m | 2 | 14 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.65 | 0 | 20,872 (in 11k / out 10k) | 95.6% | 9m | 21 (0) |
| test-automation-engineer | $0.59 | 1 | 16,853 (in 10k / out 7k) | 85.5% | 1m | 8 (0) |
| qa-engineer | $0.39 | 1 | 16,121 (in 12k / out 4k) | 81.8% | 1m | 6 (0) |
