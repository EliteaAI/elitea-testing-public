# Batch cost — fix-2287-elitea-1901

Generated: 2026-09-14T21:09:57.325Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-13 → 2026-09-15 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (9 runs)
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: $10.80  ·  0.4h active (cases 3m · lead 19m · stages 0m)  ·  2 dispatches
- Tokens: total 11,742,207  ·  **real work 53,306** (in 134 / out 53,172)  ·  cache 11.2M read / 499k write  ·  **cache hit rate 95.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  65 tool calls (4 err, 94% ok)
- Overhead (lead + triage + gate + report, shown once): $7.37 (68%)
- **Per delivered case (incl. overhead): $10.80**
- Avg direct per case (excl. overhead): $3.43
- Direct cost spread: avg $3.43 · median $3.43 · min $3.43 · max $3.43
- Loaded cost spread (direct + even overhead share): avg $10.80 · median $10.80 · min $10.80 · max $10.80
- Active-time spread: avg 3m · median 3m · min 3m · max 3m  ·  loaded: avg 22m · median 22m · min 22m · max 22m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1901 | automated | $3.43 | $10.80 | 12,839 (in 40 / out 13k) | 3m | 22m | 2 | 18 (1) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $7.37 | 0 | 40,467 (in 94 / out 40k) | 97.7% | 19m | 47 (3) |
| test-automation-engineer | $3.43 | 2 | 12,839 (in 40 / out 13k) | 89.5% | 3m | 18 (1) |
