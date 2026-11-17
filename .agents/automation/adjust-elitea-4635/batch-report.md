# Batch cost — adjust-elitea-4635

Generated: 2026-11-17T06:40:40.703Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-16 → 2026-11-18 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined (3 runs)
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.33  ·  0.1h active (cases 3m · lead 6m · stages 0m)  ·  2 dispatches
- Tokens: total 2,303,483  ·  **real work 43,647** (in 31,558 / out 12,089)  ·  cache 1.9M read / 333k write  ·  **cache hit rate 84.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 10 turns  ·  21 tool calls (1 err, 95% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.51 (38%)
- **Per delivered case (incl. overhead): $1.33**
- Avg direct per case (excl. overhead): $0.82
- Direct cost spread: avg $0.82 · median $0.82 · min $0.82 · max $0.82
- Loaded cost spread (direct + even overhead share): avg $1.33 · median $1.33 · min $1.33 · max $1.33
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 9m · median 9m · min 9m · max 9m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4635 | automated | $0.82 | $1.33 | 28,289 (in 21k / out 7k) | 3m | 9m | 2 | 10 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $0.51 | 1 | 15,375 (in 10k / out 5k) | 83.9% | 3m | 6 (1) |
| test-automation-lead | $0.51 | 0 | 15,358 (in 11k / out 5k) | 88.1% | 6m | 11 (0) |
| qa-engineer | $0.31 | 1 | 12,914 (in 11k / out 2k) | 71.4% | 0m | 4 (0) |
