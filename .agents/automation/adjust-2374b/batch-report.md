# Batch cost — adjust-2374b

Generated: 2026-10-30T12:51:57.296Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3/3 passed, separate invocations, DEV, APP_PREFIX=/app, reruns {} runs)
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.98  ·  0.3h active (cases 6m · lead 10m · stages 0m)  ·  2 dispatches
- Tokens: total 6,073,255  ·  **real work 58,345** (in 33,207 / out 25,138)  ·  cache 5.6M read / 365k write  ·  **cache hit rate 93.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  49 tool calls (3 err, 94% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.80 (40%)
- **Per delivered case (incl. overhead): $1.98**
- Avg direct per case (excl. overhead): $1.18
- Direct cost spread: avg $1.18 · median $1.18 · min $1.18 · max $1.18
- Loaded cost spread (direct + even overhead share): avg $1.98 · median $1.98 · min $1.98 · max $1.98
- Active-time spread: avg 6m · median 6m · min 6m · max 6m  ·  loaded: avg 16m · median 16m · min 16m · max 16m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2374 | automated | $1.18 | $1.98 | 32,748 (in 22k / out 11k) | 6m | 16m | 2 | 23 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.82 | 1 | 18,690 (in 12k / out 7k) | 93.7% | 5m | 19 (1) |
| test-automation-lead | $0.80 | 0 | 25,597 (in 11k / out 15k) | 95.7% | 10m | 26 (2) |
| qa-engineer | $0.36 | 1 | 14,058 (in 10k / out 4k) | 77.9% | 1m | 4 (0) |
