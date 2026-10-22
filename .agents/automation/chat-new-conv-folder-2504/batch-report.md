# Batch cost — chat-new-conv-folder-2504

Generated: 2026-10-22T11:09:54.572Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-21 → 2026-10-23 (scopes)_

_1 session(s) also served other batches — their session-level figures are split evenly; 8 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-22T11:33:00Z (3 run record(s))
- Findings reported: 2  ·  fix rounds: 2

## What it cost

- Total: $20.20  ·  3.3h active (cases 52m · lead 118m · stages 26m)  ·  22 dispatches
- Tokens: total 45,102,497  ·  **real work 385,417** (in 200,278 / out 185,139)  ·  cache 40.0M read / 4.7M write  ·  **cache hit rate 89.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 72 turns  ·  339 tool calls (13 err, 96% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $11.54 (57%)
  - by stage: lead $8.50 · triage $0.18 (1m) · gate $0.67 (6m) · report $0.54 (1m) · other $1.65 (19m)
- Rework (fix rounds — already inside per-case direct): $1.05  ·  2 dispatch(es)  ·  9m
- **Per delivered case (incl. overhead): $20.20**
- Avg direct per case (excl. overhead): $8.65
- Direct cost spread: avg $8.65 · median $8.65 · min $8.65 · max $8.65
- Loaded cost spread (direct + even overhead share): avg $20.19 · median $20.19 · min $20.19 · max $20.19
- Active-time spread: avg 52m · median 52m · min 52m · max 52m  ·  loaded: avg 196m · median 196m · min 196m · max 196m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2757 | automated | $8.65 | $20.19 | 236,299 (in 122k / out 114k) | 52m | 196m | 15 | 202 (5) | 2 | 2 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $8.50 | 0 | 69,641 (in 36k / out 34k) | 81.8% | 118m | 70 (4) |
| test-automation-engineer | $6.46 | 12 | 172,354 (in 96k / out 76k) | 93.2% | 51m | 156 (5) |
| qa-engineer | $5.23 | 10 | 143,424 (in 69k / out 75k) | 90.0% | 28m | 113 (5) |
