# Batch cost — builder-modules-chat-2459

Generated: 2026-10-30T11:47:22.238Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-18 → 2026-10-31 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 1**  ·  automated 1  ·  not-started 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- ⚠️ **OUTCOME DRIFT** (1): ELITEA-3372 receipt=not-started declared=blocked — reconcile report.json
- Findings reported: 1  ·  fix rounds: 5

## What it cost

- Total: $153.01  ·  20.9h active (cases 521m · lead 655m · stages 80m)  ·  25 dispatches
- Tokens: total 466,581,463  ·  **real work 2,235,209** (in 577,435 / out 1,657,774)  ·  cache 450.5M read / 13.9M write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 284 turns  ·  2026 tool calls (73 err, 96% ok)  ·  skills: memory, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $50.66 (33%)
  - by stage: lead $31.14 · triage $0.17 (1m) · gate $4.89 (19m) · report $0.19 (1m) · other $14.28 (59m)
- Rework (fix rounds — already inside per-case direct): $24.98  ·  5 dispatch(es)  ·  153m
- **Per delivered case (incl. overhead): $153.01**
- Avg direct per case (excl. overhead): $51.18
- Direct cost spread: avg $51.18 · median $51.18 · min $33.17 · max $69.18
- Loaded cost spread (direct + even overhead share): avg $76.51 · median $76.51 · min $58.50 · max $94.51
- Active-time spread: avg 261m · median 261m · min 161m · max 360m  ·  loaded: avg 629m · median 629m · min 529m · max 728m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3370 | automated | $33.17 | $58.50 | 648,124 (in 222k / out 427k) | 161m | 529m | 10.5 | 541 (16) | 2.5 | 1 |
| ELITEA-3372 | not-started | $69.18 | $94.51 | 987,339 (in 176k / out 811k) | 360m | 728m | 6.5 | 817 (31) | 2.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $97.20 | 19 | 1,644,848 (in 396k / out 1.2M) | 97.5% | 507m | 1351 (62) |
| test-automation-lead | $31.14 | 0 | 180,436 (in 51k / out 129k) | 92.9% | 655m | 280 (5) |
| qa-engineer | $24.67 | 6 | 409,925 (in 131k / out 279k) | 98.5% | 94m | 395 (6) |
