# Batch cost — chat-ask-4955-adj

Generated: 2026-11-27T17:50:26.680Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $7.99  ·  0.9h active (cases 20m · lead 36m · stages 1m)  ·  9 dispatches
- Tokens: total 20,873,979  ·  **real work 183,452** (in 98,211 / out 85,241)  ·  cache 18.7M read / 2.0M write  ·  **cache hit rate 89.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 50 turns  ·  160 tool calls (5 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $3.83 (48%)
  - by stage: lead $3.12 · triage $0.32 (0m) · report $0.39 (1m)
- **Per delivered case (incl. overhead): $7.99**
- Avg direct per case (excl. overhead): $4.16
- Direct cost spread: avg $4.16 · median $4.16 · min $4.16 · max $4.16
- Loaded cost spread (direct + even overhead share): avg $7.99 · median $7.99 · min $7.99 · max $7.99
- Active-time spread: avg 20m · median 20m · min 20m · max 20m  ·  loaded: avg 57m · median 57m · min 57m · max 57m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4955 | automated | $4.16 | $7.99 | 122,723 (in 65k / out 57k) | 20m | 57m | 7 | 104 (2) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.42 | 5 | 95,208 (in 46k / out 50k) | 93.6% | 19m | 86 (1) |
| test-automation-lead | $3.12 | 0 | 38,044 (in 15k / out 23k) | 86.4% | 36m | 49 (3) |
| qa-engineer | $1.45 | 4 | 50,200 (in 37k / out 13k) | 81.4% | 2m | 25 (1) |
