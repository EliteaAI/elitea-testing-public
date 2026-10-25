# Batch cost — adjust-2686

Generated: 2026-10-25T09:41:53.094Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (17.23s,18.60s,17.88s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.61  ·  0.3h active (cases 1m · lead 14m · stages 0m)  ·  2 dispatches
- Tokens: total 4,229,572  ·  **real work 48,764** (in 31,642 / out 17,122)  ·  cache 3.9M read / 330k write  ·  **cache hit rate 91.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  39 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.74 (46%)
- **Per delivered case (incl. overhead): $1.61**
- Avg direct per case (excl. overhead): $0.87
- Direct cost spread: avg $0.87 · median $0.87 · min $0.87 · max $0.87
- Loaded cost spread (direct + even overhead share): avg $1.61 · median $1.61 · min $1.61 · max $1.61
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 15m · median 15m · min 15m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2378 | automated | $0.87 | $1.61 | 27,533 (in 21k / out 7k) | 1m | 15m | 2 | 12 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.74 | 0 | 21,231 (in 11k / out 10k) | 96.4% | 14m | 27 (1) |
| test-automation-engineer | $0.54 | 1 | 14,555 (in 10k / out 4k) | 80.6% | 1m | 8 (0) |
| qa-engineer | $0.33 | 1 | 12,978 (in 10k / out 2k) | 78.2% | 0m | 4 (0) |
