# Batch cost — agent-hub-2351w1

Generated: 2026-09-14T11:44:33.023Z  ·  sessions: 4 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_4 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 8  ·  **delivered: 4**  ·  blocked 4  ·  automated 2  ·  merged-sanctioned-red 2
- Gate: green (3 runs)
- Findings reported: 54  ·  fix rounds: 0

## What it cost

- Total: $53.15  ·  2.6h active (cases 78m · lead 60m · stages 21m)  ·  8 dispatches
- Tokens: total 59,332,590  ·  **real work 358,474** (in 659 / out 357,815)  ·  cache 56.6M read / 2.4M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 75 turns  ·  371 tool calls (10 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.31 (40%)
  - by stage: lead $10.90 · triage $5.94 (10m) · other $4.47 (11m)
- **Per delivered case (incl. overhead): $13.29**
- Avg direct per case (excl. overhead): $31.85
- Direct cost spread: avg $31.85 · median $31.85 · min $31.85 · max $31.85
- Loaded cost spread (direct + even overhead share): avg $6.64 · median $2.66 · min $2.66 · max $34.51
- Active-time spread: avg 78m · median 78m · min 78m · max 78m  ·  loaded: avg 20m · median 10m · min 10m · max 88m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2351 | automated | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2353 | blocked | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 6 |
| ELITEA-2355 | blocked | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2357 | automated | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2358 | merged-sanctioned-red | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2364 | merged-sanctioned-red | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2366 | blocked | n/a | $2.66 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2367 | blocked | $31.85 | $34.51 | 228,078 (in 372 / out 228k) | 78m | 88m | 6 | 217 (6) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $22.49 | 3.67 | 144,834 (in 271 / out 145k) | 95.6% | 54m | 142 (4) |
| qa-engineer | $19.76 | 4.33 | 146,885 (in 238 / out 147k) | 95.2% | 45m | 156 (4) |
| test-automation-lead | $10.90 | 0 | 66,755 (in 150 / out 67k) | 97.8% | 60m | 74 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-2351, ELITEA-2353, ELITEA-2355, ELITEA-2357, ELITEA-2358, ELITEA-2364, ELITEA-2366

---

# Batch cost — agent-hub-2351w2

Generated: 2026-09-14T11:44:33.027Z  ·  sessions: 4 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_4 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 9  ·  **delivered: 0**  ·  blocked 8  ·  not-started 1
- Gate: red (1 runs)
- Findings reported: 67  ·  fix rounds: 0

## What it cost

- Total: $53.15  ·  2.6h active (cases 78m · lead 60m · stages 21m)  ·  8 dispatches
- Tokens: total 59,332,590  ·  **real work 358,474** (in 659 / out 357,815)  ·  cache 56.6M read / 2.4M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 75 turns  ·  371 tool calls (10 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.31 (40%)
  - by stage: lead $10.90 · triage $5.94 (10m) · other $4.47 (11m)
- Avg direct per case (excl. overhead): $31.85
- Direct cost spread: avg $31.85 · median $31.85 · min $31.85 · max $31.85
- Loaded cost spread (direct + even overhead share): avg $5.91 · median $2.37 · min $2.37 · max $34.22
- Active-time spread: avg 78m · median 78m · min 78m · max 78m  ·  loaded: avg 18m · median 9m · min 9m · max 87m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2353 | not-started | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2355 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2366 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2367 | blocked | $31.85 | $34.22 | 228,078 (in 372 / out 228k) | 78m | 87m | 6 | 217 (6) | 0 | 7 |
| ELITEA-2359 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 20 |
| ELITEA-2360 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 2 |
| ELITEA-2361 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2362 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2370 | blocked | n/a | $2.37 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 7 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $22.49 | 3.67 | 144,834 (in 271 / out 145k) | 95.6% | 54m | 142 (4) |
| qa-engineer | $19.76 | 4.33 | 146,885 (in 238 / out 147k) | 95.2% | 45m | 156 (4) |
| test-automation-lead | $10.90 | 0 | 66,755 (in 150 / out 67k) | 97.8% | 60m | 74 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-2353, ELITEA-2355, ELITEA-2366, ELITEA-2359, ELITEA-2360, ELITEA-2361, ELITEA-2362, ELITEA-2370

---

# Batch cost — agent-hub-2351w3

Generated: 2026-09-14T11:44:33.030Z  ·  sessions: 4 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_4 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 7  ·  **delivered: 0**  ·  blocked 7
- Gate: red (3 runs)
- Findings reported: 65  ·  fix rounds: 0

## What it cost

- Total: $53.15  ·  2.6h active (cases 78m · lead 60m · stages 21m)  ·  8 dispatches
- Tokens: total 59,332,590  ·  **real work 358,474** (in 659 / out 357,815)  ·  cache 56.6M read / 2.4M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 75 turns  ·  371 tool calls (10 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.31 (40%)
  - by stage: lead $10.90 · triage $5.94 (10m) · other $4.47 (11m)
- Avg direct per case (excl. overhead): $31.85
- Direct cost spread: avg $31.85 · median $31.85 · min $31.85 · max $31.85
- Loaded cost spread (direct + even overhead share): avg $7.59 · median $3.04 · min $3.04 · max $34.89
- Active-time spread: avg 78m · median 78m · min 78m · max 78m  ·  loaded: avg 23m · median 12m · min 12m · max 90m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2366 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2370 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2355 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2367 | blocked | $31.85 | $34.89 | 228,078 (in 372 / out 228k) | 78m | 90m | 6 | 217 (6) | 0 | 10 |
| ELITEA-2360 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2361 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2362 | blocked | n/a | $3.04 | 0 (incl. cache) | 0m | 12m | 0 | 0 (0) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $22.49 | 3.67 | 144,834 (in 271 / out 145k) | 95.6% | 54m | 142 (4) |
| qa-engineer | $19.76 | 4.33 | 146,885 (in 238 / out 147k) | 95.2% | 45m | 156 (4) |
| test-automation-lead | $10.90 | 0 | 66,755 (in 150 / out 67k) | 97.8% | 60m | 74 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-2366, ELITEA-2370, ELITEA-2355, ELITEA-2360, ELITEA-2361, ELITEA-2362

---

# Batch cost — agent-hub-2369

Generated: 2026-09-14T11:44:33.031Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 4 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 24  ·  fix rounds: 0

## What it cost

- Total: $24.56  ·  1.6h active (cases 23m · lead 60m · stages 15m)  ·  2.67 dispatches
- Tokens: total 30,666,543  ·  **real work 138,380** (in 344 / out 138,036)  ·  cache 29.6M read / 889k write  ·  **cache hit rate 97.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 43 turns  ·  192 tool calls (4 err, 98% ok)
- Overhead (lead + triage + gate + report, shown once): $16.42 (67%)
  - by stage: lead $7.95 · triage $5.81 (11m) · other $2.67 (4m)
- **Per delivered case (incl. overhead): $24.56**
- Avg direct per case (excl. overhead): $8.14
- Direct cost spread: avg $8.14 · median $8.14 · min $8.14 · max $8.14
- Loaded cost spread (direct + even overhead share): avg $24.56 · median $24.56 · min $24.56 · max $24.56
- Active-time spread: avg 23m · median 23m · min 23m · max 23m  ·  loaded: avg 98m · median 98m · min 98m · max 98m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2369 | automated | $8.14 | $24.56 | 43,390 (in 96 / out 43k) | 23m | 98m | 1 | 58 (1) | 0 | 24 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $8.14 | 1 | 43,390 (in 96 / out 43k) | 95.4% | 23m | 58 (1) |
| test-automation-lead | $7.95 | 0 | 41,618 (in 86 / out 42k) | 98.1% | 60m | 42 (2) |
| qa-engineer | $5.81 | 1 | 37,087 (in 102 / out 37k) | 97.7% | 11m | 62 (1) |
| general-purpose | $2.67 | 0.67 | 16,285 (in 60 / out 16k) | 97.4% | 4m | 29 (0) |

---

# Batch cost — agent-hub-start-conversation-no-starters

Generated: 2026-09-14T11:44:33.078Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 315 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: $11.16  ·  2.5h active (cases 0m · lead 145m · stages 5m)  ·  1.15 dispatches
- Tokens: total 46,744,646  ·  **real work 59,641** (in 264 / out 59,377)  ·  cache 46.2M read / 442k write  ·  **cache hit rate 99.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  98 tool calls (2 err, 98% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $11.16 (100%)
  - by stage: lead $10.62 · report $0.27 (4m) · other $0.28 (1m)
- **Per delivered case (incl. overhead): $11.16**
- Loaded cost spread (direct + even overhead share): avg $11.16 · median $11.16 · min $11.16 · max $11.16

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2368 | automated | n/a | $11.16 | 0 (incl. cache) | 0m | 150m | 0 | 0 (0) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| test-automation-engineer | $0.54 | 1.15 | 20,593 (in 85 / out 21k) | 92.4% | 5m | 15 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2368

---

# Batch cost — agents-batch1-1277

Generated: 2026-09-14T11:44:33.127Z  ·  sessions: 3 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_2 session(s) also served other batches — their session-level figures are split evenly; 315 other-batch dispatch(es) excluded._

## What happened

- Cases: 11  ·  **delivered: 0**  ·  merged-ungated 10  ·  blocked 1
- Gate: not-run
- Findings reported: 61  ·  fix rounds: 0

## What it cost

- Total: $67.89  ·  6.2h active (cases 127m · lead 224m · stages 22m)  ·  8.82 dispatches
- Tokens: total 122,964,039  ·  **real work 458,049** (in 1,186 / out 456,863)  ·  cache 119.5M read / 3.1M write  ·  **cache hit rate 97.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 177 turns  ·  591 tool calls (16 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $29.78 (44%)
  - by stage: lead $20.64 · triage $5.81 (11m) · report $0.39 (6m) · other $2.94 (5m)
- Avg direct per case (excl. overhead): $19.05
- Direct cost spread: avg $19.05 · median $19.05 · min $2.58 · max $35.52
- Loaded cost spread (direct + even overhead share): avg $6.17 · median $2.71 · min $2.71 · max $38.23
- Active-time spread: avg 64m · median 64m · min 9m · max 118m  ·  loaded: avg 34m · median 22m · min 22m · max 140m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1873 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 5 |
| ELITEA-1874 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 7 |
| ELITEA-1875 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 7 |
| ELITEA-1876 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 6 |
| ELITEA-1878 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 5 |
| ELITEA-1879 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 5 |
| ELITEA-1882 | blocked | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 4 |
| ELITEA-1886 | merged-ungated | $35.52 | $38.23 | 224,500 (in 468 / out 224k) | 118m | 140m | 5 | 259 (6) | 0 | 5 |
| ELITEA-1898 | merged-ungated | $2.58 | $5.29 | 35,077 (in 102 / out 35k) | 9m | 31m | 1 | 54 (1) | 0 | 6 |
| ELITEA-1900 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 4 |
| ELITEA-1951 | merged-ungated | n/a | $2.71 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 7 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $23.53 | 4 | 149,074 (in 358 / out 149k) | 96.1% | 71m | 205 (6) |
| test-automation-engineer | $21.06 | 4.15 | 178,412 (in 415 / out 178k) | 96.0% | 74m | 187 (5) |
| test-automation-lead | $20.64 | 0 | 114,280 (in 354 / out 114k) | 98.9% | 224m | 169 (4) |
| general-purpose | $2.67 | 0.67 | 16,285 (in 60 / out 16k) | 97.4% | 4m | 29 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-1873, ELITEA-1874, ELITEA-1875, ELITEA-1876, ELITEA-1878, ELITEA-1879, ELITEA-1882, ELITEA-1900, ELITEA-1951

---

# Batch cost — approved-next50/wave-01-heads_artifacts-upload-dup_pipe-hitl-node

Generated: 2026-09-14T11:44:33.173Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 314 other-batch dispatch(es) excluded._

## What happened

- Cases: 11  ·  **delivered: 11**  ·  automated 11
- Gate: green (3 runs)
- Findings reported: 0  ·  fix rounds: 1

## What it cost

- Total: $22.06  ·  3.0h active (cases 12m · lead 161m · stages 9m)  ·  3.15 dispatches
- Tokens: total 65,377,236  ·  **real work 129,662** (in 439 / out 129,223)  ·  cache 64.2M read / 1.0M write  ·  **cache hit rate 98.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 115 turns  ·  217 tool calls (5 err, 98% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $18.54 (84%)
  - by stage: lead $14.72 · triage $3.55 (8m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $2.51  ·  1 dispatch(es)  ·  9m
- **Per delivered case (incl. overhead): $2.01**
- Avg direct per case (excl. overhead): $3.52
- Direct cost spread: avg $3.52 · median $3.52 · min $3.52 · max $3.52
- Loaded cost spread (direct + even overhead share): avg $2.01 · median $1.69 · min $1.69 · max $5.21
- Active-time spread: avg 12m · median 12m · min 12m · max 12m  ·  loaded: avg 16m · median 15m · min 15m · max 27m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1920 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1999 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1811 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1814 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2021 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1828 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1829 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1831 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2014 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2015 | automated | n/a | $1.69 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2181 | automated | $3.52 | $5.21 | 42,798 (in 148 / out 43k) | 12m | 27m | 2 | 80 (2) | 1 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $14.72 | 0 | 65,244 (in 230 / out 65k) | 99.0% | 161m | 107 (3) |
| qa-engineer | $4.56 | 2 | 32,206 (in 86 / out 32k) | 94.7% | 11m | 48 (1) |
| test-automation-engineer | $2.79 | 1.15 | 32,213 (in 124 / out 32k) | 97.7% | 10m | 62 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-1920, ELITEA-1999, ELITEA-1811, ELITEA-1814, ELITEA-2021, ELITEA-1828, ELITEA-1829, ELITEA-1831, ELITEA-2014, ELITEA-2015

---

# Batch cost — approved-next50/wave-02-05-merged

Generated: 2026-09-14T11:44:33.226Z  ·  sessions: 11 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_5 session(s) also served other batches — their session-level figures are split evenly; 307 other-batch dispatch(es) excluded._

## What happened

- Cases: 39  ·  **delivered: 33**  ·  automated 33  ·  blocked 6
- Gate: green
- Findings reported: 0  ·  fix rounds: 5

## What it cost

- Total: $314.61  ·  23.2h active (cases 513m · lead 743m · stages 135m)  ·  48.82 dispatches
- Tokens: total 445,429,143  ·  **real work 2,091,886** (in 5,423 / out 2,086,463)  ·  cache 429.9M read / 13.5M write  ·  **cache hit rate 97.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 678 turns  ·  2586 tool calls (126 err, 95% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $124.82 (40%)
  - by stage: lead $82.82 · triage $19.43 (43m) · report $2.92 (44m) · other $19.66 (48m)
- Rework (fix rounds — already inside per-case direct): $11.04  ·  5 dispatch(es)  ·  24m
- **Per delivered case (incl. overhead): $9.53**
- Avg direct per case (excl. overhead): $21.09
- Direct cost spread: avg $21.09 · median $21.62 · min $1.95 · max $42.49
- Loaded cost spread (direct + even overhead share): avg $8.07 · median $3.20 · min $3.20 · max $45.69
- Active-time spread: avg 57m · median 51m · min 5m · max 175m  ·  loaded: avg 36m · median 23m · min 23m · max 198m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1851 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1852 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1856 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1857 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1858 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1862 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2028 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2135 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2137 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2149 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2162 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2168 | automated | $3.42 | $6.62 | 20,307 (in 112 / out 20k) | 10m | 33m | 2 | 50 (6) | 1 | 0 |
| ELITEA-2197 | automated | $1.95 | $5.15 | 20,577 (in 80 / out 20k) | 5m | 28m | 2 | 42 (1) | 1 | 0 |
| ELITEA-2200 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2202 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2203 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2204 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2211 | blocked | $36.90 | $40.10 | 142,770 (in 496 / out 142k) | 60m | 83m | 2 | 261 (13) | 0 | 0 |
| ELITEA-2212 | blocked | $28.29 | $31.49 | 168,041 (in 380 / out 168k) | 88m | 111m | 3 | 209 (11) | 0 | 0 |
| ELITEA-2213 | blocked | $21.62 | $24.82 | 118,372 (in 328 / out 118k) | 47m | 70m | 3 | 182 (10) | 0 | 0 |
| ELITEA-2214 | blocked | $18.17 | $21.37 | 138,062 (in 250 / out 138k) | 51m | 74m | 3 | 134 (3) | 0 | 0 |
| ELITEA-2215 | blocked | $25.71 | $28.91 | 184,656 (in 378 / out 184k) | 57m | 80m | 9 | 204 (5) | 3 | 0 |
| ELITEA-2218 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2075 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2079 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2085 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2086 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2087 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2088 | blocked | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2004 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2010 | automated | $11.24 | $14.44 | 58,592 (in 160 / out 58k) | 20m | 43m | 1 | 90 (8) | 0 | 0 |
| ELITEA-2005 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2006 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2007 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2008 | automated | $42.49 | $45.69 | 277,533 (in 504 / out 277k) | 175m | 198m | 6 | 281 (4) | 0 | 0 |
| ELITEA-2018 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2030 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2031 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2032 | automated | n/a | $3.20 | 0 (incl. cache) | 0m | 23m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $124.47 | 24 | 796,185 (in 2k / out 794k) | 96.8% | 292m | 1126 (59) |
| test-automation-engineer | $102.39 | 23.15 | 770,559 (in 2k / out 769k) | 95.4% | 349m | 742 (41) |
| test-automation-lead | $82.82 | 0 | 499,744 (in 1k / out 498k) | 98.5% | 743m | 662 (23) |
| general-purpose | $4.93 | 1.67 | 25,400 (in 116 / out 25k) | 96.7% | 7m | 56 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-1851, ELITEA-1852, ELITEA-1856, ELITEA-1857, ELITEA-1858, ELITEA-1862, ELITEA-2028, ELITEA-2135, ELITEA-2137, ELITEA-2149, ELITEA-2162, ELITEA-2200, ELITEA-2202, ELITEA-2203, ELITEA-2204, ELITEA-2218, ELITEA-2075, ELITEA-2079, ELITEA-2085, ELITEA-2086, ELITEA-2087, ELITEA-2088, ELITEA-2004, ELITEA-2005, ELITEA-2006, ELITEA-2007, ELITEA-2018, ELITEA-2030, ELITEA-2031, ELITEA-2032

---

# Batch cost — approved-top10

Generated: 2026-09-14T11:44:33.252Z  ·  sessions: 5 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_3 session(s) also served other batches — their session-level figures are split evenly; 128 other-batch dispatch(es) excluded._

## What happened

- Cases: 10  ·  **delivered: 10**  ·  automated 10
- Gate: green (3 runs)
- Findings reported: 150  ·  fix rounds: 1

## What it cost

- Total: $106.90  ·  10.1h active (cases 180m · lead 371m · stages 53m)  ·  12.5 dispatches
- Tokens: total 129,787,407  ·  **real work 679,613** (in 1,542 / out 678,071)  ·  cache 124.5M read / 4.6M write  ·  **cache hit rate 96.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 246 turns  ·  773 tool calls (25 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $42.49 (40%)
  - by stage: lead $33.41 · report $1.00 (16m) · other $8.07 (37m)
- Rework (fix rounds — already inside per-case direct): $4.86  ·  1 dispatch(es)  ·  12m
- **Per delivered case (incl. overhead): $10.69**
- Avg direct per case (excl. overhead): $32.21
- Direct cost spread: avg $32.21 · median $32.21 · min $26.31 · max $38.10
- Loaded cost spread (direct + even overhead share): avg $10.69 · median $4.25 · min $4.25 · max $42.35
- Active-time spread: avg 90m · median 90m · min 70m · max 110m  ·  loaded: avg 60m · median 42m · min 42m · max 152m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1934 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 22 |
| ELITEA-1937 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 22 |
| ELITEA-1976 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 15 |
| ELITEA-1978 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 15 |
| ELITEA-1979 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 15 |
| ELITEA-1890 | automated | $26.31 | $30.56 | 175,308 (in 326 / out 175k) | 70m | 112m | 4.5 | 198 (5) | 1 | 17 |
| ELITEA-1891 | automated | $38.10 | $42.35 | 203,065 (in 454 / out 203k) | 110m | 152m | 3.5 | 253 (7) | 0 | 17 |
| ELITEA-1877 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 9 |
| ELITEA-1880 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 9 |
| ELITEA-1993 | automated | n/a | $4.25 | 0 (incl. cache) | 0m | 42m | 0 | 0 (0) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $50.74 | 6.5 | 294,106 (in 800 / out 293k) | 96.3% | 150m | 347 (13) |
| test-automation-lead | $33.41 | 0 | 184,397 (in 490 / out 184k) | 98.2% | 371m | 242 (9) |
| qa-engineer | $22.75 | 6 | 201,111 (in 252 / out 201k) | 92.6% | 82m | 184 (3) |

Unattributed (no dispatch named them in any captured session): ELITEA-1934, ELITEA-1937, ELITEA-1976, ELITEA-1978, ELITEA-1979, ELITEA-1877, ELITEA-1880, ELITEA-1993

---

# Batch cost — artifacts-w01

Generated: 2026-09-14T11:44:33.272Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 101 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 8**  ·  automated 8  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-21T16:52:17.578Z (3 run record(s))
- Findings reported: 162  ·  fix rounds: 0.99

## What it cost

- Total: $71.07  ·  5.0h active (cases 122m · lead 152m · stages 29m)  ·  21 dispatches
- Tokens: total 88,384,975  ·  **real work 520,530** (in 1,386 / out 519,144)  ·  cache 84.4M read / 3.4M write  ·  **cache hit rate 96.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  588 tool calls (13 err, 98% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $15.84 (22%)
  - by stage: lead $12.38 · triage $0.22 (2m) · gate $2.57 (17m) · report $0.67 (10m)
- Rework (fix rounds — already inside per-case direct): $3.36  ·  1 dispatch(es)  ·  6m
- **Per delivered case (incl. overhead): $8.88**
- Avg direct per case (excl. overhead): $6.90
- Direct cost spread: avg $6.90 · median $6.80 · min $3.20 · max $9.29
- Loaded cost spread (direct + even overhead share): avg $7.90 · median $8.33 · min $1.76 · max $11.05
- Active-time spread: avg 15m · median 16m · min 5m · max 19m  ·  loaded: avg 34m · median 35m · min 20m · max 39m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1803 | automated | $9.29 | $11.05 | 65,439 (in 151 / out 65k) | 19m | 39m | 1.83 | 76 (1) | 0.33 | 32 |
| ELITEA-1804 | automated | $9.29 | $11.05 | 65,439 (in 151 / out 65k) | 19m | 39m | 1.83 | 76 (1) | 0.33 | 32 |
| ELITEA-1805 | automated | $3.20 | $4.96 | 18,537 (in 68 / out 18k) | 5m | 25m | 1.33 | 29 (0) | 0.33 | 32 |
| ELITEA-1806 | blocked | n/a | $1.76 | 0 (incl. cache) | 0m | 20m | 0 | 0 (0) | 0 | 7 |
| ELITEA-1807 | automated | $8.51 | $10.27 | 62,694 (in 185 / out 63k) | 17m | 37m | 3 | 92 (3) | 0 | 12 |
| ELITEA-1820 | automated | $5.67 | $7.43 | 47,608 (in 103 / out 48k) | 15m | 35m | 1.5 | 52 (2) | 0 | 12 |
| ELITEA-1821 | automated | $5.67 | $7.43 | 47,608 (in 103 / out 48k) | 15m | 35m | 1.5 | 52 (2) | 0 | 12 |
| ELITEA-1822 | automated | $7.03 | $8.79 | 67,412 (in 155 / out 67k) | 18m | 38m | 3 | 57 (1) | 0 | 11 |
| ELITEA-1823 | automated | $6.57 | $8.33 | 52,106 (in 153 / out 52k) | 14m | 34m | 3 | 62 (1) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $43.73 | 14 | 367,143 (in 979 / out 366k) | 96.1% | 122m | 401 (12) |
| qa-engineer | $14.96 | 7 | 118,494 (in 295 / out 118k) | 93.2% | 29m | 132 (0) |
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-1806

---

# Batch cost — artifacts-w02

Generated: 2026-09-14T11:44:33.292Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 91 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 7**  ·  automated 7
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-21T20:15:10.578Z (3 run record(s))
- Findings reported: 106  ·  fix rounds: 0.99

## What it cost

- Total: $95.65  ·  6.3h active (cases 161m · lead 188m · stages 29m)  ·  31 dispatches
- Tokens: total 110,548,872  ·  **real work 688,788** (in 1,986 / out 686,802)  ·  cache 104.8M read / 5.0M write  ·  **cache hit rate 95.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 131 turns  ·  820 tool calls (23 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $28.57 (30%)
  - by stage: lead $24.66 · triage $0.54 (5m) · gate $3.05 (19m) · report $0.31 (5m)
- Rework (fix rounds — already inside per-case direct): $3.61  ·  1 dispatch(es)  ·  8m
- **Per delivered case (incl. overhead): $13.66**
- Avg direct per case (excl. overhead): $9.58
- Direct cost spread: avg $9.58 · median $9.59 · min $3.55 · max $13.29
- Loaded cost spread (direct + even overhead share): avg $13.66 · median $13.67 · min $7.63 · max $17.37
- Active-time spread: avg 23m · median 25m · min 7m · max 30m  ·  loaded: avg 54m · median 56m · min 38m · max 61m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1825 | automated | $12.77 | $16.85 | 91,007 (in 288 / out 91k) | 26m | 57m | 7 | 137 (4) | 0 | 11 |
| ELITEA-1830 | automated | $9.14 | $13.22 | 77,144 (in 202 / out 77k) | 24m | 55m | 3.5 | 87 (2) | 0 | 10 |
| ELITEA-1833 | automated | $9.14 | $13.22 | 77,144 (in 202 / out 77k) | 24m | 55m | 3.5 | 87 (2) | 0 | 10 |
| ELITEA-1834 | automated | $13.29 | $17.37 | 102,077 (in 372 / out 102k) | 30m | 61m | 7 | 138 (4) | 0 | 9 |
| ELITEA-1836 | automated | $9.59 | $13.67 | 78,522 (in 139 / out 78k) | 25m | 56m | 2.33 | 79 (1) | 0.33 | 22 |
| ELITEA-1837 | automated | $9.59 | $13.67 | 78,522 (in 139 / out 78k) | 25m | 56m | 2.33 | 79 (1) | 0.33 | 22 |
| ELITEA-1838 | automated | $3.55 | $7.63 | 27,969 (in 66 / out 28k) | 7m | 38m | 1.33 | 34 (1) | 0.33 | 22 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $37.31 | 17 | 314,966 (in 1k / out 314k) | 94.9% | 113m | 352 (14) |
| qa-engineer | $33.68 | 14 | 276,083 (in 696 / out 275k) | 93.9% | 76m | 343 (4) |
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |
| scout | $12.28 | 0 | 62,846 (in 148 / out 63k) | 96.7% | 36m | 70 (4) |

---

# Batch cost — artifacts-w03

Generated: 2026-09-14T11:44:33.312Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 105 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 7**  ·  automated 7
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-21T22:25:49.798Z (3 run record(s))
- Findings reported: 141  ·  fix rounds: 1.9900000000000002

## What it cost

- Total: $59.40  ·  4.5h active (cases 95m · lead 152m · stages 25m)  ·  17 dispatches
- Tokens: total 75,460,471  ·  **real work 432,151** (in 1,206 / out 430,945)  ·  cache 72.2M read / 2.8M write  ·  **cache hit rate 96.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  520 tool calls (13 err, 98% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $15.31 (26%)
  - by stage: lead $12.38 · triage $0.23 (1m) · gate $1.85 (13m) · report $0.85 (11m)
- Rework (fix rounds — already inside per-case direct): $6.94  ·  2 dispatch(es)  ·  13m
- **Per delivered case (incl. overhead): $8.49**
- Avg direct per case (excl. overhead): $6.30
- Direct cost spread: avg $6.30 · median $6.22 · min $2.87 · max $8.26
- Loaded cost spread (direct + even overhead share): avg $8.49 · median $8.41 · min $5.06 · max $10.45
- Active-time spread: avg 14m · median 15m · min 5m · max 18m  ·  loaded: avg 39m · median 40m · min 30m · max 43m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1842 | automated | $6.14 | $8.33 | 40,361 (in 119 / out 40k) | 12m | 37m | 1.5 | 54 (1) | 0 | 11 |
| ELITEA-1843 | automated | $6.14 | $8.33 | 40,361 (in 119 / out 40k) | 12m | 37m | 1.5 | 54 (1) | 0 | 11 |
| ELITEA-1844 | automated | $8.26 | $10.45 | 64,475 (in 148 / out 64k) | 18m | 43m | 2.5 | 80 (2) | 0.5 | 25 |
| ELITEA-1845 | automated | $8.26 | $10.45 | 64,475 (in 148 / out 64k) | 18m | 43m | 2.5 | 80 (2) | 0.5 | 25 |
| ELITEA-1848 | automated | $6.22 | $8.41 | 48,860 (in 119 / out 49k) | 15m | 40m | 1.83 | 59 (2) | 0.33 | 23 |
| ELITEA-1849 | automated | $6.22 | $8.41 | 48,860 (in 119 / out 49k) | 15m | 40m | 1.83 | 59 (2) | 0.33 | 23 |
| ELITEA-1850 | automated | $2.87 | $5.06 | 19,151 (in 73 / out 19k) | 5m | 30m | 1.33 | 31 (0) | 0.33 | 23 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $33.66 | 11 | 291,364 (in 815 / out 291k) | 96.1% | 94m | 336 (11) |
| qa-engineer | $13.36 | 6 | 105,894 (in 279 / out 106k) | 93.4% | 25m | 129 (1) |
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |

---

# Batch cost — artifacts-w04

Generated: 2026-09-14T11:44:33.331Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 91 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 7**  ·  automated 5  ·  merged-sanctioned-red 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): red at 2026-08-23T16:42:58.666Z (5 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `red` — write the verdict back into report.json
- Findings reported: 49  ·  fix rounds: 3

## What it cost

- Total: $116.60  ·  7.1h active (cases 246m · lead 152m · stages 29m)  ·  31 dispatches
- Tokens: total 141,535,922  ·  **real work 760,663** (in 2,066 / out 758,597)  ·  cache 135.4M read / 5.4M write  ·  **cache hit rate 96.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  1010 tool calls (27 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $19.74 (17%)
  - by stage: lead $12.38 · triage $0.21 (2m) · gate $6.78 (23m) · report $0.37 (4m)
- Rework (fix rounds — already inside per-case direct): $10.91  ·  3 dispatch(es)  ·  23m
- **Per delivered case (incl. overhead): $16.66**
- Avg direct per case (excl. overhead): $12.11
- Direct cost spread: avg $12.11 · median $8.09 · min $6.58 · max $39.99
- Loaded cost spread (direct + even overhead share): avg $14.58 · median $10.56 · min $9.05 · max $42.46
- Active-time spread: avg 31m · median 20m · min 13m · max 119m  ·  loaded: avg 54m · median 43m · min 36m · max 142m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1810 | merged-sanctioned-red | $39.99 | $42.46 | 240,048 (in 707 / out 239k) | 119m | 142m | 11 | 388 (11) | 2 | 49 |
| ELITEA-1812 | automated | $10.16 | $12.63 | 76,783 (in 180 / out 77k) | 24m | 47m | 3.5 | 90 (2) | 0.5 | 0 |
| ELITEA-1813 | automated | $6.58 | $9.05 | 47,284 (in 125 / out 47k) | 13m | 36m | 2.5 | 61 (0) | 0 | 0 |
| ELITEA-1815 | automated | $6.58 | $9.05 | 47,284 (in 125 / out 47k) | 13m | 36m | 2.5 | 61 (0) | 0 | 0 |
| ELITEA-1816 | automated | $10.16 | $12.63 | 76,783 (in 180 / out 77k) | 24m | 47m | 3.5 | 90 (2) | 0.5 | 0 |
| ELITEA-1818 | merged-sanctioned-red | $7.22 | $9.69 | 68,592 (in 126 / out 68k) | 20m | 43m | 2 | 59 (2) | 0 | 0 |
| ELITEA-1819 | automated | $7.22 | $9.69 | 68,592 (in 126 / out 68k) | 20m | 43m | 2 | 59 (2) | 0 | 0 |
| ELITEA-1867 | blocked | $8.96 | $11.43 | 46,696 (in 158 / out 47k) | 13m | 36m | 1 | 91 (4) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $62.19 | 18 | 408,922 (in 1k / out 408k) | 96.3% | 158m | 608 (15) |
| test-automation-engineer | $42.03 | 13 | 316,848 (in 891 / out 316k) | 95.1% | 115m | 347 (11) |
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |

---

# Batch cost — artifacts-w05

Generated: 2026-09-14T11:44:33.350Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 102 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 8**  ·  automated 8  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-23T18:54:20.154Z (3 run record(s))
- Findings reported: 87  ·  fix rounds: 0.99

## What it cost

- Total: $62.39  ·  4.5h active (cases 94m · lead 152m · stages 22m)  ·  20 dispatches
- Tokens: total 77,872,845  ·  **real work 443,849** (in 1,347 / out 442,502)  ·  cache 74.4M read / 3.0M write  ·  **cache hit rate 96.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  563 tool calls (17 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $15.40 (25%)
  - by stage: lead $12.38 · triage $0.46 (3m) · gate $2.02 (13m) · report $0.54 (6m)
- Rework (fix rounds — already inside per-case direct): $3.03  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $7.80**
- Avg direct per case (excl. overhead): $5.22
- Direct cost spread: avg $5.22 · median $3.78 · min $2.00 · max $11.02
- Loaded cost spread (direct + even overhead share): avg $6.93 · median $5.49 · min $3.71 · max $12.73
- Active-time spread: avg 10m · median 9m · min 4m · max 24m  ·  loaded: avg 29m · median 28m · min 23m · max 43m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1853 | automated | $11.02 | $12.73 | 89,533 (in 186 / out 89k) | 24m | 43m | 2.33 | 101 (3) | 0.33 | 29 |
| ELITEA-1854 | automated | $2.60 | $4.31 | 16,599 (in 64 / out 17k) | 5m | 24m | 1.33 | 28 (0) | 0.33 | 29 |
| ELITEA-1855 | automated | $2.60 | $4.31 | 16,599 (in 64 / out 17k) | 5m | 24m | 1.33 | 28 (0) | 0.33 | 29 |
| ELITEA-1859 | automated | $3.78 | $5.49 | 33,430 (in 70 / out 33k) | 9m | 28m | 1.5 | 32 (0) | 0 | 0 |
| ELITEA-1860 | automated | $3.78 | $5.49 | 33,430 (in 70 / out 33k) | 9m | 28m | 1.5 | 32 (0) | 0 | 0 |
| ELITEA-1861 | automated | $2.00 | $3.71 | 14,968 (in 49 / out 15k) | 4m | 23m | 1 | 18 (0) | 0 | 0 |
| ELITEA-1863 | automated | $6.60 | $8.31 | 47,832 (in 131 / out 48k) | 12m | 31m | 2 | 65 (3) | 0 | 0 |
| ELITEA-1864 | automated | $6.60 | $8.31 | 47,832 (in 131 / out 48k) | 12m | 31m | 2 | 65 (3) | 0 | 0 |
| ELITEA-1865 | blocked | $8.02 | $9.73 | 53,836 (in 138 / out 54k) | 14m | 33m | 2 | 82 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $26.28 | 10 | 201,817 (in 580 / out 201k) | 94.9% | 52m | 265 (2) |
| test-automation-engineer | $23.73 | 10 | 207,139 (in 655 / out 206k) | 95.7% | 63m | 243 (14) |
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |

---

# Batch cost — artifacts-w06

Generated: 2026-09-14T11:44:33.370Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 118 other-batch dispatch(es) excluded._

## What happened

- Cases: 2  ·  **delivered: 0**  ·  blocked 2
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: $21.95  ·  3.0h active (cases 28m · lead 152m · stages 3m)  ·  4 dispatches
- Tokens: total 29,936,471  ·  **real work 123,131** (in 382 / out 122,749)  ·  cache 29.0M read / 792k write  ·  **cache hit rate 97.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  158 tool calls (5 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.77 (58%)
  - by stage: lead $12.38 · triage $0.23 (1m) · report $0.15 (2m)
- Avg direct per case (excl. overhead): $4.59
- Direct cost spread: avg $4.59 · median $4.59 · min $3.88 · max $5.30
- Loaded cost spread (direct + even overhead share): avg $10.97 · median $10.97 · min $10.26 · max $11.68
- Active-time spread: avg 14m · median 14m · min 10m · max 18m  ·  loaded: avg 92m · median 92m · min 88m · max 96m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2491 | blocked | $3.88 | $10.26 | 31,083 (in 62 / out 31k) | 10m | 88m | 1 | 41 (1) | 0 | 6 |
| ELITEA-2492 | blocked | $5.30 | $11.68 | 44,579 (in 78 / out 45k) | 18m | 96m | 1 | 46 (0) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |
| qa-engineer | $9.42 | 3 | 81,298 (in 237 / out 81k) | 96.0% | 29m | 99 (3) |
| test-automation-engineer | $0.15 | 1 | 6,940 (in 33 / out 7k) | 74.0% | 2m | 4 (1) |

---

# Batch cost — artifacts-w07

Generated: 2026-09-14T11:44:33.390Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 117 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 5  ·  fix rounds: 0

## What it cost

- Total: $21.02  ·  2.8h active (cases 14m · lead 152m · stages 4m)  ·  5 dispatches
- Tokens: total 30,006,031  ·  **real work 107,170** (in 477 / out 106,693)  ·  cache 29.0M read / 859k write  ·  **cache hit rate 97.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 57 turns  ·  165 tool calls (4 err, 98% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $13.01 (62%)
  - by stage: lead $12.38 · triage $0.46 (3m) · report $0.16 (1m)
- Avg direct per case (excl. overhead): $8.02
- Direct cost spread: avg $8.02 · median $8.02 · min $8.02 · max $8.02
- Loaded cost spread (direct + even overhead share): avg $21.03 · median $21.03 · min $21.03 · max $21.03
- Active-time spread: avg 14m · median 14m · min 14m · max 14m  ·  loaded: avg 170m · median 170m · min 170m · max 170m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1865 | blocked | $8.02 | $21.03 | 53,836 (in 138 / out 54k) | 14m | 170m | 2 | 82 (1) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $12.38 | 0 | 34,893 (in 112 / out 35k) | 98.6% | 152m | 55 (1) |
| qa-engineer | $8.48 | 4 | 67,059 (in 324 / out 67k) | 95.5% | 17m | 105 (2) |
| test-automation-engineer | $0.16 | 1 | 5,218 (in 41 / out 5k) | 79.4% | 1m | 5 (1) |

---

# Batch cost — chat-remaining-w01

Generated: 2026-09-14T11:44:33.437Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 297 other-batch dispatch(es) excluded._

## What happened

- Cases: 5  ·  **delivered: 3**  ·  automated 3  ·  blocked 2
- Gate: green (3 runs)
- Findings reported: 36  ·  fix rounds: 1

## What it cost

- Total: $80.69  ·  5.6h active (cases 159m · lead 145m · stages 33m)  ·  19.15 dispatches
- Tokens: total 332,063,285  ·  **real work 709,823** (in 3,239 / out 706,584)  ·  cache 327.5M read / 3.8M write  ·  **cache hit rate 98.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1392 tool calls (51 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $18.72 (23%)
  - by stage: lead $10.62 · triage $0.34 (2m) · gate $6.23 (11m) · report $1.25 (19m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $3.87  ·  1 dispatch(es)  ·  17m
- **Per delivered case (incl. overhead): $26.90**
- Avg direct per case (excl. overhead): $12.39
- Direct cost spread: avg $12.39 · median $9.99 · min $1.31 · max $26.39
- Loaded cost spread (direct + even overhead share): avg $16.13 · median $13.73 · min $5.05 · max $30.13
- Active-time spread: avg 32m · median 29m · min 4m · max 63m  ·  loaded: avg 68m · median 65m · min 40m · max 99m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2091 | automated | $26.39 | $30.13 | 238,188 (in 877 / out 237k) | 63m | 99m | 4 | 423 (12) | 0 | 9 |
| ELITEA-2093 | automated | $9.99 | $13.73 | 83,493 (in 405 / out 83k) | 29m | 65m | 3 | 187 (7) | 0 | 4 |
| ELITEA-2096 | blocked | $1.31 | $5.05 | 13,095 (in 59 / out 13k) | 4m | 40m | 0.33 | 30 (2) | 0 | 3 |
| ELITEA-2097 | blocked | $1.31 | $5.05 | 13,095 (in 59 / out 13k) | 4m | 40m | 0.33 | 30 (2) | 0 | 3 |
| ELITEA-2098 | automated | $22.97 | $26.71 | 194,267 (in 858 / out 193k) | 59m | 95m | 5.33 | 423 (17) | 1 | 17 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $56.01 | 12.15 | 490,589 (in 2k / out 488k) | 99.0% | 149m | 974 (36) |
| qa-engineer | $14.06 | 7 | 180,186 (in 793 / out 179k) | 97.5% | 42m | 335 (14) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w02

Generated: 2026-09-14T11:44:33.482Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 296 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 0**  ·  blocked 6
- Gate: red (2 runs)
- Findings reported: 55  ·  fix rounds: 0

## What it cost

- Total: $39.87  ·  4.0h active (cases 78m · lead 145m · stages 18m)  ·  20.15 dispatches
- Tokens: total 146,327,459  ·  **real work 400,668** (in 1,825 / out 398,843)  ·  cache 142.7M read / 3.2M write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  809 tool calls (36 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.62 (32%)
  - by stage: lead $10.62 · triage $0.15 (1m) · gate $1.11 (9m) · report $0.46 (7m) · other $0.28 (1m)
- Avg direct per case (excl. overhead): $4.54
- Direct cost spread: avg $4.54 · median $3.71 · min $2.81 · max $9.43
- Loaded cost spread (direct + even overhead share): avg $6.64 · median $5.81 · min $4.91 · max $11.53
- Active-time spread: avg 13m · median 12m · min 8m · max 22m  ·  loaded: avg 40m · median 39m · min 35m · max 49m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2099 | blocked | $9.43 | $11.53 | 95,562 (in 448 / out 95k) | 22m | 49m | 4 | 207 (6) | 0 | 11 |
| ELITEA-2100 | blocked | $4.79 | $6.89 | 55,278 (in 295 / out 55k) | 16m | 43m | 4 | 129 (4) | 0 | 8 |
| ELITEA-2101 | blocked | $2.81 | $4.91 | 27,847 (in 150 / out 28k) | 8m | 35m | 2 | 74 (3) | 0 | 6 |
| ELITEA-2102 | blocked | $2.81 | $4.91 | 27,847 (in 150 / out 28k) | 8m | 35m | 2 | 74 (3) | 0 | 6 |
| ELITEA-2103 | blocked | $3.71 | $5.81 | 50,914 (in 207 / out 51k) | 12m | 39m | 2 | 96 (7) | 0 | 12 |
| ELITEA-2104 | blocked | $3.71 | $5.81 | 50,914 (in 207 / out 51k) | 12m | 39m | 2 | 96 (7) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $18.09 | 9 | 201,071 (in 892 / out 200k) | 97.6% | 48m | 450 (21) |
| test-automation-engineer | $11.16 | 11.15 | 160,549 (in 754 / out 160k) | 96.3% | 47m | 276 (14) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w03

Generated: 2026-09-14T11:44:33.527Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 302 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 9**  ·  automated 9
- Gate: green (3 runs)
- Findings reported: 112  ·  fix rounds: 1

## What it cost

- Total: $30.46  ·  3.8h active (cases 63m · lead 145m · stages 18m)  ·  14.15 dispatches
- Tokens: total 112,037,340  ·  **real work 307,783** (in 1,272 / out 306,511)  ·  cache 109.4M read / 2.4M write  ·  **cache hit rate 97.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  538 tool calls (20 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.47 (41%)
  - by stage: lead $10.62 · triage $0.19 (1m) · gate $1.12 (12m) · report $0.27 (4m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $0.88  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $3.38**
- Avg direct per case (excl. overhead): $2.00
- Direct cost spread: avg $2.00 · median $2.55 · min $0.54 · max $4.43
- Loaded cost spread (direct + even overhead share): avg $3.39 · median $3.94 · min $1.93 · max $5.82
- Active-time spread: avg 7m · median 7m · min 2m · max 14m  ·  loaded: avg 25m · median 25m · min 20m · max 32m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2105 | automated | $2.75 | $4.14 | 39,644 (in 113 / out 40k) | 12m | 30m | 1.3 | 52 (2) | 0.2 | 13 |
| ELITEA-2106 | automated | $2.75 | $4.14 | 39,644 (in 113 / out 40k) | 12m | 30m | 1.3 | 52 (2) | 0.2 | 13 |
| ELITEA-2107 | automated | $0.81 | $2.20 | 9,703 (in 48 / out 10k) | 3m | 21m | 0.8 | 20 (0) | 0.2 | 13 |
| ELITEA-2108 | automated | $0.81 | $2.20 | 9,703 (in 48 / out 10k) | 3m | 21m | 0.8 | 20 (0) | 0.2 | 13 |
| ELITEA-2109 | automated | $0.81 | $2.20 | 9,703 (in 48 / out 10k) | 3m | 21m | 0.8 | 20 (0) | 0.2 | 13 |
| ELITEA-2110 | automated | $2.55 | $3.94 | 29,860 (in 140 / out 30k) | 7m | 25m | 1.17 | 62 (3) | 0 | 13 |
| ELITEA-2111 | automated | $4.43 | $5.82 | 52,437 (in 221 / out 52k) | 14m | 32m | 3 | 97 (3) | 0 | 8 |
| ELITEA-2112 | automated | $2.55 | $3.94 | 29,860 (in 140 / out 30k) | 7m | 25m | 1.17 | 62 (3) | 0 | 13 |
| ELITEA-2113 | automated | $0.54 | $1.93 | 6,714 (in 49 / out 7k) | 2m | 20m | 0.67 | 16 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $14.27 | 9.15 | 192,472 (in 776 / out 192k) | 97.3% | 62m | 311 (15) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $5.57 | 5 | 76,263 (in 317 / out 76k) | 95.8% | 18m | 144 (4) |

---

# Batch cost — chat-remaining-w04

Generated: 2026-09-14T11:44:33.573Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 303 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 0**  ·  blocked 7  ·  already-covered 1
- Gate: red (1 runs)
- Findings reported: 104  ·  fix rounds: 1.99

## What it cost

- Total: $63.87  ·  5.6h active (cases 166m · lead 145m · stages 25m)  ·  13.15 dispatches
- Tokens: total 235,538,359  ·  **real work 516,040** (in 2,004 / out 514,036)  ·  cache 229.8M read / 5.3M write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  913 tool calls (32 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $13.54 (21%)
  - by stage: lead $10.62 · triage $0.28 (2m) · gate $2.04 (17m) · report $0.32 (5m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $3.24  ·  2 dispatch(es)  ·  10m
- Avg direct per case (excl. overhead): $7.19
- Direct cost spread: avg $7.19 · median $8.67 · min $1.42 · max $14.15
- Loaded cost spread (direct + even overhead share): avg $7.98 · median $6.85 · min $1.69 · max $15.84
- Active-time spread: avg 24m · median 20m · min 4m · max 55m  ·  loaded: avg 42m · median 34m · min 21m · max 76m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2115 | blocked | $8.67 | $10.36 | 78,903 (in 288 / out 79k) | 20m | 41m | 1.83 | 142 (5) | 0.33 | 16 |
| ELITEA-2116 | blocked | $8.67 | $10.36 | 78,903 (in 288 / out 79k) | 20m | 41m | 1.83 | 142 (5) | 0.33 | 16 |
| ELITEA-2117 | blocked | $1.42 | $3.11 | 20,089 (in 81 / out 20k) | 4m | 25m | 1.33 | 34 (1) | 0.33 | 16 |
| ELITEA-2456 | already-covered | n/a | $1.69 | 0 (incl. cache) | 0m | 21m | 0 | 0 (0) | 0 | 4 |
| ELITEA-2163 | blocked | $14.15 | $15.84 | 90,269 (in 363 / out 90k) | 55m | 76m | 1.5 | 179 (6) | 0.25 | 13 |
| ELITEA-2164 | blocked | $14.15 | $15.84 | 90,269 (in 363 / out 90k) | 55m | 76m | 1.5 | 179 (6) | 0.25 | 13 |
| ELITEA-2165 | blocked | $1.64 | $3.33 | 24,445 (in 80 / out 24k) | 6m | 27m | 1 | 37 (1) | 0.25 | 13 |
| ELITEA-2463 | blocked | $1.64 | $3.33 | 24,445 (in 80 / out 24k) | 6m | 27m | 1 | 37 (1) | 0.25 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $45.69 | 8.15 | 348,705 (in 1k / out 347k) | 97.5% | 164m | 654 (26) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $7.56 | 5 | 128,287 (in 411 / out 128k) | 96.4% | 26m | 176 (5) |

Unattributed (no dispatch named them in any captured session): ELITEA-2456

---

# Batch cost — chat-remaining-w05

Generated: 2026-09-14T11:44:33.617Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 300 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 0**  ·  blocked 6
- Gate: red (1 runs)
- Findings reported: 61  ·  fix rounds: 2.0100000000000002

## What it cost

- Total: $31.45  ·  3.6h active (cases 63m · lead 145m · stages 11m)  ·  16.15 dispatches
- Tokens: total 114,157,208  ·  **real work 301,872** (in 1,297 / out 300,575)  ·  cache 111.3M read / 2.6M write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  570 tool calls (15 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.39 (39%)
  - by stage: lead $10.62 · triage $0.18 (1m) · gate $1.08 (6m) · report $0.23 (3m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $2.37  ·  2 dispatch(es)  ·  9m
- Avg direct per case (excl. overhead): $3.18
- Direct cost spread: avg $3.18 · median $3.24 · min $1.81 · max $4.29
- Loaded cost spread (direct + even overhead share): avg $5.24 · median $5.30 · min $3.87 · max $6.35
- Active-time spread: avg 11m · median 11m · min 6m · max 14m  ·  loaded: avg 37m · median 37m · min 32m · max 40m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2118 | blocked | $4.12 | $6.18 | 44,327 (in 182 / out 44k) | 14m | 40m | 2.5 | 91 (2) | 0.67 | 14 |
| ELITEA-2119 | blocked | $4.12 | $6.18 | 44,327 (in 182 / out 44k) | 14m | 40m | 2.5 | 91 (2) | 0.67 | 14 |
| ELITEA-2120 | blocked | $1.81 | $3.87 | 18,848 (in 97 / out 19k) | 6m | 32m | 2 | 44 (1) | 0.67 | 14 |
| ELITEA-2133 | blocked | $2.36 | $4.42 | 32,713 (in 118 / out 33k) | 8m | 34m | 1.5 | 57 (1) | 0 | 6 |
| ELITEA-2134 | blocked | $2.36 | $4.42 | 32,713 (in 118 / out 33k) | 8m | 34m | 1.5 | 57 (1) | 0 | 6 |
| ELITEA-2457 | blocked | $4.29 | $6.35 | 50,821 (in 241 / out 51k) | 13m | 39m | 3 | 102 (5) | 0 | 7 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $15.68 | 10.15 | 188,472 (in 833 / out 188k) | 97.3% | 55m | 363 (12) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $5.15 | 6 | 74,352 (in 285 / out 74k) | 94.0% | 18m | 124 (2) |

---

# Batch cost — chat-remaining-w06

Generated: 2026-09-14T11:44:33.661Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 298 other-batch dispatch(es) excluded._

## What happened

- Cases: 11  ·  **delivered: 7**  ·  automated 7  ·  already-covered 4
- Gate: green (3 runs)
- Findings reported: 80  ·  fix rounds: 1

## What it cost

- Total: $50.26  ·  4.6h active (cases 123m · lead 145m · stages 10m)  ·  18.15 dispatches
- Tokens: total 191,188,169  ·  **real work 517,325** (in 2,029 / out 515,296)  ·  cache 187.4M read / 3.2M write  ·  **cache hit rate 98.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  948 tool calls (41 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.04 (24%)
  - by stage: lead $10.62 · triage $0.16 (1m) · gate $0.73 (4m) · report $0.24 (4m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $1.71  ·  1 dispatch(es)  ·  6m
- **Per delivered case (incl. overhead): $7.18**
- Avg direct per case (excl. overhead): $3.82
- Direct cost spread: avg $3.82 · median $3.59 · min $0.66 · max $7.55
- Loaded cost spread (direct + even overhead share): avg $4.56 · median $4.32 · min $1.09 · max $8.64
- Active-time spread: avg 12m · median 12m · min 2m · max 24m  ·  loaded: avg 25m · median 26m · min 14m · max 38m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2121 | automated | $7.55 | $8.64 | 82,670 (in 303 / out 82k) | 24m | 38m | 2.5 | 156 (4) | 0.5 | 16 |
| ELITEA-2122 | automated | $4.64 | $5.73 | 57,447 (in 247 / out 57k) | 16m | 30m | 3 | 115 (3) | 0 | 4 |
| ELITEA-2123 | already-covered | $2.06 | $3.15 | 19,518 (in 109 / out 19k) | 5m | 19m | 0.5 | 55 (2) | 0 | 3 |
| ELITEA-2124 | already-covered | $2.56 | $3.65 | 36,765 (in 84 / out 37k) | 11m | 25m | 0.5 | 47 (8) | 0 | 3 |
| ELITEA-2125 | automated | $3.23 | $4.32 | 44,527 (in 136 / out 44k) | 12m | 26m | 1.5 | 65 (8) | 0 | 11 |
| ELITEA-2126 | already-covered | n/a | $1.09 | 0 (incl. cache) | 0m | 14m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2127 | already-covered | $2.06 | $3.15 | 19,518 (in 109 / out 19k) | 5m | 19m | 0.5 | 55 (2) | 0 | 3 |
| ELITEA-2128 | automated | $3.95 | $5.04 | 46,999 (in 190 / out 47k) | 12m | 26m | 1.5 | 84 (4) | 0 | 5 |
| ELITEA-2129 | automated | $3.95 | $5.04 | 46,999 (in 190 / out 47k) | 12m | 26m | 1.5 | 84 (4) | 0 | 5 |
| ELITEA-2130 | automated | $7.55 | $8.64 | 82,670 (in 303 / out 82k) | 24m | 38m | 2.5 | 156 (4) | 0.5 | 16 |
| ELITEA-2131 | automated | $0.66 | $1.75 | 7,763 (in 52 / out 8k) | 2m | 16m | 1 | 18 (0) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $32.65 | 12.15 | 375,193 (in 1k / out 374k) | 98.4% | 107m | 688 (37) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $6.99 | 6 | 103,084 (in 355 / out 103k) | 95.7% | 23m | 177 (3) |

Unattributed (no dispatch named them in any captured session): ELITEA-2126

---

# Batch cost — chat-remaining-w07

Generated: 2026-09-14T11:44:33.706Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 296 other-batch dispatch(es) excluded._

## What happened

- Cases: 12  ·  **delivered: 8**  ·  automated 8  ·  blocked 4
- Gate: green (3 runs)
- Findings reported: 138  ·  fix rounds: 1.9800000000000002

## What it cost

- Total: $72.54  ·  5.9h active (cases 178m · lead 145m · stages 32m)  ·  20.15 dispatches
- Tokens: total 279,184,825  ·  **real work 762,645** (in 3,227 / out 759,418)  ·  cache 274.0M read / 4.4M write  ·  **cache hit rate 98.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1253 tool calls (44 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $13.69 (19%)
  - by stage: lead $10.62 · triage $0.40 (2m) · gate $1.71 (19m) · report $0.69 (10m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $3.02  ·  2 dispatch(es)  ·  10m
- **Per delivered case (incl. overhead): $9.07**
- Avg direct per case (excl. overhead): $4.90
- Direct cost spread: avg $4.90 · median $4.43 · min $0.31 · max $10.95
- Loaded cost spread (direct + even overhead share): avg $6.04 · median $5.57 · min $1.45 · max $12.09
- Active-time spread: avg 15m · median 15m · min 1m · max 31m  ·  loaded: avg 30m · median 30m · min 16m · max 46m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2136 | automated | $3.51 | $4.65 | 45,378 (in 119 / out 45k) | 13m | 28m | 0.9 | 57 (3) | 0 | 7 |
| ELITEA-2138 | automated | $3.51 | $4.65 | 45,378 (in 119 / out 45k) | 13m | 28m | 0.9 | 57 (3) | 0 | 7 |
| ELITEA-2139 | automated | $0.31 | $1.45 | 3,759 (in 20 / out 4k) | 1m | 16m | 0.4 | 7 (0) | 0 | 7 |
| ELITEA-2140 | automated | $0.31 | $1.45 | 3,759 (in 20 / out 4k) | 1m | 16m | 0.4 | 7 (0) | 0 | 7 |
| ELITEA-2141 | automated | $0.31 | $1.45 | 3,759 (in 20 / out 4k) | 1m | 16m | 0.4 | 7 (0) | 0 | 7 |
| ELITEA-2142 | blocked | $10.95 | $12.09 | 118,760 (in 604 / out 118k) | 31m | 46m | 2.58 | 198 (6) | 0.33 | 16 |
| ELITEA-2143 | blocked | $10.74 | $11.88 | 116,503 (in 598 / out 116k) | 31m | 46m | 2.08 | 196 (6) | 0.33 | 16 |
| ELITEA-2144 | blocked | $0.49 | $1.63 | 5,818 (in 21 / out 6k) | 2m | 17m | 0.25 | 10 (0) | 0 | 4 |
| ELITEA-2145 | blocked | $7.44 | $8.58 | 69,025 (in 232 / out 69k) | 19m | 34m | 1.58 | 122 (3) | 0.33 | 16 |
| ELITEA-2146 | automated | $8.07 | $9.21 | 90,761 (in 326 / out 90k) | 25m | 40m | 2.67 | 163 (5) | 0.33 | 17 |
| ELITEA-2147 | automated | $7.86 | $9.00 | 88,504 (in 320 / out 88k) | 24m | 39m | 2.17 | 161 (5) | 0.33 | 17 |
| ELITEA-2148 | automated | $5.35 | $6.49 | 58,305 (in 210 / out 58k) | 17m | 32m | 1.67 | 106 (2) | 0.33 | 17 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $40.56 | 11.15 | 433,692 (in 2k / out 432k) | 98.6% | 139m | 682 (23) |
| qa-engineer | $21.36 | 9 | 289,905 (in 2k / out 288k) | 97.6% | 72m | 488 (20) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w08

Generated: 2026-09-14T11:44:33.751Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 298 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 7**  ·  automated 7
- Gate: green (3 runs)
- Findings reported: 38  ·  fix rounds: 0

## What it cost

- Total: $42.42  ·  4.2h active (cases 94m · lead 145m · stages 16m)  ·  18.15 dispatches
- Tokens: total 159,017,307  ·  **real work 448,426** (in 1,750 / out 446,676)  ·  cache 155.6M read / 3.0M write  ·  **cache hit rate 98.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  736 tool calls (26 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.59 (30%)
  - by stage: lead $10.62 · triage $0.15 (1m) · gate $1.22 (10m) · report $0.31 (4m) · other $0.28 (1m)
- **Per delivered case (incl. overhead): $6.06**
- Avg direct per case (excl. overhead): $4.26
- Direct cost spread: avg $4.26 · median $3.59 · min $2.26 · max $6.90
- Loaded cost spread (direct + even overhead share): avg $6.06 · median $5.39 · min $4.06 · max $8.70
- Active-time spread: avg 13m · median 13m · min 8m · max 20m  ·  loaded: avg 36m · median 36m · min 31m · max 43m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2150 | automated | $4.64 | $6.44 | 53,379 (in 275 / out 53k) | 13m | 36m | 3 | 115 (4) | 0 | 9 |
| ELITEA-2151 | automated | $3.59 | $5.39 | 58,338 (in 177 / out 58k) | 14m | 37m | 3 | 72 (1) | 0 | 4 |
| ELITEA-2152 | automated | $6.90 | $8.70 | 70,724 (in 259 / out 70k) | 20m | 43m | 1.5 | 121 (6) | 0 | 6 |
| ELITEA-2153 | automated | $6.90 | $8.70 | 70,724 (in 259 / out 70k) | 20m | 43m | 1.5 | 121 (6) | 0 | 6 |
| ELITEA-2154 | automated | $3.27 | $5.07 | 48,073 (in 177 / out 48k) | 11m | 34m | 3 | 73 (0) | 0 | 5 |
| ELITEA-2155 | automated | $2.26 | $4.06 | 33,345 (in 98 / out 33k) | 8m | 31m | 1.5 | 45 (2) | 0 | 4 |
| ELITEA-2156 | automated | $2.26 | $4.06 | 33,345 (in 98 / out 33k) | 8m | 31m | 1.5 | 45 (2) | 0 | 4 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $25.59 | 12.15 | 313,497 (in 1k / out 312k) | 98.1% | 89m | 504 (23) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $6.21 | 6 | 95,881 (in 309 / out 96k) | 95.1% | 19m | 149 (2) |

---

# Batch cost — chat-remaining-w09

Generated: 2026-09-14T11:44:33.796Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 301 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 4**  ·  automated 4  ·  already-covered 4
- Gate: green (3 runs)
- Findings reported: 44  ·  fix rounds: 1

## What it cost

- Total: $32.49  ·  3.9h active (cases 67m · lead 145m · stages 21m)  ·  15.15 dispatches
- Tokens: total 118,786,825  ·  **real work 320,461** (in 7,484 / out 312,977)  ·  cache 115.9M read / 2.6M write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  571 tool calls (16 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.32 (38%)
  - by stage: lead $10.62 · triage $0.27 (2m) · gate $0.93 (15m) · report $0.22 (3m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $1.40  ·  1 dispatch(es)  ·  4m
- **Per delivered case (incl. overhead): $8.12**
- Avg direct per case (excl. overhead): $2.52
- Direct cost spread: avg $2.52 · median $1.84 · min $0.94 · max $5.45
- Loaded cost spread (direct + even overhead share): avg $4.06 · median $3.38 · min $2.48 · max $6.99
- Active-time spread: avg 8m · median 7m · min 3m · max 17m  ·  loaded: avg 29m · median 28m · min 24m · max 38m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2157 | automated | $5.45 | $6.99 | 66,188 (in 3k / out 63k) | 17m | 38m | 2.5 | 123 (4) | 0.5 | 13 |
| ELITEA-2158 | automated | $5.45 | $6.99 | 66,188 (in 3k / out 63k) | 17m | 38m | 2.5 | 123 (4) | 0.5 | 13 |
| ELITEA-2159 | already-covered | $0.99 | $2.53 | 13,258 (in 38 / out 13k) | 3m | 24m | 1 | 19 (0) | 0 | 1 |
| ELITEA-2160 | automated | $2.46 | $4.00 | 28,806 (in 121 / out 29k) | 10m | 31m | 1.5 | 52 (1) | 0 | 7 |
| ELITEA-2161 | automated | $2.46 | $4.00 | 28,806 (in 121 / out 29k) | 10m | 31m | 1.5 | 52 (1) | 0 | 7 |
| ELITEA-2461 | already-covered | $1.21 | $2.75 | 17,118 (in 48 / out 17k) | 4m | 25m | 1 | 24 (0) | 0 | 1 |
| ELITEA-2462 | already-covered | $0.94 | $2.48 | 13,077 (in 40 / out 13k) | 3m | 24m | 1 | 20 (1) | 0 | 1 |
| ELITEA-2460 | already-covered | $1.21 | $2.75 | 12,908 (in 44 / out 13k) | 3m | 24m | 1 | 22 (0) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $16.34 | 9.15 | 197,871 (in 7k / out 191k) | 97.6% | 68m | 353 (10) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |
| qa-engineer | $5.53 | 6 | 83,542 (in 321 / out 83k) | 94.1% | 19m | 135 (5) |

---

# Batch cost — chat-remaining-w10

Generated: 2026-09-14T11:44:33.841Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 298 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 0**  ·  merged-ungated 5  ·  already-covered 2
- Gate: incomplete
- Findings reported: 63  ·  fix rounds: 2

## What it cost

- Total: $58.64  ·  4.7h active (cases 129m · lead 145m · stages 11m)  ·  18.15 dispatches
- Tokens: total 224,557,163  ·  **real work 500,136** (in 2,198 / out 497,938)  ·  cache 220.0M read / 4.0M write  ·  **cache hit rate 98.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1006 tool calls (45 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.32 (21%)
  - by stage: lead $10.62 · triage $0.23 (2m) · gate $0.91 (4m) · report $0.28 (4m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $4.48  ·  2 dispatch(es)  ·  13m
- Avg direct per case (excl. overhead): $6.62
- Direct cost spread: avg $6.62 · median $6.17 · min $2.34 · max $15.68
- Loaded cost spread (direct + even overhead share): avg $8.38 · median $7.93 · min $4.10 · max $17.44
- Active-time spread: avg 18m · median 14m · min 7m · max 38m  ·  loaded: avg 40m · median 36m · min 29m · max 60m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2169 | already-covered | $2.34 | $4.10 | 29,075 (in 94 / out 29k) | 9m | 31m | 1 | 48 (0) | 0 | 3 |
| ELITEA-2171 | already-covered | $2.90 | $4.66 | 26,599 (in 126 / out 26k) | 7m | 29m | 0.5 | 63 (4) | 0 | 4 |
| ELITEA-2172 | merged-ungated | $15.68 | $17.44 | 120,684 (in 617 / out 120k) | 38m | 60m | 3.5 | 291 (14) | 0 | 14 |
| ELITEA-2173 | merged-ungated | $6.17 | $7.93 | 53,501 (in 237 / out 53k) | 14m | 36m | 2 | 120 (6) | 0 | 10 |
| ELITEA-2174 | merged-ungated | $6.17 | $7.93 | 53,501 (in 237 / out 53k) | 14m | 36m | 2 | 120 (6) | 0 | 10 |
| ELITEA-2175 | merged-ungated | $8.01 | $9.77 | 77,869 (in 302 / out 78k) | 27m | 49m | 3.5 | 139 (8) | 1.5 | 11 |
| ELITEA-2176 | merged-ungated | $5.04 | $6.80 | 61,656 (in 208 / out 61k) | 20m | 42m | 2.5 | 97 (3) | 0.5 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $29.85 | 11.15 | 287,527 (in 1k / out 286k) | 97.9% | 94m | 542 (30) |
| qa-engineer | $18.17 | 7 | 173,561 (in 757 / out 173k) | 98.0% | 44m | 381 (14) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w11

Generated: 2026-09-14T11:44:33.887Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 298 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 0**  ·  blocked 5  ·  already-covered 2
- Gate: red (1 runs)
- Findings reported: 51  ·  fix rounds: 5

## What it cost

- Total: $79.37  ·  5.4h active (cases 170m · lead 145m · stages 12m)  ·  18.15 dispatches
- Tokens: total 316,248,286  ·  **real work 642,358** (in 3,721 / out 638,637)  ·  cache 311.3M read / 4.3M write  ·  **cache hit rate 98.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1389 tool calls (50 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.59 (16%)
  - by stage: lead $10.62 · triage $0.27 (2m) · gate $1.21 (6m) · report $0.20 (3m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $11.74  ·  5 dispatch(es)  ·  38m
- Avg direct per case (excl. overhead): $13.36
- Direct cost spread: avg $13.36 · median $1.97 · min $1.17 · max $38.34
- Loaded cost spread (direct + even overhead share): avg $11.34 · median $2.97 · min $1.80 · max $40.14
- Active-time spread: avg 34m · median 6m · min 5m · max 79m  ·  loaded: avg 46m · median 27m · min 22m · max 101m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2188 | blocked | $38.34 | $40.14 | 257,848 (in 1k / out 256k) | 79m | 101m | 7 | 694 (19) | 3 | 18 |
| ELITEA-2189 | blocked | $1.17 | $2.97 | 19,494 (in 488 / out 19k) | 5m | 27m | 0.5 | 35 (1) | 0 | 4 |
| ELITEA-2190 | blocked | $1.17 | $2.97 | 19,494 (in 488 / out 19k) | 5m | 27m | 0.5 | 35 (1) | 0 | 4 |
| ELITEA-2191 | blocked | n/a | $1.80 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 4 |
| ELITEA-2192 | already-covered | $1.97 | $3.77 | 26,052 (in 75 / out 26k) | 6m | 28m | 0.5 | 41 (3) | 0 | 3 |
| ELITEA-2193 | blocked | $24.14 | $25.94 | 237,834 (in 907 / out 237k) | 75m | 97m | 6.5 | 448 (23) | 2 | 15 |
| ELITEA-2194 | already-covered | n/a | $1.80 | 0 (incl. cache) | 0m | 22m | 0 | 0 (0) | 0 | 3 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $51.46 | 9.15 | 344,804 (in 2k / out 343k) | 98.8% | 123m | 884 (36) |
| qa-engineer | $17.29 | 9 | 258,506 (in 2k / out 257k) | 97.3% | 57m | 422 (13) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2191, ELITEA-2194

---

# Batch cost — chat-remaining-w12

Generated: 2026-09-14T11:44:33.932Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 295 other-batch dispatch(es) excluded._

## What happened

- Cases: 11  ·  **delivered: 0**  ·  blocked 6  ·  merged-ungated 5
- Gate: incomplete
- Findings reported: 116  ·  fix rounds: 4

## What it cost

- Total: $86.52  ·  5.9h active (cases 193m · lead 145m · stages 13m)  ·  21.15 dispatches
- Tokens: total 339,782,715  ·  **real work 807,713** (in 3,137 / out 804,576)  ·  cache 334.2M read / 4.8M write  ·  **cache hit rate 98.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1477 tool calls (59 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.40 (14%)
  - by stage: lead $10.62 · triage $0.24 (2m) · gate $0.87 (4m) · report $0.39 (6m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $11.28  ·  4 dispatch(es)  ·  42m
- Avg direct per case (excl. overhead): $6.74
- Direct cost spread: avg $6.74 · median $5.47 · min $0.60 · max $14.87
- Loaded cost spread (direct + even overhead share): avg $7.87 · median $6.60 · min $1.73 · max $16.00
- Active-time spread: avg 18m · median 17m · min 2m · max 33m  ·  loaded: avg 32m · median 31m · min 16m · max 47m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2177 | blocked | $14.87 | $16.00 | 121,350 (in 481 / out 121k) | 33m | 47m | 2 | 240 (8) | 0.83 | 12 |
| ELITEA-2178 | blocked | $14.28 | $15.41 | 116,214 (in 460 / out 116k) | 30m | 44m | 1.83 | 230 (8) | 0.67 | 12 |
| ELITEA-2179 | merged-ungated | $5.47 | $6.60 | 59,316 (in 233 / out 59k) | 15m | 29m | 1.67 | 107 (2) | 0.17 | 8 |
| ELITEA-2182 | blocked | $8.12 | $9.25 | 82,775 (in 330 / out 82k) | 23m | 37m | 3.17 | 165 (9) | 0.17 | 3 |
| ELITEA-2183 | blocked | $5.49 | $6.62 | 52,677 (in 212 / out 52k) | 14m | 28m | 1.17 | 107 (8) | 0.17 | 3 |
| ELITEA-2184 | merged-ungated | $4.66 | $5.79 | 60,219 (in 195 / out 60k) | 17m | 31m | 1.83 | 95 (6) | 0.33 | 18 |
| ELITEA-2185 | merged-ungated | $4.66 | $5.79 | 60,219 (in 195 / out 60k) | 17m | 31m | 1.83 | 95 (6) | 0.33 | 18 |
| ELITEA-2186 | blocked | $0.60 | $1.73 | 5,137 (in 21 / out 5k) | 2m | 16m | 0.17 | 11 (0) | 0.17 | 4 |
| ELITEA-2187 | merged-ungated | $1.63 | $2.76 | 23,806 (in 80 / out 24k) | 7m | 21m | 1.33 | 38 (1) | 0.33 | 18 |
| ELITEA-2465 | blocked | $9.46 | $10.59 | 85,920 (in 301 / out 86k) | 22m | 36m | 1.5 | 150 (4) | 0.83 | 12 |
| ELITEA-2466 | merged-ungated | $4.87 | $6.00 | 54,180 (in 212 / out 54k) | 13m | 27m | 1.5 | 96 (2) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $52.87 | 13.15 | 522,958 (in 2k / out 521k) | 98.6% | 142m | 934 (40) |
| qa-engineer | $23.02 | 8 | 245,707 (in 941 / out 245k) | 98.0% | 65m | 460 (18) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w13

Generated: 2026-09-14T11:44:33.976Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 291 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 0**  ·  blocked 6
- Gate: red (1 runs)
- Findings reported: 56  ·  fix rounds: 3

## What it cost

- Total: $52.40  ·  4.7h active (cases 120m · lead 145m · stages 17m)  ·  25.15 dispatches
- Tokens: total 189,751,674  ·  **real work 574,672** (in 2,157 / out 572,515)  ·  cache 184.9M read / 4.3M write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  953 tool calls (45 err, 95% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.82 (24%)
  - by stage: lead $10.62 · triage $0.24 (2m) · gate $1.09 (5m) · report $0.59 (9m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $6.52  ·  3 dispatch(es)  ·  23m
- Avg direct per case (excl. overhead): $6.60
- Direct cost spread: avg $6.60 · median $5.68 · min $2.72 · max $12.10
- Loaded cost spread (direct + even overhead share): avg $8.74 · median $7.82 · min $4.86 · max $14.24
- Active-time spread: avg 20m · median 19m · min 7m · max 32m  ·  loaded: avg 47m · median 46m · min 34m · max 59m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2195 | blocked | $5.29 | $7.43 | 57,959 (in 253 / out 58k) | 15m | 42m | 3 | 118 (8) | 0 | 5 |
| ELITEA-2196 | blocked | $12.10 | $14.24 | 131,306 (in 465 / out 131k) | 32m | 59m | 5 | 218 (6) | 1 | 10 |
| ELITEA-2198 | blocked | $2.72 | $4.86 | 34,671 (in 139 / out 35k) | 7m | 34m | 3 | 62 (1) | 0 | 6 |
| ELITEA-2199 | blocked | $5.68 | $7.82 | 75,583 (in 241 / out 75k) | 19m | 46m | 3 | 119 (6) | 0.5 | 13 |
| ELITEA-2201 | blocked | $8.12 | $10.26 | 97,894 (in 389 / out 98k) | 28m | 55m | 4 | 177 (10) | 1 | 9 |
| ELITEA-2467 | blocked | $5.68 | $7.82 | 75,583 (in 241 / out 75k) | 19m | 46m | 3 | 119 (6) | 0.5 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $30.16 | 16.15 | 370,400 (in 1k / out 369k) | 97.7% | 98m | 615 (35) |
| qa-engineer | $11.62 | 9 | 165,224 (in 511 / out 165k) | 95.8% | 38m | 255 (9) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w14

Generated: 2026-09-14T11:44:34.020Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 291 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 7**  ·  automated 5  ·  merged-sanctioned-red 2
- Gate: green (3 runs)
- Findings reported: 97  ·  fix rounds: 3

## What it cost

- Total: $69.90  ·  5.8h active (cases 177m · lead 145m · stages 30m)  ·  25.15 dispatches
- Tokens: total 259,489,728  ·  **real work 724,556** (in 2,833 / out 721,723)  ·  cache 253.7M read / 5.1M write  ·  **cache hit rate 98.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1291 tool calls (44 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $13.41 (19%)
  - by stage: lead $10.62 · triage $0.25 (2m) · gate $1.90 (21m) · report $0.37 (6m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $6.90  ·  3 dispatch(es)  ·  24m
- **Per delivered case (incl. overhead): $9.99**
- Avg direct per case (excl. overhead): $8.07
- Direct cost spread: avg $8.07 · median $7.50 · min $5.94 · max $13.61
- Loaded cost spread (direct + even overhead share): avg $9.99 · median $9.42 · min $7.86 · max $15.53
- Active-time spread: avg 25m · median 23m · min 16m · max 45m  ·  loaded: avg 50m · median 48m · min 41m · max 70m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2205 | merged-sanctioned-red | $5.94 | $7.86 | 62,411 (in 261 / out 62k) | 16m | 41m | 2 | 124 (4) | 0 | 11 |
| ELITEA-2206 | automated | $13.61 | $15.53 | 177,453 (in 613 / out 177k) | 45m | 70m | 8 | 298 (12) | 2 | 17 |
| ELITEA-2207 | automated | $8.01 | $9.93 | 75,340 (in 316 / out 75k) | 23m | 48m | 2 | 154 (7) | 0 | 10 |
| ELITEA-2208 | automated | $7.50 | $9.42 | 86,390 (in 321 / out 86k) | 27m | 52m | 3 | 148 (3) | 0.5 | 19 |
| ELITEA-2468 | merged-sanctioned-red | $5.94 | $7.86 | 62,411 (in 261 / out 62k) | 16m | 41m | 2 | 124 (4) | 0 | 11 |
| ELITEA-2469 | automated | $8.01 | $9.93 | 75,340 (in 316 / out 75k) | 23m | 48m | 2 | 154 (7) | 0 | 10 |
| ELITEA-2470 | automated | $7.50 | $9.42 | 86,390 (in 321 / out 86k) | 27m | 52m | 3 | 148 (3) | 0.5 | 19 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $31.24 | 13.15 | 368,089 (in 1k / out 367k) | 97.9% | 128m | 615 (19) |
| qa-engineer | $28.04 | 12 | 317,419 (in 1k / out 316k) | 97.7% | 78m | 593 (24) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — chat-remaining-w15

Generated: 2026-09-14T11:44:34.064Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_2 session(s) also served other batches — their session-level figures are split evenly; 286 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 0**  ·  blocked 4  ·  already-covered 4
- Gate: red (1 runs)
- Findings reported: 84  ·  fix rounds: 7

## What it cost

- Total: $94.73  ·  7.5h active (cases 254m · lead 179m · stages 20m)  ·  39.15 dispatches
- Tokens: total 259,875,185  ·  **real work 978,203** (in 3,093 / out 975,110)  ·  cache 251.3M read / 7.6M write  ·  **cache hit rate 97.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 132 turns  ·  1463 tool calls (58 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $19.85 (21%)
  - by stage: lead $16.11 · triage $0.31 (2m) · gate $2.85 (12m) · report $0.30 (5m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $17.59  ·  7 dispatch(es)  ·  56m
- Avg direct per case (excl. overhead): $9.36
- Direct cost spread: avg $9.36 · median $5.12 · min $0.41 · max $31.80
- Loaded cost spread (direct + even overhead share): avg $11.84 · median $7.60 · min $2.89 · max $34.28
- Active-time spread: avg 32m · median 14m · min 1m · max 95m  ·  loaded: avg 57m · median 39m · min 26m · max 120m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2209 | blocked | $6.27 | $8.75 | 63,608 (in 301 / out 63k) | 18m | 43m | 4 | 135 (10) | 0 | 8 |
| ELITEA-2210 | blocked | $31.80 | $34.28 | 333,045 (in 774 / out 332k) | 95m | 120m | 14 | 399 (10) | 3.5 | 24 |
| ELITEA-2216 | blocked | $15.07 | $17.55 | 158,768 (in 593 / out 158k) | 55m | 80m | 6 | 279 (11) | 1 | 18 |
| ELITEA-2217 | blocked | $16.54 | $19.02 | 214,153 (in 713 / out 213k) | 73m | 98m | 9 | 346 (14) | 2 | 26 |
| ELITEA-2471 | already-covered | $0.41 | $2.89 | 6,913 (in 15 / out 7k) | 1m | 26m | 0.33 | 10 (0) | 0 | 2 |
| ELITEA-2472 | already-covered | $0.41 | $2.89 | 6,913 (in 15 / out 7k) | 1m | 26m | 0.33 | 10 (0) | 0 | 2 |
| ELITEA-2473 | already-covered | $0.41 | $2.89 | 6,913 (in 15 / out 7k) | 1m | 26m | 0.33 | 10 (0) | 0 | 2 |
| ELITEA-2474 | already-covered | $3.97 | $6.45 | 42,696 (in 91 / out 43k) | 10m | 35m | 2 | 49 (1) | 0.5 | 2 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $39.83 | 22 | 471,723 (in 1k / out 470k) | 96.0% | 116m | 654 (27) |
| test-automation-engineer | $38.79 | 17.15 | 433,097 (in 2k / out 432k) | 97.0% | 159m | 685 (29) |
| test-automation-lead | $16.11 | 0 | 73,384 (in 264 / out 73k) | 99.2% | 179m | 124 (2) |

---

# Batch cost — chat-remaining-w16

Generated: 2026-09-14T11:44:34.107Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 287 other-batch dispatch(es) excluded._

## What happened

- Cases: 7  ·  **delivered: 7**  ·  automated 7
- Gate: green (3 runs)
- Findings reported: 81  ·  fix rounds: 4

## What it cost

- Total: $77.13  ·  5.8h active (cases 174m · lead 145m · stages 27m)  ·  29.15 dispatches
- Tokens: total 293,680,386  ·  **real work 716,653** (in 3,129 / out 713,524)  ·  cache 287.6M read / 5.4M write  ·  **cache hit rate 98.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 90 turns  ·  1395 tool calls (42 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $12.71 (16%)
  - by stage: lead $10.62 · triage $0.27 (2m) · gate $1.20 (19m) · report $0.34 (5m) · other $0.28 (1m)
- Rework (fix rounds — already inside per-case direct): $9.48  ·  4 dispatch(es)  ·  30m
- **Per delivered case (incl. overhead): $11.02**
- Avg direct per case (excl. overhead): $9.20
- Direct cost spread: avg $9.20 · median $9.17 · min $6.37 · max $13.37
- Loaded cost spread (direct + even overhead share): avg $11.02 · median $10.99 · min $8.19 · max $15.19
- Active-time spread: avg 25m · median 25m · min 18m · max 36m  ·  loaded: avg 50m · median 50m · min 43m · max 61m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2073 | automated | $6.37 | $8.19 | 75,157 (in 265 / out 75k) | 21m | 46m | 2.5 | 125 (3) | 0.5 | 17 |
| ELITEA-2074 | automated | $6.37 | $8.19 | 75,157 (in 265 / out 75k) | 21m | 46m | 2.5 | 125 (3) | 0.5 | 17 |
| ELITEA-2076 | automated | $13.37 | $15.19 | 125,267 (in 545 / out 125k) | 36m | 61m | 5 | 257 (6) | 1 | 14 |
| ELITEA-2077 | automated | $11.82 | $13.64 | 89,823 (in 485 / out 89k) | 25m | 50m | 3 | 221 (9) | 0 | 5 |
| ELITEA-2078 | automated | $9.99 | $11.81 | 104,897 (in 413 / out 104k) | 25m | 50m | 5 | 198 (5) | 1 | 10 |
| ELITEA-2081 | automated | $9.17 | $10.99 | 95,566 (in 377 / out 95k) | 28m | 53m | 5 | 179 (4) | 1 | 10 |
| ELITEA-2084 | automated | $7.32 | $9.14 | 66,314 (in 317 / out 66k) | 18m | 43m | 3 | 146 (5) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $54.97 | 18.15 | 513,339 (in 2k / out 511k) | 98.4% | 164m | 1057 (39) |
| qa-engineer | $11.54 | 11 | 164,266 (in 577 / out 164k) | 94.6% | 36m | 255 (2) |
| test-automation-lead | $10.62 | 0 | 39,049 (in 180 / out 39k) | 99.3% | 145m | 83 (1) |

---

# Batch cost — credentials-w01

Generated: 2026-09-14T11:44:34.115Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_2 session(s) also served other batches — their session-level figures are split evenly; 13 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 9**  ·  automated 9
- Gate: green ([object Object],[object Object],[object Object] runs)
- Gate record (script-authored): green at 2026-08-22T11:32:24.700Z (2 run record(s))
- Findings reported: 0  ·  fix rounds: 4

## What it cost

- Total: $146.92  ·  6.9h active (cases 242m · lead 135m · stages 36m)  ·  33.67 dispatches
- Tokens: total 188,689,613  ·  **real work 958,537** (in 2,832 / out 955,705)  ·  cache 182.0M read / 5.8M write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 73 turns  ·  1311 tool calls (39 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $23.65 (16%)
  - by stage: lead $10.79 · triage $0.21 (1m) · gate $3.20 (15m) · other $9.46 (20m)
- Rework (fix rounds — already inside per-case direct): $11.24  ·  4 dispatch(es)  ·  23m
- **Per delivered case (incl. overhead): $16.32**
- Avg direct per case (excl. overhead): $13.69
- Direct cost spread: avg $13.69 · median $12.42 · min $9.07 · max $19.73
- Loaded cost spread (direct + even overhead share): avg $16.32 · median $15.05 · min $11.70 · max $22.36
- Active-time spread: avg 27m · median 27m · min 18m · max 39m  ·  loaded: avg 46m · median 46m · min 37m · max 58m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1964 | automated | $12.42 | $15.05 | 72,562 (in 257 / out 72k) | 21m | 40m | 3 | 126 (4) | 0 | 0 |
| ELITEA-1966 | automated | $10.49 | $13.12 | 64,532 (in 198 / out 64k) | 18m | 37m | 2.5 | 92 (3) | 0.5 | 0 |
| ELITEA-1973 | automated | $10.49 | $13.12 | 64,532 (in 198 / out 64k) | 18m | 37m | 2.5 | 92 (3) | 0.5 | 0 |
| ELITEA-1967 | automated | $12.16 | $14.79 | 81,662 (in 241 / out 81k) | 27m | 46m | 3 | 103 (4) | 0 | 0 |
| ELITEA-1968 | automated | $15.75 | $18.38 | 102,894 (in 270 / out 103k) | 30m | 49m | 3.5 | 142 (4) | 1 | 0 |
| ELITEA-1969 | automated | $15.75 | $18.38 | 102,894 (in 270 / out 103k) | 30m | 49m | 3.5 | 142 (4) | 1 | 0 |
| ELITEA-1970 | automated | $17.39 | $20.02 | 130,755 (in 297 / out 130k) | 38m | 57m | 5 | 157 (4) | 1 | 0 |
| ELITEA-1977 | automated | $9.07 | $11.70 | 69,606 (in 203 / out 69k) | 21m | 40m | 3 | 93 (2) | 0 | 0 |
| ELITEA-1980 | automated | $19.73 | $22.36 | 125,191 (in 367 / out 125k) | 39m | 58m | 4 | 179 (6) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $96.32 | 19.67 | 584,085 (in 2k / out 582k) | 97.5% | 190m | 867 (32) |
| qa-engineer | $39.81 | 14 | 316,844 (in 790 / out 316k) | 94.7% | 87m | 373 (5) |
| test-automation-lead | $10.79 | 0 | 57,609 (in 145 / out 57k) | 98.2% | 135m | 72 (2) |

---

# Batch cost — credentials-w02

Generated: 2026-09-14T11:44:34.123Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 31 other-batch dispatch(es) excluded._

## What happened

- Cases: 3  ·  **delivered: 2**  ·  automated 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-23T21:50:42.480Z (3 run record(s))
- Findings reported: 70  ·  fix rounds: 1

## What it cost

- Total: $56.85  ·  3.5h active (cases 93m · lead 101m · stages 18m)  ·  13 dispatches
- Tokens: total 75,172,235  ·  **real work 384,200** (in 1,195 / out 383,005)  ·  cache 72.4M read / 2.4M write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  508 tool calls (30 err, 94% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $10.91 (19%)
  - by stage: lead $7.07 · triage $0.41 (2m) · gate $2.90 (10m) · report $0.53 (6m)
- Rework (fix rounds — already inside per-case direct): $5.51  ·  1 dispatch(es)  ·  12m
- **Per delivered case (incl. overhead): $28.43**
- Avg direct per case (excl. overhead): $15.32
- Direct cost spread: avg $15.32 · median $19.58 · min $6.79 · max $19.58
- Loaded cost spread (direct + even overhead share): avg $18.96 · median $23.22 · min $10.43 · max $23.22
- Active-time spread: avg 31m · median 35m · min 23m · max 35m  ·  loaded: avg 71m · median 75m · min 63m · max 75m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1981 | automated | $19.58 | $23.22 | 119,665 (in 333 / out 119k) | 35m | 75m | 3 | 171 (10) | 0.5 | 33 |
| ELITEA-1982 | automated | $19.58 | $23.22 | 119,665 (in 333 / out 119k) | 35m | 75m | 3 | 171 (10) | 0.5 | 33 |
| ELITEA-1984 | blocked | $6.79 | $10.43 | 61,390 (in 82 / out 61k) | 23m | 63m | 2 | 55 (1) | 0 | 4 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $28.92 | 7 | 198,524 (in 592 / out 198k) | 96.7% | 61m | 271 (19) |
| test-automation-engineer | $20.85 | 6 | 156,228 (in 509 / out 156k) | 96.6% | 50m | 190 (9) |
| test-automation-lead | $7.07 | 0 | 29,448 (in 94 / out 29k) | 98.2% | 101m | 47 (2) |

---

# Batch cost — credentials-w03

Generated: 2026-09-14T11:44:34.131Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 39 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 6  ·  fix rounds: 0

## What it cost

- Total: $14.48  ·  2.1h active (cases 23m · lead 101m · stages 4m)  ·  5 dispatches
- Tokens: total 17,284,373  ·  **real work 108,156** (in 419 / out 107,737)  ·  cache 16.3M read / 874k write  ·  **cache hit rate 94.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  136 tool calls (8 err, 94% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $7.69 (53%)
  - by stage: lead $7.07 · triage $0.41 (2m) · report $0.21 (2m)
- Avg direct per case (excl. overhead): $6.79
- Direct cost spread: avg $6.79 · median $6.79 · min $6.79 · max $6.79
- Loaded cost spread (direct + even overhead share): avg $14.48 · median $14.48 · min $14.48 · max $14.48
- Active-time spread: avg 23m · median 23m · min 23m · max 23m  ·  loaded: avg 128m · median 128m · min 128m · max 128m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1984 | blocked | $6.79 | $14.48 | 61,390 (in 82 / out 61k) | 23m | 128m | 2 | 55 (1) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $7.20 | 4 | 71,638 (in 244 / out 71k) | 91.1% | 25m | 79 (4) |
| test-automation-lead | $7.07 | 0 | 29,448 (in 94 / out 29k) | 98.2% | 101m | 47 (2) |
| test-automation-engineer | $0.21 | 1 | 7,070 (in 81 / out 7k) | 89.6% | 2m | 10 (2) |

---

# Batch cost — elitea-2002

Generated: 2026-09-14T11:44:34.133Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_2 session(s) also served other batches — their session-level figures are split evenly; 1 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 14  ·  fix rounds: 0

## What it cost

- Total: $29.61  ·  1.4h active (cases 45m · lead 41m · stages 0m)  ·  6 dispatches
- Tokens: total 33,874,430  ·  **real work 207,000** (in 431 / out 206,569)  ·  cache 32.5M read / 1.2M write  ·  **cache hit rate 96.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 47 turns  ·  264 tool calls (5 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $6.35 (21%)
- **Per delivered case (incl. overhead): $29.61**
- Avg direct per case (excl. overhead): $23.25
- Direct cost spread: avg $23.25 · median $23.25 · min $23.25 · max $23.25
- Loaded cost spread (direct + even overhead share): avg $29.60 · median $29.60 · min $29.60 · max $29.60
- Active-time spread: avg 45m · median 45m · min 45m · max 45m  ·  loaded: avg 86m · median 86m · min 86m · max 86m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2002 | automated | $23.25 | $29.60 | 165,445 (in 338 / out 165k) | 45m | 86m | 6 | 218 (4) | 0 | 14 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $16.84 | 4 | 123,544 (in 230 / out 123k) | 96.2% | 33m | 148 (1) |
| test-automation-engineer | $6.42 | 2 | 41,901 (in 108 / out 42k) | 96.0% | 12m | 70 (3) |
| test-automation-lead | $6.35 | 0 | 41,555 (in 93 / out 41k) | 97.5% | 41m | 46 (1) |

---

# Batch cost — elitea-2020-create-pipeline-minimal

Generated: 2026-09-14T11:44:34.134Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 21  ·  fix rounds: 1

## What it cost

- Total: $16.38  ·  0.7h active (cases 11m · lead 30m · stages 0m)  ·  2 dispatches
- Tokens: total 20,642,268  ·  **real work 95,800** (in 264 / out 95,536)  ·  cache 20.0M read / 511k write  ·  **cache hit rate 97.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 88 turns  ·  142 tool calls (6 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $10.80 (66%)
- Rework (fix rounds — already inside per-case direct): $3.57  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $16.38**
- Avg direct per case (excl. overhead): $5.58
- Direct cost spread: avg $5.58 · median $5.58 · min $5.58 · max $5.58
- Loaded cost spread (direct + even overhead share): avg $16.38 · median $16.38 · min $16.38 · max $16.38
- Active-time spread: avg 11m · median 11m · min 11m · max 11m  ·  loaded: avg 41m · median 41m · min 41m · max 41m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2020 | automated | $5.58 | $16.38 | 34,462 (in 88 / out 34k) | 11m | 41m | 2 | 55 (2) | 1 | 21 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $10.80 | 0 | 61,338 (in 176 / out 61k) | 98.6% | 30m | 87 (4) |
| test-automation-engineer | $3.57 | 1 | 17,708 (in 62 / out 18k) | 96.1% | 7m | 37 (2) |
| qa-engineer | $2.01 | 1 | 16,754 (in 26 / out 17k) | 91.7% | 4m | 18 (0) |

---

# Batch cost — elitea-2023-pipeline-dashboard-search

Generated: 2026-09-14T11:44:34.135Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 1 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: $13.18  ·  0.5h active (cases 15m · lead 16m · stages 0m)  ·  2 dispatches
- Tokens: total 15,927,882  ·  **real work 82,471** (in 188 / out 82,283)  ·  cache 15.3M read / 498k write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 23 turns  ·  102 tool calls (1 err, 99% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $3.12 (24%)
- **Per delivered case (incl. overhead): $13.18**
- Avg direct per case (excl. overhead): $10.06
- Direct cost spread: avg $10.06 · median $10.06 · min $10.06 · max $10.06
- Loaded cost spread (direct + even overhead share): avg $13.18 · median $13.18 · min $13.18 · max $13.18
- Active-time spread: avg 15m · median 15m · min 15m · max 15m  ·  loaded: avg 31m · median 31m · min 31m · max 31m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2023 | automated | $10.06 | $13.18 | 62,793 (in 142 / out 63k) | 15m | 31m | 2 | 79 (1) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $5.64 | 1 | 37,948 (in 84 / out 38k) | 97.1% | 9m | 50 (0) |
| test-automation-engineer | $4.42 | 1 | 24,845 (in 58 / out 25k) | 96.0% | 6m | 29 (1) |
| test-automation-lead | $3.12 | 0 | 19,678 (in 46 / out 20k) | 97.5% | 16m | 23 (0) |

---

# Batch cost — elitea-2026-pipeline-yaml-editor-view

Generated: 2026-09-14T11:44:34.136Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2026 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2026

---

# Batch cost — elitea-2037

Generated: 2026-09-14T11:44:34.150Z  ·  sessions: 4 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_3 session(s) also served other batches — their session-level figures are split evenly; 89 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 24  ·  fix rounds: 1

## What it cost

- Total: $56.66  ·  6.3h active (cases 110m · lead 262m · stages 3m)  ·  7 dispatches
- Tokens: total 64,613,364  ·  **real work 403,822** (in 801 / out 403,021)  ·  cache 61.9M read / 2.3M write  ·  **cache hit rate 96.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 171 turns  ·  409 tool calls (6 err, 99% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $24.64 (43%)
  - by stage: lead $24.40 · report $0.24 (3m)
- Rework (fix rounds — already inside per-case direct): $1.47  ·  1 dispatch(es)  ·  1m
- **Per delivered case (incl. overhead): $56.66**
- Avg direct per case (excl. overhead): $32.02
- Direct cost spread: avg $32.02 · median $32.02 · min $32.02 · max $32.02
- Loaded cost spread (direct + even overhead share): avg $56.66 · median $56.66 · min $56.66 · max $56.66
- Active-time spread: avg 110m · median 110m · min 110m · max 110m  ·  loaded: avg 375m · median 375m · min 375m · max 375m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2037 | automated | $32.02 | $56.66 | 239,132 (in 402 / out 239k) | 110m | 375m | 6 | 233 (4) | 1 | 24 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $25.21 | 4 | 204,533 (in 288 / out 204k) | 94.4% | 96m | 175 (2) |
| test-automation-lead | $24.40 | 0 | 150,265 (in 342 / out 150k) | 98.2% | 262m | 169 (1) |
| test-automation-engineer | $7.05 | 3 | 49,024 (in 171 / out 49k) | 95.8% | 17m | 65 (3) |

---

# Batch cost — elitea-2040

Generated: 2026-09-14T11:44:34.151Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 5  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2040 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2040

---

# Batch cost — elitea-2042-pipeline-state-panel

Generated: 2026-09-14T11:44:34.152Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2042 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2042

---

# Batch cost — elitea-2068

Generated: 2026-09-14T11:44:34.153Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 5  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2068 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2068

---

# Batch cost — elitea-2094

Generated: 2026-09-14T11:44:34.155Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_2 session(s) also served other batches — their session-level figures are split evenly; 5 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: $14.53  ·  1.3h active (cases 10m · lead 66m · stages 4m)  ·  4 dispatches
- Tokens: total 21,225,617  ·  **real work 111,674** (in 412 / out 111,262)  ·  cache 20.3M read / 771k write  ·  **cache hit rate 96.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 87 turns  ·  146 tool calls (8 err, 95% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $10.83 (75%)
  - by stage: lead $10.29 · triage $0.17 (1m) · report $0.37 (3m)
- Avg direct per case (excl. overhead): $3.70
- Direct cost spread: avg $3.70 · median $3.70 · min $3.70 · max $3.70
- Loaded cost spread (direct + even overhead share): avg $14.53 · median $14.53 · min $14.53 · max $14.53
- Active-time spread: avg 10m · median 10m · min 10m · max 10m  ·  loaded: avg 80m · median 80m · min 80m · max 80m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2094 | blocked | $3.70 | $14.53 | 33,955 (in 52 / out 34k) | 10m | 80m | 1 | 32 (0) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $10.29 | 0 | 61,328 (in 173 / out 61k) | 97.8% | 66m | 86 (2) |
| qa-engineer | $3.87 | 2 | 38,882 (in 101 / out 39k) | 93.8% | 11m | 43 (3) |
| test-automation-engineer | $0.37 | 2 | 11,464 (in 138 / out 11k) | 86.3% | 3m | 17 (3) |

---

# Batch cost — elitea-2227

Generated: 2026-09-14T11:44:34.156Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2227 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2227

---

# Batch cost — elitea-2257-notification-text-content

Generated: 2026-09-14T11:44:34.157Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2257 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2257

---

# Batch cost — elitea-2259-notifications-read-unread

Generated: 2026-09-14T11:44:34.158Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 11  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2259 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2259

---

# Batch cost — elitea-2277-personal-tokens

Generated: 2026-09-14T11:44:34.158Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2277 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2277

---

# Batch cost — elitea-2280-personal-token-create

Generated: 2026-09-14T11:44:34.159Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2280 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2280

---

# Batch cost — elitea-2284

Generated: 2026-09-14T11:44:34.160Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 6  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2284 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2284

---

# Batch cost — elitea-2286-token-name-validation

Generated: 2026-09-14T11:44:34.161Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 7  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2286 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 7 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2286

---

# Batch cost — elitea-2292-users-page-layout

Generated: 2026-09-14T11:44:34.198Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 23  ·  fix rounds: 0

## What it cost

- Total: $18.68  ·  2.1h active (cases 0m · lead 110m · stages 15m)  ·  2 dispatches
- Tokens: total 31,405,835  ·  **real work 88,948** (in 344 / out 88,604)  ·  cache 30.7M read / 604k write  ·  **cache hit rate 98.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  102 tool calls (5 err, 95% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.68 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.70 (5m) · other $4.20 (9m)
- Loaded cost spread (direct + even overhead share): avg $18.68 · median $18.68 · min $18.68 · max $18.68

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2292 | blocked | n/a | $18.68 | 0 (incl. cache) | 0m | 125m | 0 | 0 (0) | 0 | 23 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $3.05 | 1.6 | 45,717 (in 219 / out 45k) | 95.5% | 12m | 40 (4) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2292

---

# Batch cost — elitea-2304-batch-edit-roles

Generated: 2026-09-14T11:44:34.236Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: red (1 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: $18.68  ·  2.1h active (cases 0m · lead 110m · stages 15m)  ·  2 dispatches
- Tokens: total 31,405,835  ·  **real work 88,948** (in 344 / out 88,604)  ·  cache 30.7M read / 604k write  ·  **cache hit rate 98.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  102 tool calls (5 err, 95% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.68 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.70 (5m) · other $4.20 (9m)
- Loaded cost spread (direct + even overhead share): avg $18.68 · median $18.68 · min $18.68 · max $18.68

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2304 | blocked | n/a | $18.68 | 0 (incl. cache) | 0m | 125m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $3.05 | 1.6 | 45,717 (in 219 / out 45k) | 95.5% | 12m | 40 (4) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2304

---

# Batch cost — elitea-2307

Generated: 2026-09-14T11:44:34.237Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 11  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2307 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2307

---

# Batch cost — elitea-2310

Generated: 2026-09-14T11:44:34.272Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 15  ·  fix rounds: 0

## What it cost

- Total: $18.36  ·  2.0h active (cases 0m · lead 110m · stages 11m)  ·  2 dispatches
- Tokens: total 28,930,473  ·  **real work 65,340** (in 208 / out 65,132)  ·  cache 28.2M read / 636k write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  85 tool calls (3 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.37 (1m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $18.36**
- Loaded cost spread (direct + even overhead share): avg $18.36 · median $18.36 · min $18.36 · max $18.36

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2310 | automated | n/a | $18.36 | 0 (incl. cache) | 0m | 121m | 0 | 0 (0) | 0 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $2.73 | 1.6 | 22,109 (in 83 / out 22k) | 91.7% | 8m | 23 (2) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2310

---

# Batch cost — elitea-2312

Generated: 2026-09-14T11:44:34.307Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green ([object Object],[object Object],[object Object] runs)
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: $18.36  ·  2.0h active (cases 0m · lead 110m · stages 11m)  ·  2 dispatches
- Tokens: total 28,930,473  ·  **real work 65,340** (in 208 / out 65,132)  ·  cache 28.2M read / 636k write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  85 tool calls (3 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.37 (1m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $18.36**
- Loaded cost spread (direct + even overhead share): avg $18.36 · median $18.36 · min $18.36 · max $18.36

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2312 | automated | n/a | $18.36 | 0 (incl. cache) | 0m | 121m | 0 | 0 (0) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $2.73 | 1.6 | 22,109 (in 83 / out 22k) | 91.7% | 8m | 23 (2) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2312

---

# Batch cost — elitea-2313

Generated: 2026-09-14T11:44:34.308Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2313 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2313

---

# Batch cost — elitea-2320

Generated: 2026-09-14T11:44:34.342Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 15  ·  fix rounds: 0

## What it cost

- Total: $18.36  ·  2.0h active (cases 0m · lead 110m · stages 11m)  ·  2 dispatches
- Tokens: total 28,930,473  ·  **real work 65,340** (in 208 / out 65,132)  ·  cache 28.2M read / 636k write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  85 tool calls (3 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.37 (1m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $18.36**
- Loaded cost spread (direct + even overhead share): avg $18.36 · median $18.36 · min $18.36 · max $18.36

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2320 | automated | n/a | $18.36 | 0 (incl. cache) | 0m | 121m | 0 | 0 (0) | 0 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $2.73 | 1.6 | 22,109 (in 83 / out 22k) | 91.7% | 8m | 23 (2) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2320

---

# Batch cost — elitea-2321

Generated: 2026-09-14T11:44:34.376Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 6  ·  fix rounds: 0

## What it cost

- Total: $18.36  ·  2.0h active (cases 0m · lead 110m · stages 11m)  ·  2 dispatches
- Tokens: total 28,930,473  ·  **real work 65,340** (in 208 / out 65,132)  ·  cache 28.2M read / 636k write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  85 tool calls (3 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.37 (1m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $18.36**
- Loaded cost spread (direct + even overhead share): avg $18.36 · median $18.36 · min $18.36 · max $18.36

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2321 | automated | n/a | $18.36 | 0 (incl. cache) | 0m | 121m | 0 | 0 (0) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $2.73 | 1.6 | 22,109 (in 83 / out 22k) | 91.7% | 8m | 23 (2) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2321

---

# Batch cost — elitea-2336-secrets-inline-create

Generated: 2026-09-14T11:44:34.377Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: green (3 runs)
- Findings reported: 33  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2336 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 33 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2336

---

# Batch cost — elitea-2337-secret-name-validation

Generated: 2026-09-14T11:44:34.378Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: red (1 runs)
- Findings reported: 17  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2337 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2337

---

# Batch cost — elitea-2338-delete-secret

Generated: 2026-09-14T11:44:34.379Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: sanctioned-red-pass (3 runs)
- Findings reported: 17  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2338 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2338

---

# Batch cost — elitea-2343-secret-eye-icon-reveal

Generated: 2026-09-14T11:44:34.414Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 194 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  merged-ungated 1
- Gate: not-run
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: $18.36  ·  2.0h active (cases 0m · lead 110m · stages 13m)  ·  2 dispatches
- Tokens: total 28,896,645  ·  **real work 75,031** (in 216 / out 74,815)  ·  cache 28.2M read / 601k write  ·  **cache hit rate 97.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  86 tool calls (3 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (100%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.38 (3m) · other $4.20 (9m)
- Loaded cost spread (direct + even overhead share): avg $18.36 · median $18.36 · min $18.36 · max $18.36

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2343 | merged-ungated | n/a | $18.36 | 0 (incl. cache) | 0m | 123m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $2.73 | 1.6 | 31,800 (in 91 / out 32k) | 92.5% | 10m | 24 (2) |
| qa-engineer | $2.08 | 0.4 | 14,386 (in 36 / out 14k) | 97.1% | 4m | 18 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2343

---

# Batch cost — elitea-2344-hide-secret

Generated: 2026-09-14T11:44:34.415Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  merged-ungated 1
- Gate: not-run (1 runs)
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2344 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2344

---

# Batch cost — elitea-2350-agent-hub-private-project

Generated: 2026-09-14T11:44:34.416Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2350 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2350

---

# Batch cost — elitea-2352-agent-hub-filter-single-category

Generated: 2026-09-14T11:44:34.417Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2352 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2352

---

# Batch cost — ELITEA-2354-agent-hub-like

Generated: 2026-09-14T11:44:34.418Z  ·  sessions: 3 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: red (1 runs)
- Findings reported: 16  ·  fix rounds: 2

## What it cost

- Total: $63.91  ·  4.0h active (cases 86m · lead 137m · stages 16m)  ·  8 dispatches
- Tokens: total 74,031,107  ·  **real work 428,375** (in 848 / out 427,527)  ·  cache 71.1M read / 2.5M write  ·  **cache hit rate 96.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 140 turns  ·  443 tool calls (11 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $27.97 (44%)
  - by stage: lead $20.00 · triage $5.00 (11m) · other $2.97 (5m)
- Rework (fix rounds — already inside per-case direct): $13.23  ·  2 dispatch(es)  ·  43m
- Avg direct per case (excl. overhead): $35.93
- Direct cost spread: avg $35.93 · median $35.93 · min $35.93 · max $35.93
- Loaded cost spread (direct + even overhead share): avg $63.90 · median $63.90 · min $63.90 · max $63.90
- Active-time spread: avg 86m · median 86m · min 86m · max 86m  ·  loaded: avg 239m · median 239m · min 239m · max 239m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2354 | blocked | $35.93 | $63.90 | 228,723 (in 458 / out 228k) | 86m | 239m | 6 | 242 (3) | 2 | 16 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $22.84 | 5 | 169,667 (in 308 / out 169k) | 96.3% | 43m | 173 (3) |
| test-automation-engineer | $21.07 | 3 | 118,640 (in 260 / out 118k) | 96.3% | 59m | 133 (1) |
| test-automation-lead | $20.00 | 0 | 140,068 (in 280 / out 140k) | 97.4% | 137m | 137 (7) |

---

# Batch cost — elitea-2356-agent-hub-detail-modal

Generated: 2026-09-14T11:44:34.419Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 22  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2356 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 22 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2356

---

# Batch cost — elitea-2365-my-liked-reload

Generated: 2026-09-14T11:44:34.420Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: green (1 runs)
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2365 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2365

---

# Batch cost — elitea-2374-context-mgmt-toggle

Generated: 2026-09-14T11:44:34.420Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 12  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2374 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2374

---

# Batch cost — elitea-2377-summarization-toggle

Generated: 2026-09-14T11:44:34.421Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2377 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2377

---

# Batch cost — elitea-2391-max-context-tokens

Generated: 2026-09-14T11:44:34.422Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2391 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2391

---

# Batch cost — elitea-2392-ai-configuration-page

Generated: 2026-09-14T11:44:34.456Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_2 session(s) also served other batches — their session-level figures are split evenly; 193 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 8  ·  fix rounds: 0

## What it cost

- Total: $37.72  ·  3.2h active (cases 16m · lead 145m · stages 34m)  ·  5.67 dispatches
- Tokens: total 53,079,775  ·  **real work 219,845** (in 516 / out 219,329)  ·  cache 51.7M read / 1.2M write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 70 turns  ·  247 tool calls (5 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $31.54 (84%)
  - by stage: lead $17.27 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.38 (3m) · other $13.66 (29m)
- **Per delivered case (incl. overhead): $37.72**
- Avg direct per case (excl. overhead): $6.18
- Direct cost spread: avg $6.18 · median $6.18 · min $6.18 · max $6.18
- Loaded cost spread (direct + even overhead share): avg $37.72 · median $37.72 · min $37.72 · max $37.72
- Active-time spread: avg 16m · median 16m · min 16m · max 16m  ·  loaded: avg 194m · median 194m · min 194m · max 194m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2392 | automated | $6.18 | $37.72 | 46,823 (in 104 / out 47k) | 16m | 194m | 1 | 60 (1) | 0 | 8 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $17.27 | 0 | 57,005 (in 139 / out 57k) | 98.8% | 145m | 69 (1) |
| qa-engineer | $12.72 | 2.4 | 98,910 (in 204 / out 99k) | 97.0% | 30m | 114 (2) |
| test-automation-engineer | $7.73 | 3.27 | 63,929 (in 172 / out 64k) | 96.0% | 19m | 65 (2) |

---

# Batch cost — elitea-2397-set-llm-model-tiers

Generated: 2026-09-14T11:44:34.457Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2397 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2397

---

# Batch cost — elitea-2435-skill-pin-unpin

Generated: 2026-09-14T11:44:34.458Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2435 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2435

---

# Batch cost — elitea-2437-version-dropdown-set-default

Generated: 2026-09-14T11:44:34.459Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2437 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2437

---

# Batch cost — elitea-2438-skill-import-frontmatter

Generated: 2026-09-14T11:44:34.459Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 16  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2438 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 16 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2438

---

# Batch cost — elitea-2440-test-panel-version-instructions

Generated: 2026-09-14T11:44:34.460Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 13  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2440 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2440

---

# Batch cost — elitea-2450

Generated: 2026-09-14T11:44:34.461Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 19  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2450 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 19 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2450

---

# Batch cost — elitea-2452

Generated: 2026-09-14T11:44:34.461Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 17  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2452 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2452

---

# Batch cost — elitea-2453

Generated: 2026-09-14T11:44:34.462Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 16  ·  fix rounds: 0

## What it cost

- Total: $40.72  ·  2.8h active (cases 49m · lead 75m · stages 46m)  ·  3 dispatches
- Tokens: total 44,315,325  ·  **real work 213,877** (in 422 / out 213,455)  ·  cache 41.9M read / 2.2M write  ·  **cache hit rate 95.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 66 turns  ·  229 tool calls (11 err, 95% ok)  ·  skills: sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $25.73 (63%)
  - by stage: lead $9.87 · triage $15.86 (46m)
- **Per delivered case (incl. overhead): $40.72**
- Avg direct per case (excl. overhead): $14.99
- Direct cost spread: avg $14.99 · median $14.99 · min $14.99 · max $14.99
- Loaded cost spread (direct + even overhead share): avg $40.72 · median $40.72 · min $40.72 · max $40.72
- Active-time spread: avg 49m · median 49m · min 49m · max 49m  ·  loaded: avg 170m · median 170m · min 170m · max 170m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2453 | automated | $14.99 | $40.72 | 74,219 (in 140 / out 74k) | 49m | 170m | 2 | 82 (4) | 0 | 16 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $18.17 | 2 | 103,861 (in 172 / out 104k) | 94.9% | 51m | 100 (4) |
| test-automation-engineer | $12.68 | 1 | 51,279 (in 118 / out 51k) | 92.4% | 44m | 64 (3) |
| test-automation-lead | $9.87 | 0 | 58,737 (in 132 / out 59k) | 98.0% | 75m | 65 (4) |

---

# Batch cost — elitea-2455-chat-participants

Generated: 2026-09-14T11:44:34.465Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_2 session(s) also served other batches — their session-level figures are split evenly; 2 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Findings reported: 6  ·  fix rounds: 0

## What it cost

- Total: $41.49  ·  2.5h active (cases 81m · lead 66m · stages 6m)  ·  7 dispatches
- Tokens: total 128,808,814  ·  **real work 291,611** (in 1,163 / out 290,448)  ·  cache 127.0M read / 1.5M write  ·  **cache hit rate 98.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 87 turns  ·  491 tool calls (15 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $11.03 (27%)
  - by stage: lead $10.29 · triage $0.13 (1m) · report $0.61 (5m)
- Avg direct per case (excl. overhead): $30.47
- Direct cost spread: avg $30.47 · median $30.47 · min $30.47 · max $30.47
- Loaded cost spread (direct + even overhead share): avg $41.50 · median $41.50 · min $41.50 · max $41.50
- Active-time spread: avg 81m · median 81m · min 81m · max 81m  ·  loaded: avg 153m · median 153m · min 153m · max 153m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2455 | blocked | $30.47 | $41.50 | 207,541 (in 730 / out 207k) | 81m | 153m | 3 | 372 (9) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $26.79 | 5 | 190,326 (in 899 / out 189k) | 99.1% | 67m | 360 (12) |
| test-automation-lead | $10.29 | 0 | 61,328 (in 173 / out 61k) | 97.8% | 66m | 86 (2) |
| qa-engineer | $4.41 | 2 | 39,957 (in 91 / out 40k) | 94.9% | 20m | 45 (1) |

---

# Batch cost — elitea-2459-chat-folder-rename-tooltip

Generated: 2026-09-14T11:44:34.465Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 6  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2459 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2459

---

# Batch cost — elitea-2464-chat-modules-panel

Generated: 2026-09-14T11:44:34.466Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: GREEN (scoped) (3 runs)
- Findings reported: 1  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2464 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2464

---

# Batch cost — help-center-remaining

Generated: 2026-09-14T11:44:34.468Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 10  ·  **delivered: 10**  ·  automated 9  ·  merged-sanctioned-red 1
- Gate: green (3 runs)
- Findings reported: 143  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2220 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2221 | merged-sanctioned-red | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2222 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2223 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2224 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2225 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2226 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2228 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2229 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2230 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2220, ELITEA-2221, ELITEA-2222, ELITEA-2223, ELITEA-2224, ELITEA-2225, ELITEA-2226, ELITEA-2228, ELITEA-2229, ELITEA-2230

---

# Batch cost — mcp-w01

Generated: 2026-09-14T11:44:34.481Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 66 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 8**  ·  automated 7  ·  merged-sanctioned-red 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T00:35:30.927Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 3

## What it cost

- Total: $76.87  ·  4.3h active (cases 130m · lead 90m · stages 36m)  ·  21 dispatches
- Tokens: total 100,549,890  ·  **real work 479,446** (in 1,567 / out 477,879)  ·  cache 96.7M read / 3.3M write  ·  **cache hit rate 96.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  703 tool calls (22 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $8.32 (11%)
  - by stage: lead $4.19 · triage $0.20 (1m) · gate $3.60 (28m) · report $0.33 (7m)
- Rework (fix rounds — already inside per-case direct): $8.34  ·  3 dispatch(es)  ·  17m
- **Per delivered case (incl. overhead): $9.61**
- Avg direct per case (excl. overhead): $8.57
- Direct cost spread: avg $8.57 · median $8.37 · min $5.94 · max $11.61
- Loaded cost spread (direct + even overhead share): avg $9.61 · median $9.41 · min $6.98 · max $12.65
- Active-time spread: avg 16m · median 14m · min 11m · max 26m  ·  loaded: avg 32m · median 30m · min 27m · max 42m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1923 | automated | $11.61 | $12.65 | 72,905 (in 203 / out 73k) | 26m | 42m | 2.5 | 104 (2) | 0.5 | 0 |
| ELITEA-1924 | merged-sanctioned-red | $11.61 | $12.65 | 72,905 (in 203 / out 73k) | 26m | 42m | 2.5 | 104 (2) | 0.5 | 0 |
| ELITEA-1925 | automated | $5.94 | $6.98 | 42,012 (in 126 / out 42k) | 13m | 29m | 2.5 | 54 (2) | 0.5 | 0 |
| ELITEA-1926 | automated | $5.94 | $6.98 | 42,012 (in 126 / out 42k) | 13m | 29m | 2.5 | 54 (2) | 0.5 | 0 |
| ELITEA-1928 | automated | $6.81 | $7.85 | 41,069 (in 145 / out 41k) | 11m | 27m | 1.5 | 68 (3) | 0 | 0 |
| ELITEA-1930 | automated | $6.81 | $7.85 | 41,069 (in 145 / out 41k) | 11m | 27m | 1.5 | 68 (3) | 0 | 0 |
| ELITEA-1931 | automated | $9.92 | $10.96 | 61,417 (in 189 / out 61k) | 15m | 31m | 2.5 | 92 (3) | 0.5 | 0 |
| ELITEA-1932 | automated | $9.92 | $10.96 | 61,417 (in 189 / out 61k) | 15m | 31m | 2.5 | 92 (3) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $53.09 | 13 | 323,113 (in 1k / out 322k) | 97.1% | 131m | 495 (20) |
| qa-engineer | $19.60 | 8 | 141,396 (in 387 / out 141k) | 94.5% | 34m | 179 (1) |
| test-automation-lead | $4.19 | 0 | 14,937 (in 59 / out 15k) | 98.9% | 90m | 29 (1) |

---

# Batch cost — mcp-w02

Generated: 2026-09-14T11:44:34.494Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_2 session(s) also served other batches — their session-level figures are split evenly; 66 other-batch dispatch(es) excluded._

## What happened

- Cases: 8  ·  **delivered: 6**  ·  automated 6  ·  blocked 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T04:08:19.017Z (3 run record(s))
- Findings reported: 89  ·  fix rounds: 2

## What it cost

- Total: $92.66  ·  4.9h active (cases 153m · lead 117m · stages 23m)  ·  24 dispatches
- Tokens: total 115,286,671  ·  **real work 662,521** (in 1,786 / out 660,735)  ·  cache 110.6M read / 4.0M write  ·  **cache hit rate 96.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 72 turns  ·  865 tool calls (21 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $13.38 (14%)
  - by stage: lead $10.14 · triage $0.27 (4m) · gate $2.61 (14m) · report $0.35 (5m)
- Rework (fix rounds — already inside per-case direct): $8.75  ·  2 dispatch(es)  ·  18m
- **Per delivered case (incl. overhead): $15.44**
- Avg direct per case (excl. overhead): $9.91
- Direct cost spread: avg $9.91 · median $10.08 · min $2.72 · max $19.49
- Loaded cost spread (direct + even overhead share): avg $11.58 · median $11.75 · min $4.39 · max $21.16
- Active-time spread: avg 19m · median 19m · min 5m · max 41m  ·  loaded: avg 36m · median 36m · min 22m · max 58m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1935 | automated | $11.42 | $13.09 | 83,725 (in 205 / out 84k) | 22m | 39m | 3 | 103 (3) | 0.5 | 35 |
| ELITEA-1936 | automated | $11.42 | $13.09 | 83,725 (in 205 / out 84k) | 22m | 39m | 3 | 103 (3) | 0.5 | 35 |
| ELITEA-1938 | blocked | $2.72 | $4.39 | 17,407 (in 45 / out 17k) | 5m | 22m | 0.33 | 26 (0) | 0 | 6 |
| ELITEA-1939 | blocked | $2.72 | $4.39 | 17,407 (in 45 / out 17k) | 5m | 22m | 0.33 | 26 (0) | 0 | 6 |
| ELITEA-1940 | automated | $19.49 | $21.16 | 147,042 (in 332 / out 147k) | 41m | 58m | 5.33 | 175 (2) | 1 | 7 |
| ELITEA-1946 | automated | $8.74 | $10.41 | 56,711 (in 162 / out 57k) | 16m | 33m | 2 | 87 (3) | 0 | 0 |
| ELITEA-1959 | automated | $8.74 | $10.41 | 56,711 (in 162 / out 57k) | 16m | 33m | 2 | 87 (3) | 0 | 0 |
| ELITEA-1961 | automated | $14.02 | $15.69 | 103,508 (in 255 / out 103k) | 26m | 43m | 5 | 140 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $46.44 | 12 | 335,236 (in 839 / out 334k) | 96.3% | 86m | 459 (6) |
| test-automation-engineer | $36.08 | 12 | 280,275 (in 803 / out 279k) | 96.1% | 89m | 335 (12) |
| test-automation-lead | $10.14 | 0 | 47,010 (in 144 / out 47k) | 98.7% | 117m | 71 (3) |

---

# Batch cost — mcp-w03

Generated: 2026-09-14T11:44:34.507Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 67 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 4**  ·  automated 4  ·  blocked 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T06:30:39.594Z (3 run record(s))
- Findings reported: 106  ·  fix rounds: 1

## What it cost

- Total: $56.78  ·  3.5h active (cases 105m · lead 90m · stages 14m)  ·  20 dispatches
- Tokens: total 69,499,652  ·  **real work 399,194** (in 1,154 / out 398,040)  ·  cache 66.3M read / 2.8M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  546 tool calls (11 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $6.35 (11%)
  - by stage: lead $4.19 · triage $0.20 (1m) · gate $1.66 (7m) · report $0.30 (6m)
- Rework (fix rounds — already inside per-case direct): $1.95  ·  1 dispatch(es)  ·  3m
- **Per delivered case (incl. overhead): $14.19**
- Avg direct per case (excl. overhead): $8.40
- Direct cost spread: avg $8.40 · median $9.68 · min $2.23 · max $13.37
- Loaded cost spread (direct + even overhead share): avg $9.47 · median $10.74 · min $3.29 · max $14.43
- Active-time spread: avg 18m · median 21m · min 6m · max 25m  ·  loaded: avg 35m · median 38m · min 23m · max 42m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1942 | automated | $13.37 | $14.43 | 87,167 (in 237 / out 87k) | 24m | 41m | 6.5 | 117 (3) | 1 | 28 |
| ELITEA-1943 | blocked | $3.22 | $4.28 | 18,696 (in 58 / out 19k) | 6m | 23m | 0.5 | 34 (1) | 0 | 6 |
| ELITEA-1945 | automated | $7.11 | $8.17 | 61,100 (in 165 / out 61k) | 18m | 35m | 4 | 76 (0) | 0 | 18 |
| ELITEA-1948 | automated | $12.25 | $13.31 | 79,621 (in 233 / out 79k) | 25m | 42m | 2.5 | 120 (2) | 0 | 24 |
| ELITEA-1949 | automated | $12.25 | $13.31 | 79,621 (in 233 / out 79k) | 25m | 42m | 2.5 | 120 (2) | 0 | 24 |
| ELITEA-1958 | blocked | $2.23 | $3.29 | 17,365 (in 38 / out 17k) | 7m | 24m | 1 | 25 (0) | 0 | 6 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $33.19 | 10 | 229,653 (in 605 / out 229k) | 96.5% | 72m | 330 (5) |
| test-automation-engineer | $19.39 | 10 | 154,604 (in 490 / out 154k) | 94.3% | 46m | 187 (5) |
| test-automation-lead | $4.19 | 0 | 14,937 (in 59 / out 15k) | 98.9% | 90m | 29 (1) |

---

# Batch cost — mcp-w04

Generated: 2026-09-14T11:44:34.520Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 66 other-batch dispatch(es) excluded._

## What happened

- Cases: 5  ·  **delivered: 3**  ·  automated 3  ·  not-started 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T07:51:01.812Z (3 run record(s))
- Findings reported: 76  ·  fix rounds: 1

## What it cost

- Total: $55.49  ·  3.5h active (cases 104m · lead 90m · stages 16m)  ·  21 dispatches
- Tokens: total 67,222,893  ·  **real work 412,656** (in 1,202 / out 411,454)  ·  cache 63.9M read / 2.9M write  ·  **cache hit rate 95.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  516 tool calls (17 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $6.78 (12%)
  - by stage: lead $4.19 · triage $0.39 (2m) · gate $1.69 (7m) · report $0.52 (7m)
- Rework (fix rounds — already inside per-case direct): $3.00  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $18.50**
- Avg direct per case (excl. overhead): $9.74
- Direct cost spread: avg $9.74 · median $10.95 · min $5.07 · max $15.27
- Loaded cost spread (direct + even overhead share): avg $11.10 · median $12.31 · min $6.43 · max $16.63
- Active-time spread: avg 21m · median 25m · min 11m · max 30m  ·  loaded: avg 42m · median 46m · min 32m · max 51m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1952 | not-started | $12.36 | $13.72 | 88,239 (in 199 / out 88k) | 27m | 48m | 3.5 | 98 (3) | 0 | 0 |
| ELITEA-1953 | not-started | $10.95 | $12.31 | 78,261 (in 183 / out 78k) | 25m | 46m | 2.5 | 90 (2) | 0 | 0 |
| ELITEA-1956 | automated | $5.07 | $6.43 | 35,865 (in 108 / out 36k) | 11m | 32m | 2 | 50 (0) | 0 | 21 |
| ELITEA-1957 | automated | $5.07 | $6.43 | 35,865 (in 108 / out 36k) | 11m | 32m | 2 | 50 (0) | 0 | 21 |
| ELITEA-1960 | automated | $15.27 | $16.63 | 110,293 (in 283 / out 110k) | 30m | 51m | 6 | 149 (5) | 1 | 34 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $29.54 | 11 | 217,726 (in 552 / out 217k) | 95.0% | 61m | 283 (11) |
| test-automation-engineer | $21.76 | 10 | 179,993 (in 591 / out 179k) | 95.5% | 59m | 204 (5) |
| test-automation-lead | $4.19 | 0 | 14,937 (in 59 / out 15k) | 98.9% | 90m | 29 (1) |

---

# Batch cost — mcp-w05

Generated: 2026-09-14T11:44:34.534Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 76 other-batch dispatch(es) excluded._

## What happened

- Cases: 2  ·  **delivered: 2**  ·  automated 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T08:59:31.657Z (3 run record(s))
- Findings reported: 44  ·  fix rounds: 0

## What it cost

- Total: $30.04  ·  2.6h active (cases 52m · lead 90m · stages 17m)  ·  11 dispatches
- Tokens: total 38,812,901  ·  **real work 229,964** (in 704 / out 229,260)  ·  cache 37.0M read / 1.6M write  ·  **cache hit rate 96.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  269 tool calls (12 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $6.73 (22%)
  - by stage: lead $4.19 · triage $0.39 (2m) · gate $1.64 (8m) · report $0.52 (7m)
- **Per delivered case (incl. overhead): $15.02**
- Avg direct per case (excl. overhead): $11.66
- Direct cost spread: avg $11.66 · median $11.66 · min $10.95 · max $12.36
- Loaded cost spread (direct + even overhead share): avg $15.02 · median $15.02 · min $14.31 · max $15.72
- Active-time spread: avg 26m · median 26m · min 25m · max 27m  ·  loaded: avg 79m · median 79m · min 78m · max 80m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1952 | automated | $12.36 | $15.72 | 88,239 (in 199 / out 88k) | 27m | 80m | 3.5 | 98 (3) | 0 | 22 |
| ELITEA-1953 | automated | $10.95 | $14.31 | 78,261 (in 183 / out 78k) | 25m | 78m | 2.5 | 90 (2) | 0 | 22 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $14.54 | 6 | 110,189 (in 330 / out 110k) | 95.0% | 32m | 139 (6) |
| test-automation-engineer | $11.31 | 5 | 104,838 (in 315 / out 105k) | 95.8% | 37m | 101 (5) |
| test-automation-lead | $4.19 | 0 | 14,937 (in 59 / out 15k) | 98.9% | 90m | 29 (1) |

---

# Batch cost — onboarding-w2

Generated: 2026-09-14T11:44:34.540Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 16 other-batch dispatch(es) excluded._

## What happened

- Cases: 4  ·  **delivered: 4**  ·  automated 4
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T11:25:21.991Z (4 run record(s))
- Findings reported: 90  ·  fix rounds: 1

## What it cost

- Total: $49.90  ·  3.0h active (cases 66m · lead 86m · stages 31m)  ·  17.33 dispatches
- Tokens: total 58,163,715  ·  **real work 378,727** (in 978 / out 377,749)  ·  cache 55.2M read / 2.6M write  ·  **cache hit rate 95.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 54 turns  ·  436 tool calls (14 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $15.28 (31%)
  - by stage: lead $8.21 · triage $0.16 (1m) · gate $2.95 (16m) · report $0.50 (6m) · other $3.46 (8m)
- Rework (fix rounds — already inside per-case direct): $1.70  ·  1 dispatch(es)  ·  3m
- **Per delivered case (incl. overhead): $12.48**
- Avg direct per case (excl. overhead): $8.66
- Direct cost spread: avg $8.66 · median $8.41 · min $3.24 · max $14.55
- Loaded cost spread (direct + even overhead share): avg $12.48 · median $12.24 · min $7.06 · max $18.37
- Active-time spread: avg 17m · median 14m · min 6m · max 32m  ·  loaded: avg 46m · median 43m · min 35m · max 61m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2235 | automated | $6.77 | $10.59 | 48,640 (in 129 / out 49k) | 12m | 41m | 1.5 | 63 (2) | 0 | 20 |
| ELITEA-2236 | automated | $10.06 | $13.88 | 65,628 (in 191 / out 65k) | 16m | 45m | 2.5 | 93 (2) | 0 | 20 |
| ELITEA-2241 | automated | $3.24 | $7.06 | 23,500 (in 65 / out 23k) | 6m | 35m | 1 | 29 (1) | 0 | 20 |
| ELITEA-2232 | automated | $14.55 | $18.37 | 125,239 (in 249 / out 125k) | 32m | 61m | 7 | 126 (3) | 1 | 30 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $22.84 | 8 | 179,695 (in 403 / out 179k) | 95.1% | 46m | 204 (4) |
| test-automation-engineer | $18.85 | 9.33 | 156,689 (in 466 / out 156k) | 93.9% | 51m | 178 (8) |
| test-automation-lead | $8.21 | 0 | 42,343 (in 109 / out 42k) | 99.1% | 86m | 54 (2) |

---

# Batch cost — onboarding-w3

Generated: 2026-09-14T11:44:34.546Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 26 other-batch dispatch(es) excluded._

## What happened

- Cases: 3  ·  **delivered: 3**  ·  automated 3
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-24T12:21:59.731Z (3 run record(s))
- Findings reported: 39  ·  fix rounds: 0

## What it cost

- Total: $24.19  ·  2.0h active (cases 19m · lead 86m · stages 14m)  ·  7.33 dispatches
- Tokens: total 31,602,908  ·  **real work 165,370** (in 494 / out 164,876)  ·  cache 30.4M read / 1.0M write  ·  **cache hit rate 96.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 54 turns  ·  217 tool calls (7 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $13.52 (56%)
  - by stage: lead $8.21 · triage $0.17 (1m) · gate $1.48 (3m) · report $0.20 (2m) · other $3.46 (8m)
- **Per delivered case (incl. overhead): $8.06**
- Avg direct per case (excl. overhead): $3.56
- Direct cost spread: avg $3.56 · median $4.93 · min $0.81 · max $4.93
- Loaded cost spread (direct + even overhead share): avg $8.07 · median $9.44 · min $5.32 · max $9.44
- Active-time spread: avg 6m · median 9m · min 1m · max 9m  ·  loaded: avg 39m · median 42m · min 34m · max 42m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2237 | automated | $4.93 | $9.44 | 35,378 (in 93 / out 35k) | 9m | 42m | 1.17 | 44 (1) | 0 | 13 |
| ELITEA-2238 | automated | $4.93 | $9.44 | 35,378 (in 93 / out 35k) | 9m | 42m | 1.17 | 44 (1) | 0 | 13 |
| ELITEA-2239 | automated | $0.81 | $5.32 | 5,648 (in 27 / out 6k) | 1m | 34m | 0.67 | 9 (0) | 0 | 13 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $13.52 | 5.33 | 102,025 (in 296 / out 102k) | 95.8% | 28m | 128 (4) |
| test-automation-lead | $8.21 | 0 | 42,343 (in 109 / out 42k) | 99.1% | 86m | 54 (2) |
| qa-engineer | $2.47 | 2 | 21,002 (in 89 / out 21k) | 91.4% | 5m | 35 (1) |

---

# Batch cost — onboarding-w4

Generated: 2026-09-14T11:44:34.552Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 20 other-batch dispatch(es) excluded._

## What happened

- Cases: 3  ·  **delivered: 0**  ·  blocked 3
- Gate: red (3 runs)
- Gate record (script-authored): green at 2026-08-24T14:13:25.700Z (5 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `red` but the recorded verdict is `green` — write the verdict back into report.json
- Findings reported: 47  ·  fix rounds: 0

## What it cost

- Total: $48.84  ·  2.9h active (cases 69m · lead 86m · stages 19m)  ·  13.33 dispatches
- Tokens: total 59,619,303  ·  **real work 367,199** (in 900 / out 366,299)  ·  cache 57.1M read / 2.1M write  ·  **cache hit rate 96.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 54 turns  ·  433 tool calls (15 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $14.43 (30%)
  - by stage: lead $8.21 · triage $0.15 (1m) · gate $2.28 (5m) · report $0.34 (5m) · other $3.46 (8m)
- Avg direct per case (excl. overhead): $11.47
- Direct cost spread: avg $11.47 · median $13.16 · min $7.49 · max $13.76
- Loaded cost spread (direct + even overhead share): avg $16.28 · median $17.97 · min $12.30 · max $18.57
- Active-time spread: avg 23m · median 24m · min 13m · max 32m  ·  loaded: avg 58m · median 59m · min 48m · max 67m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2234 | blocked | $13.16 | $17.97 | 93,768 (in 239 / out 94k) | 24m | 59m | 3 | 120 (3) | 0 | 18 |
| ELITEA-2233 | blocked | $7.49 | $12.30 | 53,736 (in 147 / out 54k) | 13m | 48m | 2 | 68 (2) | 0 | 18 |
| ELITEA-2240 | blocked | $13.76 | $18.57 | 118,695 (in 176 / out 119k) | 32m | 67m | 4 | 115 (4) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $24.10 | 7.33 | 194,932 (in 512 / out 194k) | 96.2% | 53m | 216 (9) |
| qa-engineer | $16.53 | 6 | 129,924 (in 279 / out 130k) | 95.0% | 35m | 163 (4) |
| test-automation-lead | $8.21 | 0 | 42,343 (in 109 / out 42k) | 99.1% | 86m | 54 (2) |

---

# Batch cost — pipeline-decision-node-2034

Generated: 2026-09-14T11:44:34.553Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 18  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2034 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 18 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2034

---

# Batch cost — pipeline-router-node-2033

Generated: 2026-09-14T11:44:34.566Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 85 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 0**  ·  blocked 1
- Gate: red (3 runs)
- Findings reported: 9  ·  fix rounds: 1

## What it cost

- Total: $12.74  ·  2.0h active (cases 28m · lead 90m · stages 0m)  ·  2 dispatches
- Tokens: total 15,930,423  ·  **real work 56,559** (in 189 / out 56,370)  ·  cache 15.3M read / 547k write  ·  **cache hit rate 96.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 30 turns  ·  100 tool calls (10 err, 90% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $4.19 (33%)
- Rework (fix rounds — already inside per-case direct): $7.15  ·  1 dispatch(es)  ·  26m
- Avg direct per case (excl. overhead): $8.55
- Direct cost spread: avg $8.55 · median $8.55 · min $8.55 · max $8.55
- Loaded cost spread (direct + even overhead share): avg $12.74 · median $12.74 · min $12.74 · max $12.74
- Active-time spread: avg 28m · median 28m · min 28m · max 28m  ·  loaded: avg 118m · median 118m · min 118m · max 118m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2033 | blocked | $8.55 | $12.74 | 41,622 (in 130 / out 41k) | 28m | 118m | 2 | 71 (9) | 1 | 9 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $7.15 | 1 | 31,644 (in 114 / out 32k) | 95.8% | 26m | 63 (8) |
| test-automation-lead | $4.19 | 0 | 14,937 (in 59 / out 15k) | 98.9% | 90m | 29 (1) |
| qa-engineer | $1.40 | 1 | 9,978 (in 16 / out 10k) | 86.8% | 2m | 8 (1) |

---

# Batch cost — pipelines-remaining-w1

Generated: 2026-09-14T11:44:34.568Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 8  ·  **delivered: 0**  ·  merged-ungated 8
- Gate: not-run (1 runs)
- Findings reported: 93  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2009 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2035 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2036 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 4 |
| ELITEA-2038 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 16 |
| ELITEA-2039 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2045 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2046 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2047 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 21 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2009, ELITEA-2035, ELITEA-2036, ELITEA-2038, ELITEA-2039, ELITEA-2045, ELITEA-2046, ELITEA-2047

---

# Batch cost — pipelines-remaining-w2

Generated: 2026-09-14T11:44:34.573Z  ·  sessions: 9 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_6 session(s) also served other batches — their session-level figures are split evenly; 5 other-batch dispatch(es) excluded._

## What happened

- Cases: 10  ·  **delivered: 9**  ·  automated 8  ·  already-covered 1  ·  merged-sanctioned-red 1
- Gate: green (3 runs)
- Findings reported: 118  ·  fix rounds: 1

## What it cost

- Total: $197.47  ·  11.6h active (cases 296m · lead 366m · stages 33m)  ·  23.5 dispatches
- Tokens: total 241,239,396  ·  **real work 1,174,478** (in 2,797 / out 1,171,681)  ·  cache 232.5M read / 7.6M write  ·  **cache hit rate 96.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 414 turns  ·  1481 tool calls (31 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $69.04 (35%)
  - by stage: lead $55.09 · triage $11.97 (26m) · other $1.98 (7m)
- Rework (fix rounds — already inside per-case direct): $12.14  ·  1 dispatch(es)  ·  36m
- **Per delivered case (incl. overhead): $21.94**
- Avg direct per case (excl. overhead): $25.69
- Direct cost spread: avg $25.69 · median $29.77 · min $3.85 · max $37.65
- Loaded cost spread (direct + even overhead share): avg $19.74 · median $8.82 · min $6.90 · max $44.55
- Active-time spread: avg 59m · median 72m · min 8m · max 99m  ·  loaded: avg 70m · median 44m · min 40m · max 139m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2003 | automated | $3.85 | $10.75 | 23,524 (in 68 / out 23k) | 8m | 48m | 1 | 44 (2) | 0 | 11 |
| ELITEA-2063 | already-covered | $37.65 | $44.55 | 198,195 (in 486 / out 198k) | 85m | 125m | 4 | 273 (6) | 0 | 2 |
| ELITEA-2022 | automated | $37.10 | $44.00 | 230,711 (in 452 / out 230k) | 99m | 139m | 6 | 243 (8) | 1 | 8 |
| ELITEA-2012 | automated | n/a | $6.90 | 0 (incl. cache) | 0m | 40m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2050 | automated | n/a | $6.90 | 0 (incl. cache) | 0m | 40m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2049 | automated | n/a | $6.90 | 0 (incl. cache) | 0m | 40m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2051 | merged-sanctioned-red | $29.77 | $36.67 | 160,853 (in 464 / out 160k) | 72m | 112m | 5 | 237 (5) | 0 | 16 |
| ELITEA-2024 | automated | $20.06 | $26.96 | 133,204 (in 270 / out 133k) | 32m | 72m | 5 | 154 (1) | 0 | 11 |
| ELITEA-2025 | automated | n/a | $6.90 | 0 (incl. cache) | 0m | 40m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2013 | automated | n/a | $6.90 | 0 (incl. cache) | 0m | 40m | 0 | 0 (0) | 0 | 16 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $76.91 | 9.5 | 392,745 (in 1k / out 392k) | 96.1% | 194m | 527 (14) |
| qa-engineer | $65.47 | 14 | 439,816 (in 958 / out 439k) | 96.5% | 135m | 546 (10) |
| test-automation-lead | $55.09 | 0 | 341,917 (in 828 / out 341k) | 98.2% | 366m | 408 (7) |

Unattributed (no dispatch named them in any captured session): ELITEA-2012, ELITEA-2050, ELITEA-2049, ELITEA-2025, ELITEA-2013

---

# Batch cost — pipelines-remaining-w3

Generated: 2026-09-14T11:44:34.574Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 5  ·  **delivered: 5**  ·  automated 5
- Gate: green (3 runs)
- Findings reported: 40  ·  fix rounds: 1

## What it cost

- Total: $38.43  ·  4.0h active (cases 189m · lead 50m · stages 0m)  ·  3 dispatches
- Tokens: total 34,289,961  ·  **real work 222,573** (in 378 / out 222,195)  ·  cache 31.4M read / 2.6M write  ·  **cache hit rate 92.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 36 turns  ·  201 tool calls (7 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $5.49 (14%)
- Rework (fix rounds — already inside per-case direct): $22.33  ·  1 dispatch(es)  ·  131m
- **Per delivered case (incl. overhead): $7.69**
- Avg direct per case (excl. overhead): $32.94
- Direct cost spread: avg $32.94 · median $32.94 · min $32.94 · max $32.94
- Loaded cost spread (direct + even overhead share): avg $7.69 · median $1.10 · min $1.10 · max $34.04
- Active-time spread: avg 189m · median 189m · min 189m · max 189m  ·  loaded: avg 48m · median 10m · min 10m · max 199m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2027 | automated | n/a | $1.10 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2029 | automated | n/a | $1.10 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2067 | automated | n/a | $1.10 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2016 | automated | $32.94 | $34.04 | 187,870 (in 306 / out 188k) | 189m | 199m | 3 | 165 (6) | 1 | 12 |
| ELITEA-2041 | automated | n/a | $1.10 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $22.33 | 1 | 98,120 (in 176 / out 98k) | 90.3% | 131m | 95 (4) |
| qa-engineer | $10.62 | 2 | 89,750 (in 130 / out 90k) | 93.1% | 58m | 70 (2) |
| test-automation-lead | $5.49 | 0 | 34,703 (in 72 / out 35k) | 97.1% | 50m | 36 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2027, ELITEA-2029, ELITEA-2067, ELITEA-2041

---

# Batch cost — pipelines-remaining-w4

Generated: 2026-09-14T11:44:34.576Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 6  ·  **delivered: 5**  ·  automated 5  ·  already-covered 1
- Gate: green (3 runs)
- Findings reported: 41  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2019 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2057 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2060 | already-covered | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2061 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2072 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 6 |
| ELITEA-2048 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2019, ELITEA-2057, ELITEA-2060, ELITEA-2061, ELITEA-2072, ELITEA-2048

---

# Batch cost — pipelines-remaining-w5

Generated: 2026-09-14T11:44:34.577Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 7  ·  **delivered: 0**  ·  merged-ungated 6  ·  blocked 1
- Gate: not-run (1 runs)
- Findings reported: 17  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2017 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |
| ELITEA-2052 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2053 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2058 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2059 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2062 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-2071 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2017, ELITEA-2052, ELITEA-2053, ELITEA-2058, ELITEA-2059, ELITEA-2062, ELITEA-2071

---

# Batch cost — pipelines-remaining-w6

Generated: 2026-09-14T11:44:34.579Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

## What happened

- Cases: 8  ·  **delivered: 6**  ·  automated 6  ·  already-covered 2
- Gate: green (3 runs)
- Findings reported: 71  ·  fix rounds: 0

## What it cost

- Total: $12.37  ·  0.5h active (cases 8m · lead 24m · stages 0m)  ·  2 dispatches
- Tokens: total 14,546,612  ·  **real work 76,012** (in 204 / out 75,808)  ·  cache 14.0M read / 449k write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 74 turns  ·  107 tool calls (2 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $8.32 (67%)
- **Per delivered case (incl. overhead): $2.06**
- Avg direct per case (excl. overhead): $4.06
- Direct cost spread: avg $4.06 · median $4.06 · min $4.06 · max $4.06
- Loaded cost spread (direct + even overhead share): avg $1.55 · median $1.04 · min $1.04 · max $5.10
- Active-time spread: avg 8m · median 8m · min 8m · max 8m  ·  loaded: avg 4m · median 3m · min 3m · max 11m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2043 | automated | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2044 | automated | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2066 | automated | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 6 |
| ELITEA-2054 | already-covered | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2055 | already-covered | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2056 | automated | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2064 | automated | n/a | $1.04 | 0 (incl. cache) | 0m | 3m | 0 | 0 (0) | 0 | 16 |
| ELITEA-2065 | automated | $4.06 | $5.10 | 28,178 (in 56 / out 28k) | 8m | 11m | 2 | 34 (1) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $8.32 | 0 | 47,834 (in 148 / out 48k) | 98.4% | 24m | 73 (1) |
| qa-engineer | $2.19 | 1 | 19,766 (in 28 / out 20k) | 92.3% | 5m | 18 (1) |
| test-automation-engineer | $1.86 | 1 | 8,412 (in 28 / out 8k) | 92.4% | 3m | 16 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2043, ELITEA-2044, ELITEA-2066, ELITEA-2054, ELITEA-2055, ELITEA-2056, ELITEA-2064

---

# Batch cost — pipelines-remaining-w7

Generated: 2026-09-14T11:44:34.581Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

## What happened

- Cases: 11  ·  **delivered: 0**  ·  merged-ungated 11
- Gate: not-run
- Findings reported: 120  ·  fix rounds: 1

## What it cost

- Total: $55.37  ·  3.4h active (cases 91m · lead 113m · stages 0m)  ·  7 dispatches
- Tokens: total 65,517,300  ·  **real work 354,235** (in 772 / out 353,463)  ·  cache 63.0M read / 2.2M write  ·  **cache hit rate 96.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 133 turns  ·  417 tool calls (11 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $17.87 (32%)
- Rework (fix rounds — already inside per-case direct): $2.30  ·  1 dispatch(es)  ·  3m
- Avg direct per case (excl. overhead): $12.50
- Direct cost spread: avg $12.50 · median $15.12 · min $2.61 · max $19.76
- Loaded cost spread (direct + even overhead share): avg $5.03 · median $1.62 · min $1.62 · max $21.38
- Active-time spread: avg 30m · median 33m · min 10m · max 48m  ·  loaded: avg 18m · median 10m · min 10m · max 58m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2011 | merged-ungated | $2.61 | $4.23 | 22,185 (in 19 / out 22k) | 10m | 20m | 0.5 | 13 (0) | 0 | 12 |
| ELITEA-2070 | merged-ungated | $15.12 | $16.74 | 110,048 (in 183 / out 110k) | 48m | 58m | 2.5 | 106 (2) | 0 | 14 |
| ELITEA-2451 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2454 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2443 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2444 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2445 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2446 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2447 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 7 |
| ELITEA-2448 | merged-ungated | $19.76 | $21.38 | 108,768 (in 304 / out 108k) | 33m | 43m | 4 | 167 (8) | 1 | 10 |
| ELITEA-2449 | merged-ungated | n/a | $1.62 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $24.48 | 4 | 161,562 (in 336 / out 161k) | 96.5% | 56m | 200 (8) |
| test-automation-lead | $17.87 | 0 | 113,235 (in 266 / out 113k) | 98.2% | 113m | 131 (1) |
| test-automation-engineer | $13.02 | 3 | 79,438 (in 170 / out 79k) | 94.8% | 34m | 86 (2) |

Unattributed (no dispatch named them in any captured session): ELITEA-2451, ELITEA-2454, ELITEA-2443, ELITEA-2444, ELITEA-2445, ELITEA-2446, ELITEA-2447, ELITEA-2449

---

# Batch cost — settings-project-params

Generated: 2026-09-14T11:44:34.615Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 192 other-batch dispatch(es) excluded._

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 11  ·  fix rounds: 1

## What it cost

- Total: $30.69  ·  2.4h active (cases 21m · lead 110m · stages 15m)  ·  4 dispatches
- Tokens: total 44,478,492  ·  **real work 159,976** (in 392 / out 159,584)  ·  cache 43.3M read / 1.0M write  ·  **cache hit rate 97.7%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  200 tool calls (5 err, 98% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.36 (60%)
  - by stage: lead $13.55 · triage $0.01 (0m) · gate $0.22 (1m) · report $0.38 (5m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $8.88  ·  1 dispatch(es)  ·  14m
- **Per delivered case (incl. overhead): $30.69**
- Avg direct per case (excl. overhead): $12.33
- Direct cost spread: avg $12.33 · median $12.33 · min $12.33 · max $12.33
- Loaded cost spread (direct + even overhead share): avg $30.69 · median $30.69 · min $30.69 · max $30.69
- Active-time spread: avg 21m · median 21m · min 21m · max 21m  ·  loaded: avg 146m · median 146m · min 146m · max 146m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2272 | automated | $12.33 | $30.69 | 80,771 (in 176 / out 81k) | 21m | 146m | 2 | 114 (1) | 1 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| test-automation-engineer | $11.61 | 2.6 | 92,962 (in 223 / out 93k) | 96.7% | 26m | 107 (4) |
| qa-engineer | $5.53 | 1.4 | 38,169 (in 80 / out 38k) | 95.5% | 11m | 49 (0) |

---

# Batch cost — settings-w01

Generated: 2026-09-14T11:44:34.650Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 168 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 5**  ·  automated 4  ·  blocked 4  ·  merged-sanctioned-red 1
- Gate: green (3 runs)
- Gate record (script-authored): red at 2026-08-26T05:11:49.162Z (7 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `red` — write the verdict back into report.json
- Findings reported: 70  ·  fix rounds: 0.99

## What it cost

- Total: $67.84  ·  4.5h active (cases 131m · lead 110m · stages 31m)  ·  28 dispatches
- Tokens: total 122,188,688  ·  **real work 653,287** (in 1,965 / out 651,322)  ·  cache 117.4M read / 4.1M write  ·  **cache hit rate 96.6%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  830 tool calls (30 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.08 (31%)
  - by stage: lead $13.55 · triage $0.31 (2m) · gate $1.70 (4m) · report $1.32 (16m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $1.69  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $13.57**
- Avg direct per case (excl. overhead): $5.85
- Direct cost spread: avg $5.85 · median $5.43 · min $2.83 · max $10.97
- Loaded cost spread (direct + even overhead share): avg $7.54 · median $6.05 · min $2.34 · max $13.31
- Active-time spread: avg 16m · median 13m · min 7m · max 27m  ·  loaded: avg 31m · median 27m · min 16m · max 43m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2242 | automated | $7.15 | $9.49 | 85,618 (in 270 / out 85k) | 26m | 42m | 2.67 | 137 (4) | 0.33 | 14 |
| ELITEA-2243 | merged-sanctioned-red | $7.15 | $9.49 | 85,618 (in 270 / out 85k) | 26m | 42m | 2.67 | 137 (4) | 0.33 | 14 |
| ELITEA-2244 | automated | $2.83 | $5.17 | 38,068 (in 144 / out 38k) | 8m | 24m | 1.67 | 71 (2) | 0.33 | 14 |
| ELITEA-2249 | blocked | $3.71 | $6.05 | 34,435 (in 64 / out 34k) | 11m | 27m | 1 | 41 (2) | 0 | 3 |
| ELITEA-2250 | blocked | $3.71 | $6.05 | 34,435 (in 64 / out 34k) | 11m | 27m | 1 | 41 (2) | 0 | 3 |
| ELITEA-2251 | automated | $8.17 | $10.51 | 61,911 (in 183 / out 62k) | 15m | 31m | 3 | 79 (3) | 0 | 3 |
| ELITEA-2252 | automated | $10.97 | $13.31 | 118,676 (in 266 / out 118k) | 27m | 43m | 6 | 136 (2) | 0 | 9 |
| ELITEA-2253 | blocked | $3.08 | $5.42 | 28,659 (in 61 / out 29k) | 7m | 23m | 1 | 36 (1) | 0 | 5 |
| ELITEA-2254 | blocked | n/a | $2.34 | 0 (incl. cache) | 0m | 16m | 0 | 0 (0) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $31.59 | 12.4 | 334,211 (in 893 / out 333k) | 96.4% | 95m | 436 (11) |
| test-automation-engineer | $22.70 | 15.6 | 290,231 (in 983 / out 289k) | 95.7% | 66m | 350 (18) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2254

---

# Batch cost — settings-w02

Generated: 2026-09-14T11:44:34.684Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 176 other-batch dispatch(es) excluded._

## What happened

- Cases: 9  ·  **delivered: 7**  ·  automated 7  ·  blocked 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-26T08:25:10.091Z (8 run record(s))
- Findings reported: 1  ·  fix rounds: 1.99

## What it cost

- Total: $87.58  ·  4.4h active (cases 132m · lead 110m · stages 23m)  ·  20 dispatches
- Tokens: total 113,889,614  ·  **real work 581,235** (in 1,518 / out 579,717)  ·  cache 109.8M read / 3.5M write  ·  **cache hit rate 96.9%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  717 tool calls (19 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $20.96 (24%)
  - by stage: lead $13.55 · triage $0.20 (1m) · gate $2.72 (11m) · report $0.30 (2m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $9.30  ·  2 dispatch(es)  ·  19m
- **Per delivered case (incl. overhead): $12.51**
- Avg direct per case (excl. overhead): $8.33
- Direct cost spread: avg $8.33 · median $8.73 · min $2.94 · max $12.90
- Loaded cost spread (direct + even overhead share): avg $9.73 · median $10.19 · min $2.33 · max $15.23
- Active-time spread: avg 17m · median 16m · min 6m · max 28m  ·  loaded: avg 30m · median 30m · min 15m · max 43m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2255 | automated | $9.59 | $11.92 | 63,480 (in 164 / out 63k) | 15m | 30m | 1.83 | 80 (1) | 0.33 | 1 |
| ELITEA-2256 | automated | $9.59 | $11.92 | 63,480 (in 164 / out 63k) | 15m | 30m | 1.83 | 80 (1) | 0.33 | 0 |
| ELITEA-2260 | automated | $3.84 | $6.17 | 25,341 (in 78 / out 25k) | 6m | 21m | 1.33 | 37 (0) | 0.33 | 0 |
| ELITEA-2258 | automated | $7.86 | $10.19 | 64,987 (in 145 / out 65k) | 16m | 31m | 2 | 71 (1) | 0 | 0 |
| ELITEA-2264 | automated | $7.86 | $10.19 | 64,987 (in 145 / out 65k) | 16m | 31m | 2 | 71 (1) | 0 | 0 |
| ELITEA-2265 | blocked | n/a | $2.33 | 0 (incl. cache) | 0m | 15m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2261 | automated | $12.03 | $14.36 | 91,486 (in 209 / out 91k) | 27m | 42m | 3 | 102 (5) | 0.5 | 0 |
| ELITEA-2262 | blocked | $2.94 | $5.27 | 27,425 (in 43 / out 27k) | 9m | 24m | 0.5 | 22 (2) | 0 | 0 |
| ELITEA-2263 | automated | $12.90 | $15.23 | 89,809 (in 232 / out 90k) | 28m | 43m | 3.5 | 126 (4) | 0.5 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $43.00 | 11.6 | 314,060 (in 900 / out 313k) | 96.7% | 93m | 383 (11) |
| qa-engineer | $31.03 | 8.4 | 238,330 (in 529 / out 238k) | 96.0% | 62m | 290 (7) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2265

---

# Batch cost — settings-w03

Generated: 2026-09-14T11:44:34.719Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 175 other-batch dispatch(es) excluded._

## What happened

- Cases: 10  ·  **delivered: 10**  ·  automated 10
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-26T11:54:49.196Z (8 run record(s))
- Findings reported: 82  ·  fix rounds: 2.98

## What it cost

- Total: $108.10  ·  5.2h active (cases 151m · lead 110m · stages 52m)  ·  21 dispatches
- Tokens: total 145,285,235  ·  **real work 646,759** (in 1,846 / out 644,913)  ·  cache 140.5M read / 4.1M write  ·  **cache hit rate 97.1%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  898 tool calls (25 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $22.94 (21%)
  - by stage: lead $13.55 · triage $0.24 (4m) · gate $4.57 (34m) · report $0.38 (5m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $16.81  ·  3 dispatch(es)  ·  29m
- **Per delivered case (incl. overhead): $10.81**
- Avg direct per case (excl. overhead): $8.52
- Direct cost spread: avg $8.52 · median $8.46 · min $2.70 · max $14.03
- Loaded cost spread (direct + even overhead share): avg $10.81 · median $10.75 · min $4.99 · max $16.32
- Active-time spread: avg 15m · median 15m · min 5m · max 25m  ·  loaded: avg 31m · median 31m · min 21m · max 41m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2266 | automated | $14.03 | $16.32 | 92,776 (in 227 / out 93k) | 25m | 41m | 2.67 | 127 (2) | 0.33 | 41 |
| ELITEA-2267 | automated | $14.03 | $16.32 | 92,776 (in 227 / out 93k) | 25m | 41m | 2.67 | 127 (2) | 0.33 | 41 |
| ELITEA-2276 | automated | $8.52 | $10.81 | 58,002 (in 130 / out 58k) | 15m | 31m | 1.67 | 72 (2) | 0.33 | 0 |
| ELITEA-2268 | automated | $8.40 | $10.69 | 55,953 (in 150 / out 56k) | 15m | 31m | 1.5 | 76 (1) | 0.25 | 0 |
| ELITEA-2273 | automated | $8.40 | $10.69 | 55,953 (in 150 / out 56k) | 15m | 31m | 1.5 | 76 (1) | 0.25 | 0 |
| ELITEA-2274 | automated | $2.70 | $4.99 | 18,120 (in 57 / out 18k) | 5m | 21m | 1 | 26 (0) | 0.25 | 0 |
| ELITEA-2275 | automated | $2.70 | $4.99 | 18,120 (in 57 / out 18k) | 5m | 21m | 1 | 26 (0) | 0.25 | 0 |
| ELITEA-2269 | automated | $11.50 | $13.79 | 64,862 (in 198 / out 65k) | 20m | 36m | 1.83 | 103 (4) | 0.33 | 0 |
| ELITEA-2270 | automated | $11.50 | $13.79 | 64,862 (in 198 / out 65k) | 20m | 36m | 1.83 | 103 (4) | 0.33 | 0 |
| ELITEA-2271 | automated | $3.38 | $5.67 | 23,293 (in 72 / out 23k) | 6m | 22m | 1.33 | 33 (1) | 0.33 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $64.61 | 12.6 | 412,362 (in 1k / out 411k) | 97.2% | 146m | 567 (19) |
| qa-engineer | $29.94 | 8.4 | 205,552 (in 573 / out 205k) | 96.0% | 57m | 287 (5) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

---

# Batch cost — settings-w04

Generated: 2026-09-14T11:44:34.755Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 179 other-batch dispatch(es) excluded._

## What happened

- Cases: 11  ·  **delivered: 10**  ·  automated 8  ·  merged-sanctioned-red 2  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-27T19:11:38.992Z (6 run record(s))
- Findings reported: 65  ·  fix rounds: 0

## What it cost

- Total: $75.88  ·  3.9h active (cases 94m · lead 110m · stages 30m)  ·  17 dispatches
- Tokens: total 103,818,768  ·  **real work 528,131** (in 1,465 / out 526,666)  ·  cache 100.2M read / 3.1M write  ·  **cache hit rate 97.0%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  574 tool calls (18 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.36 (28%)
  - by stage: lead $13.55 · triage $0.27 (2m) · gate $2.31 (10m) · report $1.04 (9m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $7.59**
- Avg direct per case (excl. overhead): $4.96
- Direct cost spread: avg $4.96 · median $4.61 · min $2.69 · max $8.42
- Loaded cost spread (direct + even overhead share): avg $6.90 · median $6.55 · min $4.63 · max $10.36
- Active-time spread: avg 9m · median 8m · min 5m · max 14m  ·  loaded: avg 22m · median 21m · min 18m · max 27m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2278 | blocked | $3.81 | $5.75 | 27,092 (in 62 / out 27k) | 6m | 19m | 0.5 | 34 (2) | 0 | 7 |
| ELITEA-2279 | automated | $8.42 | $10.36 | 59,928 (in 155 / out 60k) | 14m | 27m | 2 | 73 (2) | 0 | 18 |
| ELITEA-2287 | automated | $4.61 | $6.55 | 32,836 (in 93 / out 33k) | 8m | 21m | 1.5 | 39 (1) | 0 | 18 |
| ELITEA-2281 | automated | $5.63 | $7.57 | 44,928 (in 88 / out 45k) | 11m | 24m | 1.25 | 41 (1) | 0 | 17 |
| ELITEA-2282 | automated | $5.63 | $7.57 | 44,928 (in 88 / out 45k) | 11m | 24m | 1.25 | 41 (1) | 0 | 1 |
| ELITEA-2283 | automated | $2.69 | $4.63 | 17,592 (in 49 / out 18k) | 5m | 18m | 0.75 | 20 (1) | 0 | 0 |
| ELITEA-2288 | automated | $2.69 | $4.63 | 17,592 (in 49 / out 18k) | 5m | 18m | 0.75 | 20 (1) | 0 | 0 |
| ELITEA-2285 | automated | $7.39 | $9.33 | 54,485 (in 123 / out 54k) | 12m | 25m | 1.25 | 63 (2) | 0 | 2 |
| ELITEA-2289 | merged-sanctioned-red | $7.39 | $9.33 | 54,485 (in 123 / out 54k) | 12m | 25m | 1.25 | 63 (2) | 0 | 1 |
| ELITEA-2290 | automated | $3.13 | $5.07 | 20,605 (in 55 / out 21k) | 5m | 18m | 0.75 | 24 (1) | 0 | 0 |
| ELITEA-2291 | merged-sanctioned-red | $3.13 | $5.07 | 20,605 (in 55 / out 21k) | 5m | 18m | 0.75 | 24 (1) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $35.44 | 7.4 | 274,942 (in 627 / out 274k) | 96.8% | 63m | 306 (9) |
| test-automation-engineer | $26.89 | 9.6 | 224,344 (in 749 / out 224k) | 96.0% | 60m | 224 (8) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

---

# Batch cost — settings-w05

Generated: 2026-09-14T11:44:34.788Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 169 other-batch dispatch(es) excluded._

## What happened

- Cases: 14  ·  **delivered: 13**  ·  merged-sanctioned-red 9  ·  automated 4  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-27T22:31:47.979Z (6 run record(s))
- Findings reported: 27  ·  fix rounds: 5

## What it cost

- Total: $126.49  ·  5.2h active (cases 163m · lead 110m · stages 38m)  ·  27 dispatches
- Tokens: total 174,677,257  ·  **real work 808,842** (in 2,390 / out 806,452)  ·  cache 169.0M read / 4.8M write  ·  **cache hit rate 97.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  1039 tool calls (27 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $22.29 (18%)
  - by stage: lead $13.55 · triage $0.29 (1m) · gate $2.92 (16m) · report $1.33 (12m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $16.42  ·  5 dispatch(es)  ·  29m
- **Per delivered case (incl. overhead): $9.73**
- Avg direct per case (excl. overhead): $7.44
- Direct cost spread: avg $7.44 · median $7.97 · min $0.99 · max $15.99
- Loaded cost spread (direct + even overhead share): avg $9.03 · median $9.56 · min $2.58 · max $17.58
- Active-time spread: avg 12m · median 12m · min 2m · max 29m  ·  loaded: avg 23m · median 23m · min 13m · max 40m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2330 | merged-sanctioned-red | $9.25 | $10.84 | 57,385 (in 147 / out 57k) | 13m | 24m | 1.3 | 69 (1) | 0.2 | 27 |
| ELITEA-2331 | merged-sanctioned-red | $9.25 | $10.84 | 57,385 (in 147 / out 57k) | 13m | 24m | 1.3 | 69 (1) | 0.2 | 0 |
| ELITEA-2332 | merged-sanctioned-red | $1.98 | $3.57 | 13,634 (in 44 / out 14k) | 3m | 14m | 0.8 | 17 (0) | 0.2 | 0 |
| ELITEA-2334 | merged-sanctioned-red | $1.98 | $3.57 | 13,634 (in 44 / out 14k) | 3m | 14m | 0.8 | 17 (0) | 0.2 | 0 |
| ELITEA-2342 | merged-sanctioned-red | $1.98 | $3.57 | 13,634 (in 44 / out 14k) | 3m | 14m | 0.8 | 17 (0) | 0.2 | 0 |
| ELITEA-2335 | merged-sanctioned-red | $7.97 | $9.56 | 49,345 (in 138 / out 49k) | 12m | 23m | 1 | 64 (1) | 0 | 0 |
| ELITEA-2339 | merged-sanctioned-red | $7.97 | $9.56 | 49,345 (in 138 / out 49k) | 12m | 23m | 1 | 64 (1) | 0 | 0 |
| ELITEA-2340 | merged-sanctioned-red | $0.99 | $2.58 | 7,161 (in 30 / out 7k) | 2m | 13m | 0.5 | 10 (0) | 0 | 0 |
| ELITEA-2341 | merged-sanctioned-red | $0.99 | $2.58 | 7,161 (in 30 / out 7k) | 2m | 13m | 0.5 | 10 (0) | 0 | 0 |
| ELITEA-2345 | automated | $14.92 | $16.51 | 73,533 (in 274 / out 73k) | 21m | 32m | 2.5 | 131 (5) | 0 | 0 |
| ELITEA-2346 | automated | $14.92 | $16.51 | 73,533 (in 274 / out 73k) | 21m | 32m | 2.5 | 131 (5) | 0 | 0 |
| ELITEA-2333 | blocked | $5.45 | $7.04 | 41,004 (in 82 / out 41k) | 10m | 21m | 0.5 | 50 (2) | 0 | 0 |
| ELITEA-2348 | automated | $15.99 | $17.58 | 122,131 (in 235 / out 122k) | 29m | 40m | 4 | 145 (2) | 2 | 0 |
| ELITEA-2349 | automated | $10.54 | $12.13 | 81,127 (in 153 / out 81k) | 19m | 30m | 3.5 | 95 (1) | 2 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $69.87 | 16.6 | 519,189 (in 2k / out 518k) | 97.1% | 136m | 602 (16) |
| qa-engineer | $43.06 | 10.4 | 260,808 (in 783 / out 260k) | 96.7% | 67m | 393 (10) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

---

# Batch cost — settings-w06

Generated: 2026-09-14T11:44:34.823Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 171 other-batch dispatch(es) excluded._

## What happened

- Cases: 15  ·  **delivered: 9**  ·  automated 9  ·  blocked 6
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-28T18:36:21.219Z (6 run record(s))
- Findings reported: 0  ·  fix rounds: 3.980000000000001

## What it cost

- Total: $158.43  ·  6.8h active (cases 275m · lead 110m · stages 26m)  ·  25 dispatches
- Tokens: total 213,588,673  ·  **real work 1,007,900** (in 2,503 / out 1,005,397)  ·  cache 207.1M read / 5.5M write  ·  **cache hit rate 97.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  1155 tool calls (29 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.73 (14%)
  - by stage: lead $13.55 · triage $0.45 (3m) · gate $3.15 (13m) · report $0.37 (1m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $24.56  ·  4 dispatch(es)  ·  57m
- **Per delivered case (incl. overhead): $17.60**
- Avg direct per case (excl. overhead): $9.11
- Direct cost spread: avg $9.11 · median $9.04 · min $4.03 · max $20.12
- Loaded cost spread (direct + even overhead share): avg $10.56 · median $10.49 · min $5.48 · max $21.57
- Active-time spread: avg 18m · median 17m · min 9m · max 45m  ·  loaded: avg 27m · median 26m · min 18m · max 54m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2314 | blocked | $20.12 | $21.57 | 118,961 (in 279 / out 119k) | 45m | 54m | 2.08 | 142 (4) | 0.33 | 0 |
| ELITEA-2315 | blocked | $20.12 | $21.57 | 118,961 (in 279 / out 119k) | 45m | 54m | 2.08 | 142 (4) | 0.33 | 0 |
| ELITEA-2316 | blocked | $4.03 | $5.48 | 28,206 (in 53 / out 28k) | 9m | 18m | 0.83 | 29 (1) | 0.33 | 0 |
| ELITEA-2317 | blocked | $9.04 | $10.49 | 58,351 (in 123 / out 58k) | 19m | 28m | 1.58 | 64 (2) | 0.33 | 0 |
| ELITEA-2318 | blocked | $9.04 | $10.49 | 58,351 (in 123 / out 58k) | 19m | 28m | 1.58 | 64 (2) | 0.33 | 0 |
| ELITEA-2319 | blocked | $4.03 | $5.48 | 28,206 (in 53 / out 28k) | 9m | 18m | 0.83 | 29 (1) | 0.33 | 0 |
| ELITEA-2311 | automated | $10.03 | $11.48 | 71,428 (in 154 / out 71k) | 17m | 26m | 1.5 | 76 (1) | 0.2 | 0 |
| ELITEA-2322 | automated | $10.03 | $11.48 | 71,428 (in 154 / out 71k) | 17m | 26m | 1.5 | 76 (1) | 0.2 | 0 |
| ELITEA-2323 | automated | $5.55 | $7.00 | 35,922 (in 87 / out 36k) | 9m | 18m | 1 | 42 (1) | 0.2 | 0 |
| ELITEA-2324 | automated | $5.55 | $7.00 | 35,922 (in 87 / out 36k) | 9m | 18m | 1 | 42 (1) | 0.2 | 0 |
| ELITEA-2325 | automated | $5.55 | $7.00 | 35,922 (in 87 / out 36k) | 9m | 18m | 1 | 42 (1) | 0.2 | 0 |
| ELITEA-2326 | automated | $9.79 | $11.24 | 77,059 (in 152 / out 77k) | 21m | 30m | 1.75 | 79 (1) | 0.25 | 0 |
| ELITEA-2327 | automated | $9.79 | $11.24 | 77,059 (in 152 / out 77k) | 21m | 30m | 1.75 | 79 (1) | 0.25 | 0 |
| ELITEA-2328 | automated | $7.00 | $8.45 | 48,692 (in 115 / out 49k) | 13m | 22m | 1.25 | 56 (1) | 0.25 | 0 |
| ELITEA-2329 | automated | $7.00 | $8.45 | 48,692 (in 115 / out 49k) | 13m | 22m | 1.25 | 56 (1) | 0.25 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $95.63 | 13.6 | 611,790 (in 2k / out 610k) | 97.7% | 212m | 700 (24) |
| qa-engineer | $49.25 | 11.4 | 367,265 (in 899 / out 366k) | 96.2% | 88m | 411 (4) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

---

# Batch cost — settings-w07

Generated: 2026-09-14T11:44:34.857Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 184 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 6**  ·  automated 6
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-28T19:32:34.686Z (3 run record(s))
- Findings reported: 0  ·  fix rounds: 1.9800000000000002

## What it cost

- Total: $85.20  ·  4.5h active (cases 146m · lead 110m · stages 14m)  ·  12 dispatches
- Tokens: total 119,266,319  ·  **real work 488,367** (in 1,345 / out 487,022)  ·  cache 115.9M read / 2.9M write  ·  **cache hit rate 97.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  581 tool calls (18 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $18.80 (22%)
  - by stage: lead $13.55 · triage $0.45 (3m) · gate $0.22 (1m) · report $0.37 (1m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $13.34  ·  2 dispatch(es)  ·  37m
- **Per delivered case (incl. overhead): $14.20**
- Avg direct per case (excl. overhead): $11.06
- Direct cost spread: avg $11.06 · median $9.04 · min $4.03 · max $20.12
- Loaded cost spread (direct + even overhead share): avg $14.19 · median $12.17 · min $7.16 · max $23.25
- Active-time spread: avg 24m · median 19m · min 9m · max 45m  ·  loaded: avg 45m · median 40m · min 30m · max 66m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2314 | automated | $20.12 | $23.25 | 118,961 (in 279 / out 119k) | 45m | 66m | 2.08 | 142 (4) | 0.33 | 0 |
| ELITEA-2315 | automated | $20.12 | $23.25 | 118,961 (in 279 / out 119k) | 45m | 66m | 2.08 | 142 (4) | 0.33 | 0 |
| ELITEA-2316 | automated | $4.03 | $7.16 | 28,206 (in 53 / out 28k) | 9m | 30m | 0.83 | 29 (1) | 0.33 | 0 |
| ELITEA-2317 | automated | $9.04 | $12.17 | 58,351 (in 123 / out 58k) | 19m | 40m | 1.58 | 64 (2) | 0.33 | 0 |
| ELITEA-2318 | automated | $9.04 | $12.17 | 58,351 (in 123 / out 58k) | 19m | 40m | 1.58 | 64 (2) | 0.33 | 0 |
| ELITEA-2319 | automated | $4.03 | $7.16 | 28,206 (in 53 / out 28k) | 9m | 30m | 0.83 | 29 (1) | 0.33 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $54.10 | 6.6 | 322,864 (in 799 / out 322k) | 97.7% | 128m | 383 (15) |
| qa-engineer | $17.55 | 5.4 | 136,658 (in 457 / out 136k) | 95.4% | 33m | 154 (2) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

---

# Batch cost — settings-w08

Generated: 2026-09-14T11:44:34.892Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 171 other-batch dispatch(es) excluded._

## What happened

- Cases: 17  ·  **delivered: 15**  ·  automated 14  ·  blocked 2  ·  merged-sanctioned-red 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-28T23:48:09.597Z (6 run record(s))
- Findings reported: 1  ·  fix rounds: 2.99

## What it cost

- Total: $140.53  ·  5.8h active (cases 197m · lead 110m · stages 42m)  ·  25 dispatches
- Tokens: total 190,939,987  ·  **real work 830,101** (in 2,365 / out 827,736)  ·  cache 184.9M read / 5.2M write  ·  **cache hit rate 97.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  1101 tool calls (30 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $23.92 (17%)
  - by stage: lead $13.55 · triage $0.38 (2m) · gate $5.47 (29m) · report $0.32 (2m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $11.39  ·  3 dispatch(es)  ·  26m
- **Per delivered case (incl. overhead): $9.37**
- Avg direct per case (excl. overhead): $7.29
- Direct cost spread: avg $7.29 · median $6.62 · min $2.76 · max $13.43
- Loaded cost spread (direct + even overhead share): avg $8.27 · median $8.03 · min $1.41 · max $14.84
- Active-time spread: avg 12m · median 11m · min 6m · max 22m  ·  loaded: avg 21m · median 20m · min 9m · max 31m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2371 | blocked | $4.45 | $5.86 | 29,002 (in 72 / out 29k) | 7m | 16m | 0.5 | 40 (2) | 0 | 1 |
| ELITEA-2372 | automated | $11.06 | $12.47 | 77,005 (in 178 / out 77k) | 18m | 27m | 2.17 | 89 (3) | 0.33 | 0 |
| ELITEA-2373 | automated | $6.62 | $8.03 | 48,003 (in 106 / out 48k) | 11m | 20m | 1.67 | 50 (2) | 0.33 | 0 |
| ELITEA-2375 | automated | $13.43 | $14.84 | 67,994 (in 202 / out 68k) | 22m | 31m | 1.5 | 106 (3) | 0.25 | 0 |
| ELITEA-2376 | automated | $13.43 | $14.84 | 67,994 (in 202 / out 68k) | 22m | 31m | 1.5 | 106 (3) | 0.25 | 0 |
| ELITEA-2379 | automated | $2.76 | $4.17 | 19,425 (in 50 / out 19k) | 6m | 15m | 1 | 25 (0) | 0.25 | 0 |
| ELITEA-2380 | blocked | n/a | $1.41 | 0 (incl. cache) | 0m | 9m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2387 | automated | $6.62 | $8.03 | 48,003 (in 106 / out 48k) | 11m | 20m | 1.67 | 50 (2) | 0.33 | 0 |
| ELITEA-2390 | automated | $2.76 | $4.17 | 19,425 (in 50 / out 19k) | 6m | 15m | 1 | 25 (0) | 0.25 | 0 |
| ELITEA-2381 | automated | $10.14 | $11.55 | 65,551 (in 174 / out 65k) | 17m | 26m | 1.75 | 90 (2) | 0.25 | 0 |
| ELITEA-2382 | automated | $10.14 | $11.55 | 65,551 (in 174 / out 65k) | 17m | 26m | 1.75 | 90 (2) | 0.25 | 0 |
| ELITEA-2383 | automated | $4.52 | $5.93 | 33,471 (in 73 / out 33k) | 9m | 18m | 1.25 | 37 (1) | 0.25 | 0 |
| ELITEA-2384 | automated | $4.52 | $5.93 | 33,471 (in 73 / out 33k) | 9m | 18m | 1.25 | 37 (1) | 0.25 | 0 |
| ELITEA-2385 | merged-sanctioned-red | $9.54 | $10.95 | 58,980 (in 164 / out 59k) | 15m | 24m | 1.25 | 83 (3) | 0 | 0 |
| ELITEA-2386 | automated | $9.54 | $10.95 | 58,980 (in 164 / out 59k) | 15m | 24m | 1.25 | 83 (3) | 0 | 0 |
| ELITEA-2388 | automated | $3.54 | $4.95 | 21,646 (in 66 / out 22k) | 6m | 15m | 0.75 | 30 (1) | 0 | 0 |
| ELITEA-2389 | automated | $3.54 | $4.95 | 21,646 (in 66 / out 22k) | 6m | 15m | 0.75 | 30 (1) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $68.26 | 13.6 | 412,910 (in 1k / out 412k) | 97.0% | 144m | 532 (15) |
| qa-engineer | $58.72 | 11.4 | 388,346 (in 1k / out 387k) | 97.2% | 93m | 525 (14) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2380

---

# Batch cost — settings-w09

Generated: 2026-09-14T11:44:34.926Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 176 other-batch dispatch(es) excluded._

## What happened

- Cases: 15  ·  **delivered: 14**  ·  automated 13  ·  merged-sanctioned-red 1  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-29T16:54:26.548Z (6 run record(s))
- Findings reported: 0  ·  fix rounds: 2.0100000000000002

## What it cost

- Total: $111.29  ·  4.6h active (cases 136m · lead 110m · stages 33m)  ·  20 dispatches
- Tokens: total 163,457,577  ·  **real work 604,733** (in 2,047 / out 602,686)  ·  cache 159.2M read / 3.7M write  ·  **cache hit rate 97.8%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  867 tool calls (26 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $21.46 (19%)
  - by stage: lead $13.55 · triage $0.24 (1m) · gate $2.77 (18m) · report $0.70 (5m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $7.88  ·  2 dispatch(es)  ·  14m
- **Per delivered case (incl. overhead): $7.95**
- Avg direct per case (excl. overhead): $6.42
- Direct cost spread: avg $6.42 · median $7.26 · min $0.87 · max $13.68
- Loaded cost spread (direct + even overhead share): avg $7.42 · median $8.69 · min $1.43 · max $15.11
- Active-time spread: avg 10m · median 9m · min 1m · max 22m  ·  loaded: avg 19m · median 19m · min 10m · max 32m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2293 | automated | $13.68 | $15.11 | 66,483 (in 194 / out 66k) | 22m | 32m | 0.9 | 97 (5) | 0 | 0 |
| ELITEA-2294 | automated | $13.68 | $15.11 | 66,483 (in 194 / out 66k) | 22m | 32m | 0.9 | 97 (5) | 0 | 0 |
| ELITEA-2295 | automated | $0.87 | $2.30 | 5,662 (in 23 / out 6k) | 1m | 11m | 0.4 | 7 (0) | 0 | 0 |
| ELITEA-2296 | automated | $7.28 | $8.71 | 35,718 (in 146 / out 36k) | 9m | 19m | 1.17 | 65 (2) | 0 | 0 |
| ELITEA-2297 | automated | $7.28 | $8.71 | 35,718 (in 146 / out 36k) | 9m | 19m | 1.17 | 65 (2) | 0 | 0 |
| ELITEA-2298 | automated | $11.50 | $12.93 | 72,935 (in 189 / out 73k) | 19m | 29m | 2.5 | 95 (2) | 0.67 | 0 |
| ELITEA-2299 | merged-sanctioned-red | $11.50 | $12.93 | 72,935 (in 189 / out 73k) | 19m | 29m | 2.5 | 95 (2) | 0.67 | 0 |
| ELITEA-2300 | automated | $5.69 | $7.12 | 34,705 (in 102 / out 35k) | 9m | 19m | 2 | 49 (1) | 0.67 | 0 |
| ELITEA-2301 | automated | $7.26 | $8.69 | 38,589 (in 133 / out 38k) | 10m | 20m | 1.17 | 65 (1) | 0 | 0 |
| ELITEA-2302 | automated | $7.26 | $8.69 | 38,589 (in 133 / out 38k) | 10m | 20m | 1.17 | 65 (1) | 0 | 0 |
| ELITEA-2303 | automated | $1.16 | $2.59 | 7,825 (in 36 / out 8k) | 2m | 12m | 0.67 | 11 (0) | 0 | 0 |
| ELITEA-2305 | automated | $0.87 | $2.30 | 5,662 (in 23 / out 6k) | 1m | 11m | 0.4 | 7 (0) | 0 | 0 |
| ELITEA-2306 | blocked | n/a | $1.43 | 0 (incl. cache) | 0m | 10m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2308 | automated | $0.87 | $2.30 | 5,662 (in 23 / out 6k) | 1m | 11m | 0.4 | 7 (0) | 0 | 0 |
| ELITEA-2309 | automated | $0.93 | $2.36 | 6,718 (in 40 / out 7k) | 2m | 12m | 0.67 | 9 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $76.26 | 12.6 | 440,086 (in 2k / out 439k) | 98.1% | 135m | 642 (25) |
| qa-engineer | $21.48 | 7.4 | 135,802 (in 409 / out 135k) | 95.1% | 33m | 181 (0) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2306

---

# Batch cost — settings-w10

Generated: 2026-09-14T11:44:34.961Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 178 other-batch dispatch(es) excluded._

## What happened

- Cases: 13  ·  **delivered: 11**  ·  automated 8  ·  merged-sanctioned-red 3  ·  blocked 2
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-29T20:46:29.196Z (8 run record(s))
- Findings reported: 48  ·  fix rounds: 1

## What it cost

- Total: $118.78  ·  5.5h active (cases 166m · lead 110m · stages 54m)  ·  18 dispatches
- Tokens: total 161,179,885  ·  **real work 700,407** (in 1,826 / out 698,581)  ·  cache 156.1M read / 4.4M write  ·  **cache hit rate 97.3%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  855 tool calls (24 err, 97% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $26.11 (22%)
  - by stage: lead $13.55 · triage $0.19 (1m) · gate $7.78 (41m) · report $0.38 (3m) · other $4.20 (9m)
- Rework (fix rounds — already inside per-case direct): $3.72  ·  1 dispatch(es)  ·  7m
- **Per delivered case (incl. overhead): $10.80**
- Avg direct per case (excl. overhead): $8.42
- Direct cost spread: avg $8.42 · median $7.87 · min $3.00 · max $15.64
- Loaded cost spread (direct + even overhead share): avg $9.14 · median $9.88 · min $2.01 · max $17.65
- Active-time spread: avg 15m · median 13m · min 7m · max 26m  ·  loaded: avg 26m · median 26m · min 13m · max 39m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2393 | automated | $9.08 | $11.09 | 65,668 (in 149 / out 66k) | 16m | 29m | 2 | 80 (2) | 0 | 24 |
| ELITEA-2394 | automated | $9.08 | $11.09 | 65,668 (in 149 / out 66k) | 16m | 29m | 2 | 80 (2) | 0 | 24 |
| ELITEA-2417 | blocked | n/a | $2.01 | 0 (incl. cache) | 0m | 13m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2395 | automated | $7.87 | $9.88 | 46,295 (in 136 / out 46k) | 12m | 25m | 1.08 | 66 (2) | 0 | 0 |
| ELITEA-2396 | automated | $7.87 | $9.88 | 46,295 (in 136 / out 46k) | 12m | 25m | 1.08 | 66 (2) | 0 | 0 |
| ELITEA-2408 | merged-sanctioned-red | $7.87 | $9.88 | 46,295 (in 136 / out 46k) | 12m | 25m | 1.08 | 66 (2) | 0 | 0 |
| ELITEA-2409 | automated | $3.00 | $5.01 | 23,833 (in 53 / out 24k) | 7m | 20m | 0.75 | 23 (0) | 0 | 0 |
| ELITEA-2398 | automated | $15.64 | $17.65 | 91,161 (in 238 / out 91k) | 26m | 39m | 1.5 | 118 (3) | 0.2 | 0 |
| ELITEA-2410 | merged-sanctioned-red | $15.64 | $17.65 | 91,161 (in 238 / out 91k) | 26m | 39m | 1.5 | 118 (3) | 0.2 | 0 |
| ELITEA-2399 | automated | $5.54 | $7.55 | 41,675 (in 83 / out 42k) | 13m | 26m | 1 | 37 (1) | 0.2 | 0 |
| ELITEA-2400 | automated | $5.54 | $7.55 | 41,675 (in 83 / out 42k) | 13m | 26m | 1 | 37 (1) | 0.2 | 0 |
| ELITEA-2401 | merged-sanctioned-red | $5.54 | $7.55 | 41,675 (in 83 / out 42k) | 13m | 26m | 1 | 37 (1) | 0.2 | 0 |
| ELITEA-2411 | blocked | n/a | $2.01 | 0 (incl. cache) | 0m | 13m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $62.11 | 8.4 | 346,697 (in 1k / out 346k) | 98.0% | 88m | 518 (14) |
| test-automation-engineer | $43.11 | 9.6 | 324,865 (in 718 / out 324k) | 95.2% | 133m | 293 (9) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |

Unattributed (no dispatch named them in any captured session): ELITEA-2417, ELITEA-2411

---

# Batch cost — settings-w12

Generated: 2026-09-14T11:44:34.996Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5

_1 session(s) also served other batches — their session-level figures are split evenly; 187 other-batch dispatch(es) excluded._

## What happened

- Cases: 4  ·  **delivered: 2**  ·  automated 2  ·  already-covered 1  ·  blocked 1
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-30T01:46:10.169Z (6 run record(s))
- Findings reported: 54  ·  fix rounds: 0

## What it cost

- Total: $41.99  ·  3.0h active (cases 46m · lead 110m · stages 22m)  ·  9 dispatches
- Tokens: total 57,700,439  ·  **real work 257,506** (in 678 / out 256,828)  ·  cache 55.8M read / 1.6M write  ·  **cache hit rate 97.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 45 turns  ·  293 tool calls (13 err, 96% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $20.03 (48%)
  - by stage: lead $13.55 · triage $0.23 (1m) · gate $1.75 (8m) · report $0.30 (4m) · other $4.20 (9m)
- **Per delivered case (incl. overhead): $21.00**
- Avg direct per case (excl. overhead): $7.32
- Direct cost spread: avg $7.32 · median $6.87 · min $3.38 · max $11.71
- Loaded cost spread (direct + even overhead share): avg $10.50 · median $10.14 · min $5.01 · max $16.72
- Active-time spread: avg 15m · median 14m · min 6m · max 26m  ·  loaded: avg 45m · median 43m · min 33m · max 59m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2245 | automated | $11.71 | $16.72 | 95,843 (in 184 / out 96k) | 26m | 59m | 2.5 | 97 (4) | 0 | 22 |
| ELITEA-2246 | already-covered | n/a | $5.01 | 0 (incl. cache) | 0m | 33m | 0 | 0 (0) | 0 | 5 |
| ELITEA-2247 | automated | $6.87 | $11.88 | 47,542 (in 122 / out 47k) | 14m | 47m | 1.5 | 54 (3) | 0 | 22 |
| ELITEA-2248 | blocked | $3.38 | $8.39 | 24,800 (in 54 / out 25k) | 6m | 39m | 1 | 35 (2) | 0 | 5 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| test-automation-engineer | $15.04 | 4.6 | 109,273 (in 324 / out 109k) | 96.7% | 39m | 122 (9) |
| test-automation-lead | $13.55 | 0 | 28,845 (in 89 / out 29k) | 98.9% | 110m | 44 (1) |
| qa-engineer | $13.40 | 4.4 | 119,388 (in 265 / out 119k) | 95.1% | 29m | 127 (3) |

Unattributed (no dispatch named them in any captured session): ELITEA-2246

---

# Batch cost — skills-buildwithai-fidelity-rework

Generated: 2026-09-14T11:44:34.997Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 8  ·  **delivered: 8**  ·  automated 8
- Gate: green (3 runs)
- Findings reported: 9  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1989 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 3 |
| ELITEA-1990 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-1991 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 2 |
| ELITEA-1993 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-1994 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |
| ELITEA-1995 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1996 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1998 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 1 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-1989, ELITEA-1990, ELITEA-1991, ELITEA-1993, ELITEA-1994, ELITEA-1995, ELITEA-1996, ELITEA-1998

---

# Batch cost — skills-remaining-w1

Generated: 2026-09-14T11:44:34.999Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 8  ·  **delivered: 0**  ·  merged-ungated 7  ·  blocked 1
- Gate: incomplete
- Findings reported: 100  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2428 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2429 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 8 |
| ELITEA-2430 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2431 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2432 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 7 |
| ELITEA-2433 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2434 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 17 |
| ELITEA-2436 | merged-ungated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 15 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2428, ELITEA-2429, ELITEA-2430, ELITEA-2431, ELITEA-2432, ELITEA-2433, ELITEA-2434, ELITEA-2436

---

# Batch cost — skills-remaining-w2

Generated: 2026-09-14T11:44:35.000Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 8  ·  **delivered: 0**  ·  blocked 8
- Gate: red (1 runs)
- Findings reported: 67  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2439 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 7 |
| ELITEA-2441 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |
| ELITEA-2442 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 2 |
| ELITEA-2602 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2603 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2604 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 4 |
| ELITEA-2605 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2606 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 7 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2439, ELITEA-2441, ELITEA-2442, ELITEA-2602, ELITEA-2603, ELITEA-2604, ELITEA-2605, ELITEA-2606

---

# Batch cost — skills-remaining-w3

Generated: 2026-09-14T11:44:35.001Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 8  ·  **delivered: 0**  ·  blocked 8
- Gate: red (1 runs)
- Findings reported: 112  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2595 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2596 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2597 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 21 |
| ELITEA-2598 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2599 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 19 |
| ELITEA-2600 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 9 |
| ELITEA-2601 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 16 |
| ELITEA-2614 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 11 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2595, ELITEA-2596, ELITEA-2597, ELITEA-2598, ELITEA-2599, ELITEA-2600, ELITEA-2601, ELITEA-2614

---

# Batch cost — skills-remaining-w4

Generated: 2026-09-14T11:44:35.003Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly._

## What happened

- Cases: 7  ·  **delivered: 5**  ·  automated 5  ·  blocked 2
- Gate: green (3 runs)
- Findings reported: 81  ·  fix rounds: 0

## What it cost

- Total: $19.35  ·  1.2h active (cases 16m · lead 35m · stages 20m)  ·  2.67 dispatches
- Tokens: total 24,171,034  ·  **real work 144,476** (in 298 / out 144,178)  ·  cache 23.4M read / 598k write  ·  **cache hit rate 97.5%**  ·  see batch-tokenomics for the full breakdown
- Activity: 25 turns  ·  162 tool calls (2 err, 99% ok)  ·  skills: memory, sync-base-branches
- Overhead (lead + triage + gate + report, shown once): $13.18 (68%)
  - by stage: lead $3.72 · other $9.46 (20m)
- **Per delivered case (incl. overhead): $3.87**
- Avg direct per case (excl. overhead): $6.18
- Direct cost spread: avg $6.18 · median $6.18 · min $6.18 · max $6.18
- Loaded cost spread (direct + even overhead share): avg $2.76 · median $1.88 · min $1.88 · max $8.06
- Active-time spread: avg 16m · median 16m · min 16m · max 16m  ·  loaded: avg 10m · median 8m · min 8m · max 24m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2607 | blocked | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2608 | blocked | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 3 |
| ELITEA-2609 | automated | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 12 |
| ELITEA-2610 | automated | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 14 |
| ELITEA-2611 | automated | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 13 |
| ELITEA-2612 | automated | $6.18 | $8.06 | 46,823 (in 104 / out 47k) | 16m | 24m | 1 | 60 (1) | 0 | 15 |
| ELITEA-2613 | automated | n/a | $1.88 | 0 (incl. cache) | 0m | 8m | 0 | 0 (0) | 0 | 12 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $10.64 | 2 | 84,525 (in 169 / out 84k) | 97.0% | 27m | 96 (1) |
| test-automation-engineer | $5.00 | 0.67 | 31,791 (in 79 / out 32k) | 98.0% | 10m | 42 (1) |
| test-automation-lead | $3.72 | 0 | 28,161 (in 51 / out 28k) | 98.2% | 35m | 25 (0) |

Unattributed (no dispatch named them in any captured session): ELITEA-2607, ELITEA-2608, ELITEA-2609, ELITEA-2610, ELITEA-2611, ELITEA-2613

---

# Batch cost — skills-remaining-w5

Generated: 2026-09-14T11:44:35.005Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 9  ·  **delivered: 0**  ·  blocked 6  ·  already-covered 3
- Gate: red (2 runs)
- Findings reported: 11  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-1986 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 5 |
| ELITEA-1987 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 2 |
| ELITEA-1992 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 4 |
| ELITEA-1994 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1995 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1996 | blocked | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1997 | already-covered | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-1998 | already-covered | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |
| ELITEA-2000 | already-covered | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 0 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-1986, ELITEA-1987, ELITEA-1992, ELITEA-1994, ELITEA-1995, ELITEA-1996, ELITEA-1997, ELITEA-1998, ELITEA-2000

---

# Batch cost — support-assistant-w01

Generated: 2026-09-14T11:44:35.012Z  ·  sessions: 1 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 25 other-batch dispatch(es) excluded._

## What happened

- Cases: 4  ·  **delivered: 4**  ·  automated 4
- Gate: green (3 runs)
- Gate record (script-authored): green at 2026-08-22T02:22:52.347Z (3 run record(s))
- Findings reported: 85  ·  fix rounds: 1

## What it cost

- Total: $63.95  ·  6.5h active (cases 119m · lead 228m · stages 40m)  ·  22 dispatches
- Tokens: total 72,874,278  ·  **real work 485,945** (in 1,368 / out 484,577)  ·  cache 68.9M read / 3.4M write  ·  **cache hit rate 95.2%**  ·  see batch-tokenomics for the full breakdown
- Activity: 75 turns  ·  583 tool calls (25 err, 96% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $18.47 (29%)
  - by stage: lead $9.89 · triage $5.42 (14m) · gate $2.84 (21m) · report $0.31 (5m)
- Rework (fix rounds — already inside per-case direct): $3.52  ·  1 dispatch(es)  ·  10m
- **Per delivered case (incl. overhead): $15.99**
- Avg direct per case (excl. overhead): $11.37
- Direct cost spread: avg $11.37 · median $9.87 · min $9.02 · max $16.72
- Loaded cost spread (direct + even overhead share): avg $15.99 · median $14.49 · min $13.64 · max $21.34
- Active-time spread: avg 30m · median 23m · min 21m · max 53m  ·  loaded: avg 97m · median 90m · min 88m · max 120m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2418 | automated | $10.33 | $14.95 | 80,033 (in 235 / out 80k) | 24m | 91m | 4 | 111 (6) | 0 | 19 |
| ELITEA-2419 | automated | $9.02 | $13.64 | 75,305 (in 189 / out 75k) | 21m | 88m | 4 | 85 (2) | 0 | 18 |
| ELITEA-2422 | automated | $9.40 | $14.02 | 71,073 (in 211 / out 71k) | 21m | 88m | 4 | 93 (2) | 0 | 16 |
| ELITEA-2423 | automated | $16.72 | $21.34 | 144,975 (in 315 / out 145k) | 53m | 120m | 6 | 141 (7) | 1 | 32 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $29.90 | 11 | 247,648 (in 559 / out 247k) | 94.4% | 70m | 283 (9) |
| test-automation-engineer | $24.16 | 11 | 190,871 (in 661 / out 190k) | 94.2% | 89m | 226 (13) |
| test-automation-lead | $9.89 | 0 | 47,426 (in 148 / out 47k) | 99.0% | 228m | 74 (3) |

---

# Batch cost — support-assistant-w02

Generated: 2026-09-14T11:44:35.019Z  ·  sessions: 2 (claude)  ·  sources: ccusage-metered  ·  models: <synthetic>, claude-haiku-4-5-20251001, claude-opus-5

_1 session(s) also served other batches — their session-level figures are split evenly; 22 other-batch dispatch(es) excluded._

## What happened

- Cases: 6  ·  **delivered: 6**  ·  automated 4  ·  merged-sanctioned-red 2
- Gate: green (3 runs)
- Gate record (script-authored): red at 2026-08-22T06:13:54.036Z (3 run record(s))
- ⚠️ **GATE DRIFT**: receipt says `green` but the recorded verdict is `red` — write the verdict back into report.json
- Findings reported: 129  ·  fix rounds: 1

## What it cost

- Total: $95.15  ·  8.3h active (cases 173m · lead 266m · stages 60m)  ·  28 dispatches
- Tokens: total 106,341,392  ·  **real work 753,804** (in 1,801 / out 752,003)  ·  cache 100.8M read / 4.8M write  ·  **cache hit rate 95.4%**  ·  see batch-tokenomics for the full breakdown
- Activity: 116 turns  ·  848 tool calls (26 err, 97% ok)  ·  skills: memory, sync-base-branches, test-automation-workflow
- Overhead (lead + triage + gate + report, shown once): $25.40 (27%)
  - by stage: lead $15.09 · triage $0.20 (1m) · gate $4.81 (38m) · report $0.39 (6m) · other $4.92 (15m)
- Rework (fix rounds — already inside per-case direct): $2.41  ·  1 dispatch(es)  ·  5m
- **Per delivered case (incl. overhead): $15.86**
- Avg direct per case (excl. overhead): $11.63
- Direct cost spread: avg $11.63 · median $10.13 · min $8.24 · max $22.01
- Loaded cost spread (direct + even overhead share): avg $15.85 · median $14.36 · min $12.47 · max $26.24
- Active-time spread: avg 29m · median 25m · min 23m · max 51m  ·  loaded: avg 83m · median 79m · min 77m · max 105m

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2421 | merged-sanctioned-red | $22.01 | $26.24 | 173,804 (in 397 / out 173k) | 51m | 105m | 7 | 217 (3) | 1 | 35 |
| ELITEA-2420 | automated | $10.57 | $14.80 | 97,214 (in 207 / out 97k) | 25m | 79m | 4 | 95 (5) | 0 | 16 |
| ELITEA-2424 | automated | $8.24 | $12.47 | 61,965 (in 148 / out 62k) | 24m | 78m | 2 | 73 (5) | 0 | 21 |
| ELITEA-2425 | automated | $8.24 | $12.47 | 61,965 (in 148 / out 62k) | 24m | 78m | 2 | 73 (5) | 0 | 21 |
| ELITEA-2427 | merged-sanctioned-red | $9.68 | $13.91 | 85,525 (in 191 / out 85k) | 23m | 77m | 4 | 87 (2) | 0 | 16 |
| ELITEA-2426 | automated | $11.01 | $15.24 | 92,791 (in 221 / out 93k) | 26m | 80m | 4 | 105 (2) | 0 | 20 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

## By role

| role | cost | dispatches | real-work tok | cache hit | active | tools (err) |
|---|---|---|---|---|---|---|
| qa-engineer | $41.67 | 14 | 372,775 (in 695 / out 372k) | 95.0% | 105m | 394 (9) |
| test-automation-engineer | $38.39 | 14 | 295,765 (in 876 / out 295k) | 94.4% | 128m | 340 (14) |
| test-automation-lead | $15.09 | 0 | 85,264 (in 230 / out 85k) | 98.6% | 266m | 114 (3) |

---

# Batch cost — target-summary-tokens-range-2378

Generated: 2026-09-14T11:44:35.020Z  ·  sessions: 0 (none)  ·  sources: tokens only  ·  models: —

## What happened

- Cases: 1  ·  **delivered: 1**  ·  automated 1
- Gate: green (3 runs)
- Findings reported: 10  ·  fix rounds: 0

## What it cost

- Total: n/a  ·  0.0h active (cases 0m · lead 0m · stages 0m)  ·  0 dispatches
- Tokens: total 0  ·  **real work 0** (in 0 / out 0)  ·  cache 0 read / 0 write  ·  **cache hit rate n/a**  ·  see batch-tokenomics for the full breakdown
- Activity: 0 turns  ·  0 tool calls (0 err)
- Overhead (lead + triage + gate + report, shown once): n/a

## Per case (direct = measured; loaded = direct + even overhead share, an allocation)

| case | outcome | direct cost | loaded | real-work tok | active | loaded act. | dispatches | tools (err) | fix rounds | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITEA-2378 | automated | n/a | n/a | 0 (incl. cache) | 0m | 0m | 0 | 0 (0) | 0 | 10 |

_Cases analysed/built as one cluster share its measured dispatches — their rows are an even split, not per-case measurement (fractional `dispatches` marks them)._

Unattributed (no dispatch named them in any captured session): ELITEA-2378
