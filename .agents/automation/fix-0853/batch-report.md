# Batch cost — fix-0853

Generated: 2026-10-25T04:33:56.127Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.05  ·  0.1h active (cases 0m · lead 8m · stages 0m)  ·  1 dispatches
- Tokens: total 2,746,105  ·  **real work 36,253** (in 21,402 / out 14,851)  ·  cache 2.5M read / 204k write  ·  **cache hit rate 91.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  28 tool calls (1 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $0.64 (61%)
- **Per delivered case (incl. overhead): $1.05**
- Avg direct per case (excl. overhead): $0.40
- Direct cost spread: avg $0.40 · median $0.40 · min $0.40 · max $0.40
- Loaded cost spread (direct + even overhead share): avg $1.04 · median $1.04 · min $1.04 · max $1.04
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 8m · median 8m · min 8m · max 8m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-0853 | automated | $0.40 | $1.04 | 13,028 (in 10k / out 3k) | 0m | 8m | 1 | 5 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.64 | 0 | 23,225 (in 11k / out 12k) | 95.7% | 8m | 23 (1) |
| qa-engineer | $0.40 | 1 | 13,028 (in 10k / out 3k) | 71.9% | 0m | 5 (0) |
