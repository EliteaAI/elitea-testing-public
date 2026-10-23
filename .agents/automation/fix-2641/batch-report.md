# Batch cost — fix-2641

Generated: 2026-10-23T12:41:44.210Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-22 → 2026-10-24 (scopes)_

## What happened

- Cases: 2  ·  **delivered: 2**  ·  merged-sanctioned-red 2
- Gate: sanctioned-red
- Gate record (script-authored): sanctioned-red at 2026-10-23T12:00:00Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $1.93  ·  0.4h active (cases 5m · lead 19m · stages 0m)  ·  2 dispatches
- Tokens: total 5,587,339  ·  **real work 57,577** (in 31,864 / out 25,713)  ·  cache 5.2M read / 366k write  ·  **cache hit rate 92.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 29 turns  ·  48 tool calls (1 err, 98% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $0.95 (49%)
- Rework (fix rounds — already inside per-case direct): $0.62  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $0.96**
- Avg direct per case (excl. overhead): $0.49
- Direct cost spread: avg $0.49 · median $0.49 · min $0.31 · max $0.67
- Loaded cost spread (direct + even overhead share): avg $0.96 · median $0.96 · min $0.78 · max $1.14
- Active-time spread: avg 3m · median 3m · min 2m · max 3m  ·  loaded: avg 13m · median 13m · min 12m · max 13m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2356 | merged-sanctioned-red | $0.67 | $1.14 | 23,397 (in 16k / out 8k) | 3m | 13m | 1.5 | 11 (0) | 0.5 | 0 |
| ELITEA-2357 | merged-sanctioned-red | $0.31 | $0.78 | 9,067 (in 5k / out 4k) | 2m | 12m | 0.5 | 6 (0) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $0.95 | 0 | 25,114 (in 11k / out 14k) | 95.8% | 19m | 31 (1) |
| test-automation-engineer | $0.62 | 1 | 18,133 (in 10k / out 8k) | 90.4% | 4m | 12 (0) |
| qa-engineer | $0.36 | 1 | 14,330 (in 10k / out 4k) | 77.9% | 1m | 5 (0) |
