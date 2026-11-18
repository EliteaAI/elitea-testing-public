# Batch cost — elitea-4715

Generated: 2026-11-18T11:35:52.111Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-17 → 2026-11-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (passed 18.99s,passed 18.27s,passed 19.19s runs)
- Gate record (script-authored): green at 2026-11-18T11:40:00Z (1 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $4.71  ·  0.8h active (cases 16m · lead 29m · stages 0m)  ·  6 dispatches
- Tokens: total 12,911,491  ·  **real work 102,405** (in 40,507 / out 61,898)  ·  cache 11.9M read / 950k write  ·  **cache hit rate 92.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  95 tool calls (5 err, 95% ok)
- Overhead (lead + triage + gate + report, shown once): $1.74 (37%)
  - by stage: lead $1.74 · triage n/a (0m) · report n/a (0m)
- **Per delivered case (incl. overhead): $4.71**
- Avg direct per case (excl. overhead): $2.97
- Direct cost spread: avg $2.97 · median $2.97 · min $2.97 · max $2.97
- Loaded cost spread (direct + even overhead share): avg $4.71 · median $4.71 · min $4.71 · max $4.71
- Active-time spread: avg 16m · median 16m · min 16m · max 16m  ·  loaded: avg 45m · median 45m · min 45m · max 45m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4715 | automated | $2.97 | $4.71 | 77,759 (in 26k / out 52k) | 16m | 45m | 4 | 68 (2) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $1.80 | 3 | 50,642 (in 17k / out 33k) | 94.0% | 9m | 39 (0) |
| test-automation-lead | $1.74 | 0 | 24,646 (in 15k / out 10k) | 84.3% | 29m | 27 (3) |
| test-automation-engineer | $1.17 | 3 | 27,117 (in 9k / out 19k) | 95.8% | 7m | 29 (2) |
