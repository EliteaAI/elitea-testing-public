# Batch cost — chat-send-button-2505

Generated: 2026-10-22T11:32:31.237Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-21 → 2026-10-23 (scopes)_

_1 session(s) also served other batches — their session-level figures are split evenly; 19 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-22 (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $11.59  ·  2.3h active (cases 51m · lead 79m · stages 5m)  ·  11.67 dispatches
- Tokens: total 25,857,835  ·  **real work 204,753** (in 113,389 / out 91,364)  ·  cache 22.9M read / 2.8M write  ·  **cache hit rate 88.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 49 turns  ·  194 tool calls (11 err, 94% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $6.30 (54%)
  - by stage: lead $5.68 · triage $0.18 (1m) · gate $0.44 (4m) · report n/a (0m)
- **Per delivered case (incl. overhead): $11.59**
- Avg direct per case (excl. overhead): $5.29
- Direct cost spread: avg $5.29 · median $5.29 · min $5.29 · max $5.29
- Loaded cost spread (direct + even overhead share): avg $11.59 · median $11.59 · min $11.59 · max $11.59
- Active-time spread: avg 51m · median 51m · min 51m · max 51m  ·  loaded: avg 135m · median 135m · min 135m · max 135m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2466 | automated | $5.29 | $11.59 | 143,753 (in 79k / out 64k) | 51m | 135m | 8 | 131 (6) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $5.68 | 0 | 50,558 (in 28k / out 22k) | 82.1% | 79m | 48 (4) |
| test-automation-engineer | $3.50 | 5.67 | 87,468 (in 51k / out 37k) | 94.3% | 47m | 93 (2) |
| qa-engineer | $2.41 | 6 | 66,729 (in 34k / out 32k) | 86.9% | 9m | 52 (5) |
