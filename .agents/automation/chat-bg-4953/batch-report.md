# Batch cost — chat-bg-4953

Generated: 2026-11-27T11:22:02.447Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (pass 65.6s,pass 66.2s,pass 66.0s runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 1

## What it cost

- Total: $7.78  ·  1.6h active (cases 46m · lead 51m · stages 0m)  ·  7 dispatches
- Tokens: total 24,912,963  ·  **real work 187,598** (in 65,686 / out 121,912)  ·  cache 23.1M read / 1.6M write  ·  **cache hit rate 93.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 37 turns  ·  168 tool calls (10 err, 94% ok)  ·  skills: memory, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $2.89 (37%)
  - by stage: lead $2.89 · triage n/a (0m) · report n/a (0m)
- Rework (fix rounds — already inside per-case direct): $0.93  ·  1 dispatch(es)  ·  9m
- **Per delivered case (incl. overhead): $7.78**
- Avg direct per case (excl. overhead): $4.89
- Direct cost spread: avg $4.89 · median $4.89 · min $4.89 · max $4.89
- Loaded cost spread (direct + even overhead share): avg $7.78 · median $7.78 · min $7.78 · max $7.78
- Active-time spread: avg 46m · median 46m · min 46m · max 46m  ·  loaded: avg 97m · median 97m · min 97m · max 97m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4953 | automated | $4.89 | $7.78 | 155,601 (in 50k / out 106k) | 46m | 97m | 5 | 131 (6) | 1 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $2.89 | 0 | 31,997 (in 16k / out 16k) | 81.3% | 51m | 37 (4) |
| test-automation-engineer | $2.71 | 3 | 79,967 (in 19k / out 61k) | 96.8% | 26m | 72 (3) |
| qa-engineer | $2.18 | 4 | 75,634 (in 30k / out 45k) | 95.0% | 20m | 59 (3) |
