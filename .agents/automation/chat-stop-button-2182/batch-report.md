# Batch cost — chat-stop-button-2182

Generated: 2026-10-20T21:29:23.070Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 10  ·  fix rounds: 2

## What it cost

- Total: $9.95  ·  2.0h active (cases 55m · lead 64m · stages 2m)  ·  17 dispatches
- Tokens: total 19,915,227  ·  **real work 239,755** (in 143,593 / out 96,162)  ·  cache 17.2M read / 2.4M write  ·  **cache hit rate 87.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 19 turns  ·  170 tool calls (5 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $3.69 (37%)
  - by stage: lead $2.50 · triage $0.32 (0m) · gate $0.46 (1m) · report $0.40 (1m)
- Rework (fix rounds — already inside per-case direct): $0.84  ·  2 dispatch(es)  ·  13m
- **Per delivered case (incl. overhead): $9.95**
- Avg direct per case (excl. overhead): $6.26
- Direct cost spread: avg $6.26 · median $6.26 · min $6.26 · max $6.26
- Loaded cost spread (direct + even overhead share): avg $9.95 · median $9.95 · min $9.95 · max $9.95
- Active-time spread: avg 55m · median 55m · min 55m · max 55m  ·  loaded: avg 121m · median 121m · min 121m · max 121m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2182 | automated | $6.26 | $9.95 | 180,942 (in 100k / out 81k) | 55m | 121m | 12 | 135 (3) | 2 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $3.90 | 8 | 113,111 (in 61k / out 52k) | 90.6% | 27m | 76 (2) |
| test-automation-engineer | $3.55 | 9 | 101,093 (in 64k / out 37k) | 89.9% | 30m | 74 (3) |
| test-automation-lead | $2.50 | 0 | 25,551 (in 18k / out 7k) | 58.4% | 64m | 20 (0) |
