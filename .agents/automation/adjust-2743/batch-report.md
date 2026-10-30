# Batch cost — adjust-2743

Generated: 2026-10-27T08:06:42.856Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-26 → 2026-10-28 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: sanctioned-red (3 runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `sanctioned-red` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $1.31  ·  0.4h active (cases 0m · lead 22m · stages 0m)  ·  1 dispatches
- Tokens: total 4,199,698  ·  **real work 41,727** (in 21,601 / out 20,126)  ·  cache 3.9M read / 220k write  ·  **cache hit rate 94.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 31 turns  ·  35 tool calls (1 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.92 (70%)
- **Per delivered case (incl. overhead): $1.31**
- Avg direct per case (excl. overhead): $0.39
- Direct cost spread: avg $0.39 · median $0.39 · min $0.39 · max $0.39
- Loaded cost spread (direct + even overhead share): avg $1.31 · median $1.31 · min $1.31 · max $1.31
- Active-time spread: avg 0m · median 0m · min 0m · max 0m  ·  loaded: avg 22m · median 22m · min 22m · max 22m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2360 | automated | $0.39 | $1.31 | 12,932 (in 10k / out 2k) | 0m | 22m | 1 | 3 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.92 | 0 | 28,795 (in 11k / out 18k) | 97.0% | 22m | 32 (1) |
| qa-engineer | $0.39 | 1 | 12,932 (in 10k / out 2k) | 62.6% | 0m | 3 (0) |
