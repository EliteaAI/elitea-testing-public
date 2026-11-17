# Batch cost — adjust-elitea-2184

Generated: 2026-11-17T19:16:45.499Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-16 → 2026-11-18 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $2.36  ·  0.5h active (cases 7m · lead 20m · stages 0m)  ·  2 dispatches
- Tokens: total 5,843,974  ·  **real work 57,618** (in 31,832 / out 25,786)  ·  cache 5.3M read / 510k write  ·  **cache hit rate 90.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 26 turns  ·  46 tool calls (3 err, 93% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.23 (52%)
- **Per delivered case (incl. overhead): $1.18**
- Avg direct per case (excl. overhead): $1.13
- Direct cost spread: avg $1.13 · median $1.13 · min $1.13 · max $1.13
- Loaded cost spread (direct + even overhead share): avg $1.19 · median $1.19 · min $0.62 · max $1.75
- Active-time spread: avg 7m · median 7m · min 7m · max 7m  ·  loaded: avg 14m · median 14m · min 10m · max 17m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2184 | automated | $1.13 | $1.75 | 34,856 (in 21k / out 14k) | 7m | 17m | 2 | 19 (2) | 0 | 0 |
| ELITEA-2187 | automated | n/a | $0.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.23 | 0 | 22,762 (in 11k / out 12k) | 91.4% | 20m | 27 (1) |
| test-automation-engineer | $0.77 | 1 | 21,163 (in 10k / out 11k) | 91.9% | 6m | 14 (2) |
| qa-engineer | $0.36 | 1 | 13,693 (in 11k / out 3k) | 82.5% | 1m | 5 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2187
