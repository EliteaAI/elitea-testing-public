# Batch cost — fix-2758-scroll-timeout

Generated: 2026-10-30T07:00:16.804Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-29 → 2026-10-31 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.52  ·  1.4h active (cases 39m · lead 45m · stages 0m)  ·  2 dispatches
- Tokens: total 19,987,206  ·  **real work 171,311** (in 36,134 / out 135,177)  ·  cache 18.8M read / 1.0M write  ·  **cache hit rate 94.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 43 turns  ·  129 tool calls (4 err, 97% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $2.18 (33%)
- **Per delivered case (incl. overhead): $3.26**
- Avg direct per case (excl. overhead): $1.45
- Direct cost spread: avg $1.45 · median $1.45 · min $1.45 · max $1.45
- Loaded cost spread (direct + even overhead share): avg $2.18 · median $2.18 · min $2.18 · max $2.18
- Active-time spread: avg 13m · median 13m · min 13m · max 13m  ·  loaded: avg 28m · median 28m · min 28m · max 28m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2064 | automated | $1.45 | $2.18 | 45,542 (in 7k / out 38k) | 13m | 28m | 0.67 | 27 (1) | 0 | 0 |
| ELITEA-2037 | automated | $1.45 | $2.18 | 45,542 (in 7k / out 38k) | 13m | 28m | 0.67 | 27 (1) | 0 | 0 |
| ELITEA-2010 | blocked | $1.45 | $2.18 | 45,542 (in 7k / out 38k) | 13m | 28m | 0.67 | 27 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.09 | 1 | 87,989 (in 11k / out 77k) | 95.4% | 31m | 54 (1) |
| test-automation-lead | $2.18 | 0 | 34,685 (in 14k / out 20k) | 92.4% | 45m | 47 (2) |
| qa-engineer | $1.26 | 1 | 48,637 (in 11k / out 38k) | 96.1% | 8m | 28 (1) |
