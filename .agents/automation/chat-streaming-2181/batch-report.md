# Batch cost — chat-streaming-2181

Generated: 2026-10-22T04:58:46.627Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-23 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-22T04:58:45Z (1 run record(s))
- Findings reported: 24  ·  fix rounds: 4

## What it cost

- Total: $14.21  ·  3.0h active (cases 78m · lead 94m · stages 8m)  ·  19 dispatches
- Tokens: total 31,405,383  ·  **real work 379,345** (in 231,394 / out 147,951)  ·  cache 27.8M read / 3.3M write  ·  **cache hit rate 88.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 55 turns  ·  240 tool calls (10 err, 96% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $6.05 (43%)
  - by stage: lead $4.35 · triage $0.33 (0m) · gate $0.60 (4m) · report $0.45 (1m) · other $0.33 (3m)
- Rework (fix rounds — already inside per-case direct): $2.53  ·  4 dispatch(es)  ·  42m
- **Per delivered case (incl. overhead): $14.21**
- Avg direct per case (excl. overhead): $8.16
- Direct cost spread: avg $8.16 · median $8.16 · min $8.16 · max $8.16
- Loaded cost spread (direct + even overhead share): avg $14.21 · median $14.21 · min $14.21 · max $14.21
- Active-time spread: avg 78m · median 78m · min 78m · max 78m  ·  loaded: avg 180m · median 180m · min 180m · max 180m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2181 | automated | $8.16 | $14.21 | 280,159 (in 172k / out 108k) | 78m | 180m | 13 | 155 (4) | 4 | 24 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $5.82 | 11 | 203,932 (in 131k / out 73k) | 91.6% | 65m | 123 (4) |
| test-automation-lead | $4.35 | 0 | 48,986 (in 23k / out 26k) | 87.4% | 94m | 57 (3) |
| qa-engineer | $4.04 | 8 | 126,427 (in 77k / out 49k) | 84.2% | 21m | 60 (3) |
