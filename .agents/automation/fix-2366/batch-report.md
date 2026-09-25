# Batch cost — fix-2366

Generated: 2026-09-18T14:28:07.915Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-17 → 2026-09-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: undefined ([object Object],[object Object],[object Object] runs)
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $35.85  ·  1.4h active (cases 51m · lead 32m · stages 0m)  ·  4 dispatches
- Tokens: total 46,548,175  ·  **real work 215,173** (in 424 / out 214,749)  ·  cache 45.2M read / 1.1M write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 88 turns  ·  208 tool calls (8 err, 96% ok)
- Overhead (lead + triage + gate + report, shown once): $14.36 (40%)
- Rework (fix rounds — already inside per-case direct): $2.06  ·  1 dispatch(es)  ·  3m
- **Per delivered case (incl. overhead): $35.85**
- Avg direct per case (excl. overhead): $21.48
- Direct cost spread: avg $21.48 · median $21.48 · min $21.48 · max $21.48
- Loaded cost spread (direct + even overhead share): avg $35.84 · median $35.84 · min $35.84 · max $35.84
- Active-time spread: avg 51m · median 51m · min 51m · max 51m  ·  loaded: avg 83m · median 83m · min 83m · max 83m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2056 | automated | $21.48 | $35.84 | 149,234 (in 248 / out 149k) | 51m | 83m | 4 | 120 (4) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $17.01 | 2 | 112,823 (in 206 / out 113k) | 98.0% | 43m | 101 (4) |
| test-automation-lead | $14.36 | 0 | 65,939 (in 176 / out 66k) | 98.6% | 32m | 88 (4) |
| qa-engineer | $4.47 | 2 | 36,411 (in 42 / out 36k) | 89.7% | 8m | 19 (0) |
