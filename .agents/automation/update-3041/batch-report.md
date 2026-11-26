# Batch cost — update-3041

Generated: 2026-11-26T15:57:11.480Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-25 → 2026-11-27 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-26 (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.01  ·  0.3h active (cases 8m · lead 12m · stages 0m)  ·  2 dispatches
- Tokens: total 6,144,769  ·  **real work 50,082** (in 32,403 / out 17,679)  ·  cache 5.6M read / 474k write  ·  **cache hit rate 91.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 14 turns  ·  46 tool calls (1 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $0.81 (40%)
- **Per delivered case (incl. overhead): $1.01**
- Avg direct per case (excl. overhead): $0.60
- Direct cost spread: avg $0.60 · median $0.60 · min $0.60 · max $0.60
- Loaded cost spread (direct + even overhead share): avg $1.01 · median $1.01 · min $1.01 · max $1.01
- Active-time spread: avg 4m · median 4m · min 4m · max 4m  ·  loaded: avg 10m · median 10m · min 10m · max 10m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1794 | automated | $0.60 | $1.01 | 16,615 (in 11k / out 6k) | 4m | 10m | 1 | 16 (1) | 0 | 0 |
| ELITEA-1896 | automated | $0.60 | $1.01 | 16,615 (in 11k / out 6k) | 4m | 10m | 1 | 16 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.90 | 1 | 19,631 (in 11k / out 9k) | 95.9% | 7m | 28 (1) |
| test-automation-lead | $0.81 | 0 | 16,853 (in 11k / out 6k) | 84.6% | 12m | 14 (0) |
| qa-engineer | $0.30 | 1 | 13,598 (in 11k / out 3k) | 78.9% | 1m | 4 (0) |
