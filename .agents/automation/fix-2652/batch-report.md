# Batch cost — fix-2652

Generated: 2026-10-24T05:30:06.154Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-23 → 2026-10-25 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at 2026-10-24T05:40:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.41  ·  0.2h active (cases 1m · lead 9m · stages 0m)  ·  1 dispatches
- Tokens: total 5,124,143  ·  **real work 41,666** (in 21,664 / out 20,002)  ·  cache 4.9M read / 220k write  ·  **cache hit rate 95.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 37 turns  ·  43 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.98 (70%)
- **Per delivered case (incl. overhead): $1.41**
- Avg direct per case (excl. overhead): $0.43
- Direct cost spread: avg $0.43 · median $0.43 · min $0.43 · max $0.43
- Loaded cost spread (direct + even overhead share): avg $1.41 · median $1.41 · min $1.41 · max $1.41
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 10m · median 10m · min 10m · max 10m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2009 | automated | $0.43 | $1.41 | 13,399 (in 10k / out 3k) | 1m | 10m | 1 | 6 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.98 | 0 | 28,267 (in 11k / out 17k) | 97.5% | 9m | 37 (0) |
| qa-engineer | $0.43 | 1 | 13,399 (in 10k / out 3k) | 77.3% | 1m | 6 (0) |
