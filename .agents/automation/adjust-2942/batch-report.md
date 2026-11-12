# Batch cost — adjust-2942

Generated: 2026-11-12T15:56:07.111Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-11 → 2026-11-13 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 2  ·  retired 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.43  ·  1.4h active (cases 24m · lead 58m · stages 0m)  ·  3 dispatches
- Tokens: total 18,373,338  ·  **real work 117,285** (in 42,695 / out 74,590)  ·  cache 16.9M read / 1.3M write  ·  **cache hit rate 92.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 38 turns  ·  117 tool calls (1 err, 99% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $3.23 (50%)
- **Per delivered case (incl. overhead): $3.22**
- Avg direct per case (excl. overhead): $1.07
- Direct cost spread: avg $1.07 · median $1.07 · min $1.07 · max $1.07
- Loaded cost spread (direct + even overhead share): avg $2.15 · median $2.15 · min $2.15 · max $2.15
- Active-time spread: avg 8m · median 8m · min 8m · max 8m  ·  loaded: avg 27m · median 27m · min 27m · max 27m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2010 | automated | $1.07 | $2.15 | 27,777 (in 11k / out 17k) | 8m | 27m | 1 | 26 (0) | 0 | 0 |
| ELITEA-2065 | automated | $1.07 | $2.15 | 27,777 (in 11k / out 17k) | 8m | 27m | 1 | 26 (0) | 0 | 0 |
| ELITEA-2036 | retired | $1.07 | $2.15 | 27,777 (in 11k / out 17k) | 8m | 27m | 1 | 26 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $3.23 | 0 | 33,956 (in 11k / out 23k) | 83.9% | 58m | 38 (1) |
| test-automation-engineer | $2.77 | 2 | 67,362 (in 21k / out 46k) | 96.9% | 22m | 71 (0) |
| qa-engineer | $0.44 | 1 | 15,967 (in 11k / out 5k) | 88.7% | 1m | 8 (0) |
