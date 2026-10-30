# Batch cost — adjust-2761

Generated: 2026-10-30T08:15:45.219Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.44  ·  0.2h active (cases 1m · lead 10m · stages 0m)  ·  1 dispatches
- Tokens: total 4,501,595  ·  **real work 40,692** (in 21,518 / out 19,174)  ·  cache 4.2M read / 262k write  ·  **cache hit rate 93.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  37 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.94 (65%)
- **Per delivered case (incl. overhead): $1.44**
- Avg direct per case (excl. overhead): $0.50
- Direct cost spread: avg $0.50 · median $0.50 · min $0.50 · max $0.50
- Loaded cost spread (direct + even overhead share): avg $1.44 · median $1.44 · min $1.44 · max $1.44
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 11m · median 11m · min 11m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2009 | automated | $0.50 | $1.44 | 14,743 (in 10k / out 4k) | 1m | 11m | 1 | 6 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.94 | 0 | 25,949 (in 11k / out 15k) | 96.6% | 10m | 31 (1) |
| qa-engineer | $0.50 | 1 | 14,743 (in 10k / out 4k) | 75.5% | 1m | 6 (0) |
