# Batch cost — adjust-elitea-4629

Generated: 2026-11-13T11:32:03.618Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-12 → 2026-11-14 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.24  ·  0.3h active (cases 0m · lead 15m · stages 0m)  ·  1 dispatches
- Tokens: total 3,599,131  ·  **real work 34,394** (in 21,672 / out 12,722)  ·  cache 3.3M read / 250k write  ·  **cache hit rate 92.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  32 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.82 (66%)
- **Per delivered case (incl. overhead): $1.24**
- Avg direct per case (excl. overhead): $0.42
- Direct cost spread: avg $0.42 · median $0.42 · min $0.42 · max $0.42
- Loaded cost spread (direct + even overhead share): avg $1.24 · median $1.24 · min $1.24 · max $1.24
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 15m · median 15m · min 15m · max 15m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4629 | automated | $0.42 | $1.24 | 13,316 (in 11k / out 3k) | 0m | 15m | 1 | 5 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.82 | 0 | 21,078 (in 11k / out 10k) | 95.2% | 15m | 27 (0) |
| qa-engineer | $0.42 | 1 | 13,316 (in 11k / out 3k) | 77.5% | 0m | 5 (0) |
