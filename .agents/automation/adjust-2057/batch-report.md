# Batch cost — adjust-2057

Generated: 2026-10-24T05:19:01.629Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-23 → 2026-10-25 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at 2026-10-24T05:30:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.99  ·  0.3h active (cases 6m · lead 11m · stages 0m)  ·  2 dispatches
- Tokens: total 6,501,107  ·  **real work 60,844** (in 32,750 / out 28,094)  ·  cache 6.1M read / 330k write  ·  **cache hit rate 94.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 32 turns  ·  49 tool calls (2 err, 96% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.95 (48%)
- Rework (fix rounds — already inside per-case direct): $0.71  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $1.99**
- Avg direct per case (excl. overhead): $1.04
- Direct cost spread: avg $1.04 · median $1.04 · min $1.04 · max $1.04
- Loaded cost spread (direct + even overhead share): avg $1.99 · median $1.99 · min $1.99 · max $1.99
- Active-time spread: avg 6m · median 6m · min 6m · max 6m  ·  loaded: avg 17m · median 17m · min 17m · max 17m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2057 | automated | $1.04 | $1.99 | 36,658 (in 21k / out 16k) | 6m | 17m | 2 | 17 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.95 | 0 | 24,186 (in 12k / out 12k) | 97.0% | 11m | 32 (2) |
| test-automation-engineer | $0.71 | 1 | 22,584 (in 10k / out 12k) | 92.3% | 5m | 13 (0) |
| qa-engineer | $0.33 | 1 | 14,074 (in 10k / out 4k) | 78.6% | 1m | 4 (0) |
