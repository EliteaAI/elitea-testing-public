# Batch cost — adjust-1955

Generated: 2026-11-12T07:14:10.677Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-01 → 2026-11-13 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $3.23  ·  0.5h active (cases 11m · lead 17m · stages 0m)  ·  2 dispatches
- Tokens: total 8,346,466  ·  **real work 71,733** (in 32,885 / out 38,848)  ·  cache 7.6M read / 688k write  ·  **cache hit rate 91.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 29 turns  ·  60 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.76 (54%)
- **Per delivered case (incl. overhead): $3.23**
- Avg direct per case (excl. overhead): $1.47
- Direct cost spread: avg $1.47 · median $1.47 · min $1.47 · max $1.47
- Loaded cost spread (direct + even overhead share): avg $3.23 · median $3.23 · min $3.23 · max $3.23
- Active-time spread: avg 11m · median 11m · min 11m · max 11m  ·  loaded: avg 28m · median 28m · min 28m · max 28m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1955 | automated | $1.47 | $3.23 | 43,024 (in 21k / out 22k) | 11m | 28m | 2 | 32 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.76 | 0 | 28,709 (in 12k / out 17k) | 88.9% | 17m | 28 (0) |
| test-automation-engineer | $1.05 | 1 | 27,383 (in 10k / out 17k) | 95.2% | 10m | 26 (1) |
| qa-engineer | $0.43 | 1 | 15,641 (in 11k / out 5k) | 84.8% | 1m | 6 (0) |
