# Batch cost — adjust-4953

Generated: 2026-11-27T18:39:46.086Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-26 → 2026-11-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 1  ·  fix rounds: 1

## What it cost

- Total: $11.83  ·  2.2h active (cases 58m · lead 74m · stages 1m)  ·  11 dispatches
- Tokens: total 35,885,900  ·  **real work 284,087** (in 110,084 / out 174,003)  ·  cache 33.0M read / 2.6M write  ·  **cache hit rate 92.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 61 turns  ·  243 tool calls (12 err, 95% ok)  ·  skills: memory, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $4.95 (42%)
  - by stage: lead $4.62 · triage n/a (0m) · report n/a (0m) · other $0.33 (1m)
- Rework (fix rounds — already inside per-case direct): $0.93  ·  1 dispatch(es)  ·  9m
- **Per delivered case (incl. overhead): $11.83**
- Avg direct per case (excl. overhead): $6.88
- Direct cost spread: avg $6.88 · median $6.88 · min $6.88 · max $6.88
- Loaded cost spread (direct + even overhead share): avg $11.83 · median $11.83 · min $11.83 · max $11.83
- Active-time spread: avg 58m · median 58m · min 58m · max 58m  ·  loaded: avg 133m · median 133m · min 133m · max 133m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4953 | automated | $6.88 | $11.83 | 222,933 (in 82k / out 141k) | 58m | 133m | 8 | 178 (7) | 1 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $4.62 | 0 | 47,232 (in 17k / out 30k) | 84.1% | 74m | 59 (5) |
| test-automation-engineer | $4.25 | 5 | 127,044 (in 41k / out 86k) | 96.0% | 37m | 111 (4) |
| qa-engineer | $2.96 | 6 | 109,811 (in 52k / out 58k) | 93.4% | 22m | 73 (3) |
