# Batch cost — skills-4635

Generated: 2026-11-11T17:58:12.369Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 15  ·  fix rounds: 1

## What it cost

- Total: $7.36  ·  1.2h active (cases 28m · lead 43m · stages 3m)  ·  14 dispatches
- Tokens: total 13,693,996  ·  **real work 175,609** (in 112,237 / out 63,372)  ·  cache 11.7M read / 1.9M write  ·  **cache hit rate 85.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  122 tool calls (2 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $2.95 (40%)
  - by stage: lead $1.69 · triage $0.34 (0m) · gate $0.47 (2m) · report $0.45 (1m)
- Rework (fix rounds — already inside per-case direct): $0.54  ·  1 dispatch(es)  ·  6m
- **Per delivered case (incl. overhead): $7.36**
- Avg direct per case (excl. overhead): $4.41
- Direct cost spread: avg $4.41 · median $4.41 · min $4.41 · max $4.41
- Loaded cost spread (direct + even overhead share): avg $7.36 · median $7.36 · min $7.36 · max $7.36
- Active-time spread: avg 28m · median 28m · min 28m · max 28m  ·  loaded: avg 74m · median 74m · min 74m · max 74m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4635 | automated | $4.41 | $7.36 | 116,363 (in 69k / out 48k) | 28m | 74m | 9 | 86 (1) | 1 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.05 | 8 | 77,308 (in 51k / out 26k) | 88.0% | 15m | 55 (1) |
| qa-engineer | $2.62 | 6 | 73,499 (in 43k / out 30k) | 86.7% | 16m | 47 (0) |
| test-automation-lead | $1.69 | 0 | 24,802 (in 18k / out 7k) | 74.7% | 43m | 20 (1) |
