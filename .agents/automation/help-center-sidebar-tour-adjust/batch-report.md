# Batch cost — help-center-sidebar-tour-adjust

Generated: 2026-11-10T09:24:14.810Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-09 → 2026-11-11 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.75  ·  0.2h active (cases 1m · lead 11m · stages 0m)  ·  1 dispatches
- Tokens: total 6,134,373  ·  **real work 46,067** (in 21,669 / out 24,398)  ·  cache 5.8M read / 282k write  ·  **cache hit rate 95.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 39 turns  ·  52 tool calls (4 err, 92% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.32 (75%)
- **Per delivered case (incl. overhead): $1.75**
- Avg direct per case (excl. overhead): $0.43
- Direct cost spread: avg $0.43 · median $0.43 · min $0.43 · max $0.43
- Loaded cost spread (direct + even overhead share): avg $1.75 · median $1.75 · min $1.75 · max $1.75
- Active-time spread: avg 1m · median 1m · min 1m · max 1m  ·  loaded: avg 12m · median 12m · min 12m · max 12m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3754 | automated | $0.43 | $1.75 | 13,546 (in 10k / out 3k) | 1m | 12m | 1 | 6 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.32 | 0 | 32,521 (in 11k / out 21k) | 96.7% | 11m | 46 (4) |
| qa-engineer | $0.43 | 1 | 13,546 (in 10k / out 3k) | 81.4% | 1m | 6 (0) |
