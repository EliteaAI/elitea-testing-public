# Batch cost — chat-bg-4957-adj

Generated: 2026-11-27T18:16:58.957Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (1 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.42  ·  1.8h active (cases 43m · lead 67m · stages 0m)  ·  8 dispatches
- Tokens: total 15,745,355  ·  **real work 128,248** (in 63,090 / out 65,158)  ·  cache 13.9M read / 1.7M write  ·  **cache hit rate 88.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 41 turns  ·  119 tool calls (3 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $3.21 (50%)
  - by stage: lead $3.21 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $6.42**
- Avg direct per case (excl. overhead): $3.21
- Direct cost spread: avg $3.21 · median $3.21 · min $3.21 · max $3.21
- Loaded cost spread (direct + even overhead share): avg $6.42 · median $6.42 · min $6.42 · max $6.42
- Active-time spread: avg 43m · median 43m · min 43m · max 43m  ·  loaded: avg 110m · median 110m · min 110m · max 110m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4957 | automated | $3.21 | $6.42 | 97,592 (in 48k / out 50k) | 43m | 110m | 6 | 80 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $3.21 | 0 | 30,656 (in 15k / out 15k) | 80.0% | 67m | 39 (3) |
| qa-engineer | $1.92 | 4 | 60,073 (in 29k / out 32k) | 93.7% | 26m | 51 (0) |
| test-automation-engineer | $1.29 | 4 | 37,519 (in 19k / out 18k) | 92.4% | 17m | 29 (0) |
