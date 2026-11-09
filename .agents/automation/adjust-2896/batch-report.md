# Batch cost — adjust-2896

Generated: 2026-11-09T13:17:21.202Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: 1_eu.anthropic.claude-sonnet-5-5

_window 2026-11-08 → 2026-11-10 (scopes)_

## What happened

- Cases: 6  ·  **delivered: 6**  ·  automated 6
- Gate: green (3x6 passed on DEV runs)
- Gate record (script-authored): undefined at ? (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `undefined` — write the verdict back into report.json
- Findings reported: 0  ·  fix rounds: 0

## What it cost

- Total: $6.30  ·  2.5h active (cases 36m · lead 77m · stages 34m)  ·  4 dispatches
- Tokens: total 14,466,064  ·  **real work 130,001** (in 55,935 / out 74,066)  ·  cache 12.9M read / 1.4M write  ·  **cache hit rate 89.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 22 turns  ·  114 tool calls (4 err, 96% ok)  ·  skills: adjust-automated-test, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $3.60 (57%)
  - by stage: lead $1.88 · triage $1.72 (34m)
- **Per delivered case (incl. overhead): $1.05**
- Avg direct per case (excl. overhead): $2.69
- Direct cost spread: avg $2.69 · median $2.69 · min $2.69 · max $2.69
- Loaded cost spread (direct + even overhead share): avg $1.05 · median $0.60 · min $0.60 · max $3.29
- Active-time spread: avg 36m · median 36m · min 36m · max 36m  ·  loaded: avg 25m · median 19m · min 19m · max 55m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1791 | automated | $2.69 | $3.29 | 74,352 (in 31k / out 43k) | 36m | 55m | 3 | 61 (0) | 0 | 0 |
| ELITEA-1870 | automated | n/a | $0.60 | 0 (incl. cache) | 0m | 19m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1883 | automated | n/a | $0.60 | 0 (incl. cache) | 0m | 19m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1884 | automated | n/a | $0.60 | 0 (incl. cache) | 0m | 19m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1888 | automated | n/a | $0.60 | 0 (incl. cache) | 0m | 19m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1891 | automated | n/a | $0.60 | 0 (incl. cache) | 0m | 19m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $2.78 | 3 | 66,478 (in 32k / out 34k) | 88.6% | 41m | 50 (2) |
| test-automation-lead | $1.88 | 0 | 26,513 (in 13k / out 13k) | 80.8% | 77m | 23 (2) |
| test-automation-engineer | $1.63 | 1 | 37,010 (in 10k / out 27k) | 95.2% | 29m | 41 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-1870, ELITEA-1883, ELITEA-1884, ELITEA-1888, ELITEA-1891
