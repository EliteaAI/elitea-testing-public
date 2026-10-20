# Batch cost — skills-builder-chat

Generated: 2026-10-20T09:10:25.406Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 31  ·  fix rounds: 0

## What it cost

- Total: $59.17  ·  7.3h active (cases 192m · lead 234m · stages 9m)  ·  19 dispatches
- Tokens: total 156,438,399  ·  **real work 633,752** (in 238,858 / out 394,894)  ·  cache 146.2M read / 9.6M write  ·  **cache hit rate 93.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 97 turns  ·  730 tool calls (36 err, 95% ok)  ·  skills: memory, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $21.63 (37%)
  - by stage: lead $19.84 · triage $0.54 (1m) · gate $0.76 (7m) · report $0.48 (1m)
- **Per delivered case (incl. overhead): $29.59**
- Avg direct per case (excl. overhead): $12.51
- Direct cost spread: avg $12.51 · median $2.77 · min $2.44 · max $32.33
- Loaded cost spread (direct + even overhead share): avg $19.72 · median $9.98 · min $9.65 · max $39.54
- Active-time spread: avg 64m · median 46m · min 18m · max 128m  ·  loaded: avg 145m · median 127m · min 99m · max 209m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3366 | automated | $32.33 | $39.54 | 399,235 (in 126k / out 274k) | 128m | 209m | 7 | 488 (21) | 0 | 14 |
| ELITEA-3367 | blocked | $2.44 | $9.65 | 44,963 (in 17k / out 28k) | 46m | 127m | 2 | 52 (2) | 0 | 3 |
| ELITEA-3316 | automated | $2.77 | $9.98 | 79,677 (in 47k / out 33k) | 18m | 99m | 5 | 65 (7) | 0 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $26.10 | 9 | 305,274 (in 112k / out 193k) | 98.1% | 97m | 378 (16) |
| test-automation-lead | $19.84 | 0 | 67,820 (in 24k / out 44k) | 69.7% | 234m | 92 (4) |
| qa-engineer | $13.24 | 10 | 260,658 (in 103k / out 157k) | 95.6% | 104m | 260 (16) |
