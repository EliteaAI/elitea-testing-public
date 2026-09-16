# Batch cost — fix-ELITEA-2036

Generated: 2026-09-16T21:15:02.022Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-15 → 2026-09-17 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.33  ·  0.1h active (cases 0m · lead 7m · stages 0m)  ·  0 dispatches
- Tokens: total 5,276,127  ·  **real work 29,682** (in 68 / out 29,614)  ·  cache 4.9M read / 312k write  ·  **cache hit rate 94.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 34 turns  ·  32 tool calls (2 err, 94% ok)
- Overhead (lead + triage + gate + report, shown once): $6.33 (100%)
- Loaded cost spread (direct + even overhead share): avg $6.33 · median $6.33 · min $6.33 · max $6.33

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2036 | blocked | n/a | $6.33 | 0 (incl. cache) | 0m | 7m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $6.33 | 0 | 29,682 (in 68 / out 30k) | 94.0% | 7m | 32 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-2036
