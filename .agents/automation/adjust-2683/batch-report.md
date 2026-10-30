# Batch cost — adjust-2683

Generated: 2026-10-25T08:55:53.318Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (41.96s,41.77s,42.39s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.82  ·  0.6h active (cases 15m · lead 21m · stages 0m)  ·  2 dispatches
- Tokens: total 9,401,021  ·  **real work 64,608** (in 32,084 / out 32,524)  ·  cache 8.8M read / 516k write  ·  **cache hit rate 94.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 31 turns  ·  72 tool calls (1 err, 99% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.30 (46%)
- **Per delivered case (incl. overhead): $1.41**
- Avg direct per case (excl. overhead): $0.76
- Direct cost spread: avg $0.76 · median $0.76 · min $0.58 · max $0.94
- Loaded cost spread (direct + even overhead share): avg $1.41 · median $1.41 · min $1.23 · max $1.59
- Active-time spread: avg 8m · median 8m · min 7m · max 8m  ·  loaded: avg 19m · median 19m · min 18m · max 19m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1140 | automated | $0.94 | $1.59 | 27,847 (in 16k / out 12k) | 8m | 19m | 1.5 | 24 (0) | 0 | 0 |
| ELITEA-1141 | automated | $0.58 | $1.23 | 13,887 (in 5k / out 9k) | 7m | 18m | 0.5 | 18 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.30 | 0 | 22,875 (in 11k / out 12k) | 93.1% | 21m | 31 (1) |
| test-automation-engineer | $1.16 | 1 | 27,773 (in 10k / out 17k) | 96.4% | 13m | 35 (0) |
| qa-engineer | $0.36 | 1 | 13,960 (in 10k / out 3k) | 82.4% | 1m | 6 (0) |
