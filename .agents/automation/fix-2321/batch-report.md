# Batch cost — fix-2321

Generated: 2026-09-16T14:36:02.980Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-15 → 2026-09-17 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $12.01  ·  0.5h active (cases 9m · lead 19m · stages 0m)  ·  2 dispatches
- Tokens: total 12,806,424  ·  **real work 70,718** (in 146 / out 70,572)  ·  cache 12.2M read / 539k write  ·  **cache hit rate 95.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 41 turns  ·  71 tool calls (0 err, 100% ok)  ·  skills: sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $6.71 (56%)
- Rework (fix rounds — already inside per-case direct): $3.28  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $12.01**
- Avg direct per case (excl. overhead): $5.30
- Direct cost spread: avg $5.30 · median $5.30 · min $5.30 · max $5.30
- Loaded cost spread (direct + even overhead share): avg $12.01 · median $12.01 · min $12.01 · max $12.01
- Active-time spread: avg 9m · median 9m · min 9m · max 9m  ·  loaded: avg 28m · median 28m · min 28m · max 28m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2056 | automated | $5.30 | $12.01 | 36,430 (in 64 / out 36k) | 9m | 28m | 2 | 30 (0) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $6.71 | 0 | 34,288 (in 82 / out 34k) | 97.3% | 19m | 41 (0) |
| test-automation-engineer | $3.28 | 1 | 19,941 (in 46 / out 20k) | 95.2% | 5m | 22 (0) |
| qa-engineer | $2.01 | 1 | 16,489 (in 18 / out 16k) | 88.4% | 4m | 8 (0) |
