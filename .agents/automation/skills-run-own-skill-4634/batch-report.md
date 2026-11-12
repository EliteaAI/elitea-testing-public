# Batch cost — skills-run-own-skill-4634

Generated: 2026-11-11T17:05:43.029Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at 2026-11-11T17:05:41Z (3 run record(s))
- Findings reported: 14  ·  fix rounds: 1

## What it cost

- Total: $8.17  ·  1.4h active (cases 36m · lead 48m · stages 1m)  ·  13 dispatches
- Tokens: total 17,932,238  ·  **real work 185,137** (in 105,787 / out 79,350)  ·  cache 15.8M read / 1.9M write  ·  **cache hit rate 88.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 24 turns  ·  147 tool calls (4 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $2.93 (36%)
  - by stage: lead $2.19 · triage $0.33 (0m) · report $0.41 (1m)
- Rework (fix rounds — already inside per-case direct): $0.46  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $8.17**
- Avg direct per case (excl. overhead): $5.23
- Direct cost spread: avg $5.23 · median $5.23 · min $5.23 · max $5.23
- Loaded cost spread (direct + even overhead share): avg $8.16 · median $8.16 · min $8.16 · max $8.16
- Active-time spread: avg 36m · median 36m · min 36m · max 36m  ·  loaded: avg 85m · median 85m · min 85m · max 85m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4634 | automated | $5.23 | $8.16 | 136,990 (in 71k / out 66k) | 36m | 85m | 9 | 116 (3) | 1 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $3.40 | 7 | 93,855 (in 54k / out 40k) | 88.8% | 17m | 62 (3) |
| test-automation-engineer | $2.57 | 6 | 64,321 (in 34k / out 30k) | 93.0% | 20m | 60 (0) |
| test-automation-lead | $2.19 | 0 | 26,961 (in 18k / out 9k) | 75.9% | 48m | 25 (1) |
