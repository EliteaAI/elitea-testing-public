# Batch cost — adjust-2059-2574

Generated: 2026-10-23T05:47:26.841Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-10-24 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $3.09  ·  0.8h active (cases 11m · lead 34m · stages 0m)  ·  2 dispatches
- Tokens: total 11,048,618  ·  **real work 73,372** (in 33,101 / out 40,271)  ·  cache 10.5M read / 516k write  ·  **cache hit rate 95.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  86 tool calls (0 err, 100% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $1.69 (55%)
- **Per delivered case (incl. overhead): $1.54**
- Avg direct per case (excl. overhead): $1.39
- Direct cost spread: avg $1.39 · median $1.39 · min $1.39 · max $1.39
- Loaded cost spread (direct + even overhead share): avg $1.55 · median $1.55 · min $0.85 · max $2.24
- Active-time spread: avg 11m · median 11m · min 11m · max 11m  ·  loaded: avg 23m · median 23m · min 17m · max 28m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2059 | automated | $1.39 | $2.24 | 38,704 (in 21k / out 18k) | 11m | 28m | 2 | 36 (0) | 0 | 0 |
| ELITEA-2066 | automated | n/a | $0.85 | 0 (incl. cache) | 0m | 17m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.69 | 0 | 34,668 (in 12k / out 22k) | 95.7% | 34m | 50 (0) |
| test-automation-engineer | $0.98 | 1 | 23,511 (in 10k / out 13k) | 95.9% | 10m | 29 (0) |
| qa-engineer | $0.41 | 1 | 15,193 (in 10k / out 5k) | 81.8% | 1m | 7 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2066
