# Batch cost — adjust-2720

Generated: 2026-10-27T06:18:07.378Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-10-26 → 2026-10-28 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 1**  ·  blocked 2  ·  automated 1
- Gate: sanctioned-red
- Gate record (script-authored): sanctioned-red at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 0.99

## What it cost

- Total: $2.99  ·  0.9h active (cases 16m · lead 37m · stages 1m)  ·  3 dispatches
- Tokens: total 8,913,739  ·  **real work 81,904** (in 42,372 / out 39,532)  ·  cache 8.3M read / 564k write  ·  **cache hit rate 93.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 38 turns  ·  72 tool calls (1 err, 99% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $1.77 (59%)
  - by stage: lead $1.43 · other $0.34 (1m)
- Rework (fix rounds — already inside per-case direct): $0.86  ·  1 dispatch(es)  ·  14m
- **Per delivered case (incl. overhead): $2.99**
- Avg direct per case (excl. overhead): $0.41
- Direct cost spread: avg $0.41 · median $0.29 · min $0.29 · max $0.65
- Loaded cost spread (direct + even overhead share): avg $1.00 · median $0.88 · min $0.88 · max $1.24
- Active-time spread: avg 5m · median 5m · min 5m · max 6m  ·  loaded: avg 18m · median 18m · min 18m · max 19m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2007 | automated | $0.29 | $0.88 | 7,818 (in 3k / out 4k) | 5m | 18m | 0.33 | 7 (0) | 0.33 | 0 |
| ELITEA-2042 | blocked | $0.29 | $0.88 | 7,818 (in 3k / out 4k) | 5m | 18m | 0.33 | 7 (0) | 0.33 | 0 |
| ELITEA-2045 | blocked | $0.65 | $1.24 | 21,750 (in 14k / out 8k) | 6m | 19m | 1.33 | 12 (0) | 0.33 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $1.43 | 0 | 30,819 (in 11k / out 20k) | 94.6% | 37m | 41 (1) |
| test-automation-engineer | $1.22 | 2 | 37,386 (in 21k / out 17k) | 93.1% | 15m | 27 (0) |
| qa-engineer | $0.34 | 1 | 13,699 (in 10k / out 3k) | 78.2% | 1m | 4 (0) |
