# Batch cost — adjust-2722

Generated: 2026-10-27T06:48:24.543Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-26 → 2026-10-28 (scopes)_

_1 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $3.23  ·  0.6h active (cases 12m · lead 22m · stages 0m)  ·  3 dispatches
- Tokens: total 10,275,299  ·  **real work 85,583** (in 47,506 / out 38,077)  ·  cache 9.6M read / 601k write  ·  **cache hit rate 93.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 42 turns  ·  80 tool calls (1 err, 99% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.44 (45%)
- **Per delivered case (incl. overhead): $3.23**
- Avg direct per case (excl. overhead): $1.79
- Direct cost spread: avg $1.79 · median $1.79 · min $1.79 · max $1.79
- Loaded cost spread (direct + even overhead share): avg $3.23 · median $3.23 · min $3.23 · max $3.23
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 34m · median 34m · min 34m · max 34m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1954 | automated | $1.79 | $3.23 | 52,165 (in 31k / out 21k) | 12m | 34m | 3 | 37 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.44 | 0 | 33,418 (in 16k / out 17k) | 95.5% | 22m | 43 (1) |
| test-automation-engineer | $1.42 | 2 | 37,968 (in 21k / out 17k) | 92.8% | 11m | 32 (0) |
| qa-engineer | $0.37 | 1 | 14,197 (in 10k / out 4k) | 82.4% | 1m | 5 (0) |
