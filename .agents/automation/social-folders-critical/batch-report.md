# Batch cost — social-folders-critical

Generated: 2026-09-15T15:48:51.055Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-haiku-4-5-20251001, claude-opus-5

_window 2026-09-14 → 2026-09-16 (scopes)_

## What happened

- Cases: 3  ·  **delivered: 3**  ·  automated 3
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-09-15T14:50:26.717Z (4 run record(s))
- Findings reported: 69  ·  fix rounds: 3

## What it cost

- Total: $66.04  ·  4.1h active (cases 94m · lead 135m · stages 15m)  ·  12 dispatches
- Tokens: total 85,753,479  ·  **real work 418,531** (in 941 / out 417,590)  ·  cache 82.8M read / 2.6M write  ·  **cache hit rate 97.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 89 turns  ·  413 tool calls (25 err, 94% ok)  ·  skills: sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $19.42 (29%)
  - by stage: lead $14.70 · triage $0.21 (1m) · gate $2.37 (7m) · report $0.30 (4m) · other $1.84 (3m)
- Rework (fix rounds — already inside per-case direct): $8.99  ·  3 dispatch(es)  ·  20m
- **Per delivered case (incl. overhead): $22.01**
- Avg direct per case (excl. overhead): $15.54
- Direct cost spread: avg $15.54 · median $11.21 · min $11.21 · max $24.19
- Loaded cost spread (direct + even overhead share): avg $22.01 · median $17.68 · min $17.68 · max $30.66
- Active-time spread: avg 31m · median 21m · min 21m · max 52m  ·  loaded: avg 81m · median 71m · min 71m · max 102m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-3208 | automated | $24.19 | $30.66 | 153,242 (in 324 / out 153k) | 52m | 102m | 5.33 | 148 (9) | 3 | 23 |
| ELITEA-3209 | automated | $11.21 | $17.68 | 71,361 (in 156 / out 71k) | 21m | 71m | 1.33 | 68 (4) | 0 | 23 |
| ELITEA-3210 | automated | $11.21 | $17.68 | 71,361 (in 156 / out 71k) | 21m | 71m | 1.33 | 68 (4) | 0 | 23 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $33.69 | 7 | 219,203 (in 510 / out 219k) | 97.1% | 80m | 210 (16) |
| qa-engineer | $17.65 | 5 | 124,837 (in 253 / out 125k) | 95.3% | 30m | 114 (6) |
| test-automation-lead | $14.70 | 0 | 74,491 (in 178 / out 74k) | 98.4% | 135m | 89 (3) |
