# Batch cost — chat-new-conv-2455

Generated: 2026-10-20T15:41:34.629Z  ·  sessions: 3 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-opus-5-5, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-10-19 → 2026-10-21 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-10-20T15:41:33Z (4 run record(s))
- Findings reported: 14  ·  fix rounds: 3

## What it cost

- Total: $61.65  ·  9.9h active (cases 158m · lead 343m · stages 95m)  ·  42 dispatches
- Tokens: total 153,177,018  ·  **real work 995,167** (in 446,090 / out 549,077)  ·  cache 141.2M read / 11.0M write  ·  **cache hit rate 92.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 168 turns  ·  901 tool calls (31 err, 97% ok)  ·  skills: test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $35.02 (57%)
  - by stage: lead $22.59 · triage $0.52 (1m) · gate $2.10 (22m) · report $0.98 (2m) · other $8.83 (70m)
- Rework (fix rounds — already inside per-case direct): $2.15  ·  3 dispatch(es)  ·  28m
- **Per delivered case (incl. overhead): $61.65**
- Avg direct per case (excl. overhead): $26.63
- Direct cost spread: avg $26.63 · median $26.63 · min $26.63 · max $26.63
- Loaded cost spread (direct + even overhead share): avg $61.65 · median $61.65 · min $61.65 · max $61.65
- Active-time spread: avg 158m · median 158m · min 158m · max 158m  ·  loaded: avg 596m · median 596m · min 596m · max 596m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2455 | automated | $26.63 | $61.65 | 513,469 (in 187k / out 326k) | 158m | 596m | 18 | 473 (11) | 3 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $30.31 | 25 | 587,966 (in 244k / out 344k) | 96.5% | 215m | 570 (15) |
| test-automation-lead | $17.75 | 0 | 119,259 (in 61k / out 58k) | 78.4% | 287m | 120 (8) |
| qa-engineer | $8.75 | 17 | 252,024 (in 129k / out 123k) | 88.1% | 38m | 168 (6) |
| session | $4.84 | 0 | 35,918 (in 11k / out 24k) | 91.8% | 56m | 43 (2) |
