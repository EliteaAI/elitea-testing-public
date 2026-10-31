# Batch cost — adjust-2799

Generated: 2026-10-31T05:05:46.049Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-30 → 2026-11-01 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (1 passed x3 on DEV (APP_PREFIX=/app); test_pipeline_canvas_delete_node.py also green runs)
- Gate record (script-authored): green at 2026-10-31T05:05:44Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.08  ·  0.5h active (cases 0m · lead 29m · stages 0m)  ·  1 dispatches
- Tokens: total 6,853,406  ·  **real work 44,918** (in 21,517 / out 23,401)  ·  cache 6.4M read / 379k write  ·  **cache hit rate 94.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  53 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.67 (80%)
- **Per delivered case (incl. overhead): $2.08**
- Avg direct per case (excl. overhead): $0.42
- Direct cost spread: avg $0.42 · median $0.42 · min $0.42 · max $0.42
- Loaded cost spread (direct + even overhead share): avg $2.09 · median $2.09 · min $2.09 · max $2.09
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 29m · median 29m · min 29m · max 29m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2008 | automated | $0.42 | $2.09 | 12,945 (in 10k / out 2k) | 0m | 29m | 1 | 5 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.67 | 0 | 31,973 (in 11k / out 21k) | 95.6% | 29m | 48 (1) |
| qa-engineer | $0.42 | 1 | 12,945 (in 10k / out 2k) | 77.5% | 0m | 5 (0) |
