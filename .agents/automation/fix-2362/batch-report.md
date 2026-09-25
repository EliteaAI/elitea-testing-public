# Batch cost — fix-2362

Generated: 2026-09-18T13:00:25.174Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-17 → 2026-09-19 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $21.78  ·  1.3h active (cases 37m · lead 40m · stages 0m)  ·  2 dispatches
- Tokens: total 23,109,306  ·  **real work 118,431** (in 240 / out 118,191)  ·  cache 21.9M read / 1.1M write  ·  **cache hit rate 95.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  116 tool calls (6 err, 95% ok)  ·  skills: sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $7.54 (35%)
- **Per delivered case (incl. overhead): $21.78**
- Avg direct per case (excl. overhead): $14.24
- Direct cost spread: avg $14.24 · median $14.24 · min $14.24 · max $14.24
- Loaded cost spread (direct + even overhead share): avg $21.78 · median $21.78 · min $21.78 · max $21.78
- Active-time spread: avg 37m · median 37m · min 37m · max 37m  ·  loaded: avg 77m · median 77m · min 77m · max 77m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1140 | automated | $14.24 | $21.78 | 77,427 (in 146 / out 77k) | 37m | 77m | 2 | 69 (5) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $11.22 | 1 | 57,200 (in 110 / out 57k) | 93.4% | 32m | 52 (4) |
| test-automation-lead | $7.54 | 0 | 41,004 (in 94 / out 41k) | 97.6% | 40m | 47 (1) |
| qa-engineer | $3.01 | 1 | 20,227 (in 36 / out 20k) | 93.6% | 5m | 17 (1) |
