# Batch cost — adjust-1795

Generated: 2026-10-25T06:11:55.844Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-24 → 2026-10-26 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `not-run` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.63  ·  0.3h active (cases 0m · lead 18m · stages 0m)  ·  1 dispatches
- Tokens: total 6,419,546  ·  **real work 43,115** (in 22,020 / out 21,095)  ·  cache 6.1M read / 245k write  ·  **cache hit rate 95.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  51 tool calls (1 err, 98% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.25 (77%)
- **Per delivered case (incl. overhead): $1.63**
- Avg direct per case (excl. overhead): $0.38
- Direct cost spread: avg $0.38 · median $0.38 · min $0.38 · max $0.38
- Loaded cost spread (direct + even overhead share): avg $1.63 · median $1.63 · min $1.63 · max $1.63
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 18m · median 18m · min 18m · max 18m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1795 | automated | $0.38 | $1.63 | 12,564 (in 10k / out 2k) | 0m | 18m | 1 | 3 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.25 | 0 | 30,551 (in 12k / out 19k) | 97.6% | 18m | 48 (1) |
| qa-engineer | $0.38 | 1 | 12,564 (in 10k / out 2k) | 62.6% | 0m | 3 (0) |
