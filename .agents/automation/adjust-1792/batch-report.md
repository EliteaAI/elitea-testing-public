# Batch cost — adjust-1792

Generated: 2026-10-25T06:38:46.273Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (76.03s,76.05s,75.78s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.08  ·  0.3h active (cases 0m · lead 17m · stages 0m)  ·  1 dispatches
- Tokens: total 3,112,211  ·  **real work 34,052** (in 21,503 / out 12,549)  ·  cache 2.9M read / 211k write  ·  **cache hit rate 92.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  28 tool calls (1 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.69 (64%)
- **Per delivered case (incl. overhead): $1.08**
- Avg direct per case (excl. overhead): $0.39
- Direct cost spread: avg $0.39 · median $0.39 · min $0.39 · max $0.39
- Loaded cost spread (direct + even overhead share): avg $1.08 · median $1.08 · min $1.08 · max $1.08
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 17m · median 17m · min 17m · max 17m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1792 | automated | $0.39 | $1.08 | 12,418 (in 10k / out 2k) | 0m | 17m | 1 | 4 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.69 | 0 | 21,634 (in 11k / out 11k) | 95.9% | 17m | 24 (1) |
| qa-engineer | $0.39 | 1 | 12,418 (in 10k / out 2k) | 72.0% | 0m | 4 (0) |
