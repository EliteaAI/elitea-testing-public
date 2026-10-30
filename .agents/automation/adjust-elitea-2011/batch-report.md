# Batch cost — adjust-elitea-2011

Generated: 2026-10-25T05:11:46.375Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined (3 runs)
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.23  ·  0.2h active (cases 0m · lead 13m · stages 0m)  ·  1 dispatches
- Tokens: total 3,647,706  ·  **real work 35,388** (in 21,319 / out 14,069)  ·  cache 3.4M read / 239k write  ·  **cache hit rate 92.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  31 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.84 (68%)
- **Per delivered case (incl. overhead): $1.23**
- Avg direct per case (excl. overhead): $0.39
- Direct cost spread: avg $0.39 · median $0.39 · min $0.39 · max $0.39
- Loaded cost spread (direct + even overhead share): avg $1.23 · median $1.23 · min $1.23 · max $1.23
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 13m · median 13m · min 13m · max 13m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2011 | automated | $0.39 | $1.23 | 12,471 (in 10k / out 2k) | 0m | 13m | 1 | 4 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.84 | 0 | 22,917 (in 11k / out 12k) | 95.7% | 13m | 27 (0) |
| qa-engineer | $0.39 | 1 | 12,471 (in 10k / out 2k) | 72.0% | 0m | 4 (0) |
