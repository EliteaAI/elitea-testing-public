# Batch cost — adjust-2916

Generated: 2026-11-11T12:10:38.499Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 separate invocations of tests/ui/pipelines/test_pipeline_canvas_zoom_and_pan.py (2 tests) on DEV, 2 passed each runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.88  ·  0.5h active (cases 14m · lead 18m · stages 0m)  ·  2 dispatches
- Tokens: total 7,932,644  ·  **real work 76,114** (in 31,630 / out 44,484)  ·  cache 7.3M read / 551k write  ·  **cache hit rate 92.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 13 turns  ·  54 tool calls (3 err, 94% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.97 (34%)
- **Per delivered case (incl. overhead): $2.88**
- Avg direct per case (excl. overhead): $1.91
- Direct cost spread: avg $1.91 · median $1.91 · min $1.91 · max $1.91
- Loaded cost spread (direct + even overhead share): avg $2.88 · median $2.88 · min $2.88 · max $2.88
- Active-time spread: avg 14m · median 14m · min 14m · max 14m  ·  loaded: avg 32m · median 32m · min 32m · max 32m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2057 | automated | $1.91 | $2.88 | 57,502 (in 21k / out 37k) | 14m | 32m | 2 | 40 (3) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $1.48 | 1 | 41,817 (in 10k / out 31k) | 96.3% | 13m | 34 (3) |
| test-automation-lead | $0.97 | 0 | 18,612 (in 11k / out 8k) | 84.0% | 18m | 14 (0) |
| qa-engineer | $0.42 | 1 | 15,685 (in 10k / out 5k) | 84.5% | 1m | 6 (0) |
