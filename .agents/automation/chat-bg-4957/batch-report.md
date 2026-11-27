# Batch cost — chat-bg-4957

Generated: 2026-11-27T13:41:12.744Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (1 run record(s))
- Findings reported: 2  ·  fix rounds: 0

## What it cost

- Total: $4.72  ·  1.5h active (cases 40m · lead 51m · stages 0m)  ·  6 dispatches
- Tokens: total 12,032,402  ·  **real work 91,300** (in 41,488 / out 49,812)  ·  cache 10.7M read / 1.2M write  ·  **cache hit rate 89.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 26 turns  ·  93 tool calls (3 err, 97% ok)
- Overhead (lead + triage + gate + report, shown once): $2.31 (49%)
  - by stage: lead $2.31 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $4.72**
- Avg direct per case (excl. overhead): $2.41
- Direct cost spread: avg $2.41 · median $2.41 · min $2.41 · max $2.41
- Loaded cost spread (direct + even overhead share): avg $4.72 · median $4.72 · min $4.72 · max $4.72
- Active-time spread: avg 40m · median 40m · min 40m · max 40m  ·  loaded: avg 91m · median 91m · min 91m · max 91m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4957 | automated | $2.41 | $4.72 | 68,305 (in 27k / out 42k) | 40m | 91m | 4 | 68 (0) | 0 | 2 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $2.31 | 0 | 22,995 (in 15k / out 8k) | 74.4% | 51m | 25 (3) |
| qa-engineer | $1.57 | 3 | 45,897 (in 18k / out 28k) | 94.7% | 25m | 45 (0) |
| test-automation-engineer | $0.83 | 3 | 22,408 (in 9k / out 14k) | 94.8% | 15m | 23 (0) |
