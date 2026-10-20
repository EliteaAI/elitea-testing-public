# Batch tokenomics — skills-builder-chat

Generated: 2026-10-20T09:10:25.406Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 238,858 | 0.2% | fresh prompt tokens, full price |
| real work: output | 394,894 | 0.3% | generated tokens — the most expensive kind |
| cache write | 9,578,039 | 6.1% | context stored for reuse (~1.25× input price) |
| cache read | 146,226,608 | 93.5% | context replayed from cache (~0.1× input price) |
| **total** | **156,438,399** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~50.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5 | 89,529 | 230,283 | 3.3M | 109.0M | 112,542,794 |
| 1_eu.anthropic.claude-sonnet-5-5 | 149,265 | 161,262 | 6.2M | 36.6M | 43,118,549 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 64 | 3,349 | 93k | 681k | 777,056 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 156,438,399 tokens · $59.17 · 7.3h active · 19 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $26.10 | 305,274 | 1.7M | 93.1M | 98.1% |
| test-automation-lead | $19.84 | 67,820 | 6.2M | 14.3M | 69.7% |
| qa-engineer | $13.24 | 260,658 | 1.7M | 38.8M | 95.6% |

## Orchestrator (lead thread) composition

Lead: $19.84 — overhead incl. stages is 37% of the batch · real work 67,820 · cache 14.3M read / 6.2M write · hit rate 69.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.54 | 12,461 | 198k | 777k | 79.0% |
| gate | $0.76 | 11,543 | 228k | 781k | 76.7% |
| report | $0.48 | 18,053 | 122k | 217k | 62.5% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3366 | $32.33 | 125,601 | 273,634 | 1.7M | 117.7M | 119,801,010 | 98.5% | 76.6% |
| ELITEA-3367 | $2.44 | 17,170 | 27,793 | 536k | 5.7M | 6,278,965 | 91.2% | 4.0% |
| ELITEA-3316 | $2.77 | 46,553 | 33,124 | 568k | 6.8M | 7,412,455 | 91.7% | 4.7% |
