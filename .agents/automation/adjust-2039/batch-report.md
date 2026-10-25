# Batch cost — adjust-2039

Generated: 2026-10-25T04:51:04.230Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.66  ·  0.1h active (cases 1m · lead 8m · stages 0m)  ·  2 dispatches
- Tokens: total 4,570,520  ·  **real work 51,187** (in 31,734 / out 19,453)  ·  cache 4.2M read / 322k write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 27 turns  ·  38 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.87 (52%)
- **Per delivered case (incl. overhead): $1.66**
- Avg direct per case (excl. overhead): $0.79
- Direct cost spread: avg $0.79 · median $0.79 · min $0.79 · max $0.79
- Loaded cost spread (direct + even overhead share): avg $1.66 · median $1.66 · min $1.66 · max $1.66
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 9m · median 9m · min 9m · max 9m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2039 | automated | $0.79 | $1.66 | 26,071 (in 21k / out 5k) | 1m | 9m | 2 | 10 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.87 | 0 | 25,116 (in 11k / out 14k) | 96.2% | 8m | 28 (1) |
| test-automation-engineer | $0.48 | 1 | 13,768 (in 10k / out 3k) | 84.1% | 1m | 6 (0) |
| qa-engineer | $0.31 | 1 | 12,303 (in 10k / out 2k) | 78.7% | 0m | 4 (0) |
