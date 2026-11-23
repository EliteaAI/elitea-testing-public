# Batch cost — modules-save-as-version-4792

Generated: 2026-11-23T20:07:40.610Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-22 → 2026-11-24 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-11-23T20:07:38Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.54  ·  0.5h active (cases 10m · lead 22m · stages 0m)  ·  6 dispatches
- Tokens: total 5,709,347  ·  **real work 62,558** (in 40,040 / out 22,518)  ·  cache 5.0M read / 697k write  ·  **cache hit rate 87.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 16 turns  ·  50 tool calls (1 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $0.97 (38%)
  - by stage: lead $0.97 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $2.54**
- Avg direct per case (excl. overhead): $1.57
- Direct cost spread: avg $1.57 · median $1.57 · min $1.57 · max $1.57
- Loaded cost spread (direct + even overhead share): avg $2.54 · median $2.54 · min $2.54 · max $2.54
- Active-time spread: avg 10m · median 10m · min 10m · max 10m  ·  loaded: avg 32m · median 32m · min 32m · max 32m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4792 | automated | $1.57 | $2.54 | 42,683 (in 26k / out 17k) | 10m | 32m | 4 | 34 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $0.98 | 3 | 27,526 (in 17k / out 10k) | 86.8% | 3m | 19 (0) |
| test-automation-lead | $0.97 | 0 | 19,875 (in 14k / out 6k) | 82.2% | 22m | 16 (1) |
| test-automation-engineer | $0.59 | 3 | 15,157 (in 9k / out 7k) | 91.9% | 7m | 15 (0) |
