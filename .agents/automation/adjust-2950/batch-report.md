# Batch cost — adjust-2950

Generated: 2026-11-12T17:16:23.908Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-11 → 2026-11-13 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $5.70  ·  1.1h active (cases 50m · lead 18m · stages 0m)  ·  3 dispatches
- Tokens: total 19,846,926  ·  **real work 135,911** (in 42,419 / out 93,492)  ·  cache 18.8M read / 914k write  ·  **cache hit rate 95.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  135 tool calls (3 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.59 (28%)
- **Per delivered case (incl. overhead): $2.85**
- Avg direct per case (excl. overhead): $2.06
- Direct cost spread: avg $2.06 · median $2.06 · min $2.06 · max $2.06
- Loaded cost spread (direct + even overhead share): avg $2.85 · median $2.85 · min $2.85 · max $2.85
- Active-time spread: avg 25m · median 25m · min 25m · max 25m  ·  loaded: avg 34m · median 34m · min 34m · max 34m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2444 | automated | $2.06 | $2.85 | 56,519 (in 16k / out 41k) | 25m | 34m | 1.5 | 58 (1) | 0 | 0 |
| ELITEA-2443 | automated | $2.06 | $2.85 | 56,519 (in 16k / out 41k) | 25m | 34m | 1.5 | 58 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.65 | 2 | 95,385 (in 21k / out 74k) | 97.6% | 48m | 106 (1) |
| test-automation-lead | $1.59 | 0 | 22,874 (in 11k / out 12k) | 81.0% | 18m | 20 (2) |
| qa-engineer | $0.46 | 1 | 17,652 (in 11k / out 7k) | 87.0% | 1m | 9 (0) |
