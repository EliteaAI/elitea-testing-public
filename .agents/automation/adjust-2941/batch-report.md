# Batch cost — adjust-2941

Generated: 2026-11-12T12:30:37.258Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-11 → 2026-11-13 (scopes)_

_1 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green
- Gate record (script-authored): green at ? (3 run record(s))
- Findings reported: 0  ·  fix rounds: 6

## What it cost

- Total: $18.68  ·  2.8h active (cases 81m · lead 81m · stages 5m)  ·  30 dispatches
- Tokens: total 45,094,675  ·  **real work 470,397** (in 255,920 / out 214,477)  ·  cache 40.5M read / 4.1M write  ·  **cache hit rate 90.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 69 turns  ·  363 tool calls (10 err, 97% ok)  ·  skills: adjust-automated-test
- Overhead (lead + triage + gate + report, shown once): $6.00 (32%)
  - by stage: lead $4.26 · triage $0.86 (2m) · gate $0.44 (2m) · report $0.44 (1m)
- Rework (fix rounds — already inside per-case direct): $3.46  ·  6 dispatch(es)  ·  29m
- **Per delivered case (incl. overhead): $18.68**
- Avg direct per case (excl. overhead): $12.68
- Direct cost spread: avg $12.68 · median $12.68 · min $12.68 · max $12.68
- Loaded cost spread (direct + even overhead share): avg $18.68 · median $18.68 · min $18.68 · max $18.68
- Active-time spread: avg 81m · median 81m · min 81m · max 81m  ·  loaded: avg 167m · median 167m · min 167m · max 167m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4632 | automated | $12.68 | $18.68 | 366,961 (in 198k / out 169k) | 81m | 167m | 23 | 266 (7) | 6 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $8.98 | 16 | 250,684 (in 127k / out 124k) | 93.6% | 66m | 217 (6) |
| qa-engineer | $5.44 | 14 | 167,015 (in 107k / out 60k) | 82.4% | 20m | 78 (1) |
| test-automation-lead | $4.26 | 0 | 52,698 (in 22k / out 31k) | 87.6% | 81m | 68 (3) |
