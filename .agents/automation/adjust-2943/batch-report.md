# Batch cost — adjust-2943

Generated: 2026-11-12T11:59:50.270Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-11 → 2026-11-13 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3/3 (2 params each) runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $3.26  ·  0.9h active (cases 23m · lead 29m · stages 0m)  ·  2 dispatches
- Tokens: total 11,900,039  ·  **real work 88,867** (in 31,670 / out 57,197)  ·  cache 11.3M read / 478k write  ·  **cache hit rate 95.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 12 turns  ·  77 tool calls (2 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $0.77 (24%)
- **Per delivered case (incl. overhead): $3.26**
- Avg direct per case (excl. overhead): $2.49
- Direct cost spread: avg $2.49 · median $2.49 · min $2.49 · max $2.49
- Loaded cost spread (direct + even overhead share): avg $3.26 · median $3.26 · min $3.26 · max $3.26
- Active-time spread: avg 23m · median 23m · min 23m · max 23m  ·  loaded: avg 52m · median 52m · min 52m · max 52m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3744 | automated | $2.49 | $3.26 | 72,069 (in 21k / out 51k) | 23m | 52m | 2 | 65 (2) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $2.08 | 1 | 56,552 (in 10k / out 46k) | 98.1% | 22m | 59 (2) |
| test-automation-lead | $0.77 | 0 | 16,798 (in 11k / out 6k) | 84.4% | 29m | 12 (0) |
| qa-engineer | $0.41 | 1 | 15,517 (in 11k / out 5k) | 81.7% | 1m | 6 (0) |
