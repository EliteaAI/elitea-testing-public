# Batch cost — chat-stop-generation-2183

Generated: 2026-10-20T21:50:48.120Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-20T22:30:00Z (1 run record(s))
- Findings reported: 3  ·  fix rounds: 0

## What it cost

- Total: $3.15  ·  0.6h active (cases 17m · lead 20m · stages 0m)  ·  6 dispatches
- Tokens: total 5,984,457  ·  **real work 64,998** (in 40,000 / out 24,998)  ·  cache 5.1M read / 800k write  ·  **cache hit rate 85.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 20 turns  ·  56 tool calls (3 err, 95% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.21 (38%)
  - by stage: lead $1.21 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $3.15**
- Avg direct per case (excl. overhead): $1.94
- Direct cost spread: avg $1.94 · median $1.94 · min $1.94 · max $1.94
- Loaded cost spread (direct + even overhead share): avg $3.15 · median $3.15 · min $3.15 · max $3.15
- Active-time spread: avg 17m · median 17m · min 17m · max 17m  ·  loaded: avg 37m · median 37m · min 37m · max 37m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2183 | automated | $1.94 | $3.15 | 43,014 (in 26k / out 17k) | 17m | 37m | 4 | 35 (1) | 0 | 3 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.21 | 0 | 21,984 (in 14k / out 8k) | 85.7% | 20m | 21 (2) |
| qa-engineer | $1.05 | 3 | 29,011 (in 17k / out 12k) | 86.7% | 9m | 20 (1) |
| test-automation-engineer | $0.89 | 3 | 14,003 (in 8k / out 6k) | 85.1% | 8m | 15 (0) |
