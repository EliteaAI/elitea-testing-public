# Batch cost — fix-2318

Generated: 2026-09-16T14:06:22.526Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_window 2026-09-15 → 2026-09-17 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.87  ·  0.2h active (cases 0m · lead 10m · stages 0m)  ·  0 dispatches
- Tokens: total 8,445,859  ·  **real work 33,108** (in 92 / out 33,016)  ·  cache 8.2M read / 194k write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 46 turns  ·  46 tool calls (1 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $6.87 (100%)
- **Per delivered case (incl. overhead): $6.87**
- Loaded cost spread (direct + even overhead share): avg $6.87 · median $6.87 · min $6.87 · max $6.87

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2063 | automated | n/a | $6.87 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $6.87 | 0 | 33,108 (in 92 / out 33k) | 97.7% | 10m | 46 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2063
