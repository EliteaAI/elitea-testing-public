# Batch cost — elitea-4631

Generated: 2026-11-11T13:38:32.414Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>

_window 2026-11-10 → 2026-11-12 (scopes)_

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: pass (4 runs)
- Gate record (script-authored): undefined at ? (4 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `pass` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 11  ·  fix rounds: 0

## What it cost

- Total: $8.72  ·  1.2h active (cases 27m · lead 40m · stages 3m)  ·  19 dispatches
- Tokens: total 18,532,105  ·  **real work 204,933** (in 132,556 / out 72,377)  ·  cache 16.2M read / 2.1M write  ·  **cache hit rate 87.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 21 turns  ·  155 tool calls (3 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $3.02 (35%)
  - by stage: lead $1.78 · triage $0.33 (0m) · gate $0.50 (2m) · report $0.41 (1m)
- **Per delivered case (incl. overhead): $8.72**
- Avg direct per case (excl. overhead): $5.70
- Direct cost spread: avg $5.70 · median $5.70 · min $5.70 · max $5.70
- Loaded cost spread (direct + even overhead share): avg $8.72 · median $8.72 · min $8.72 · max $8.72
- Active-time spread: avg 27m · median 27m · min 27m · max 27m  ·  loaded: avg 70m · median 70m · min 70m · max 70m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-4631 | automated | $5.70 | $8.72 | 142,184 (in 85k / out 57k) | 27m | 70m | 12 | 118 (2) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $3.56 | 10 | 82,460 (in 51k / out 32k) | 92.3% | 20m | 81 (0) |
| qa-engineer | $3.38 | 9 | 92,979 (in 60k / out 33k) | 84.3% | 10m | 53 (2) |
| test-automation-lead | $1.78 | 0 | 29,494 (in 22k / out 8k) | 76.5% | 40m | 21 (1) |
