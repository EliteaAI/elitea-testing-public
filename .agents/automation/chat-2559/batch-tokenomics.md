# Batch tokenomics — chat-2559

Generated: 2026-10-22T21:43:07.521Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 159,703 | 0.7% | fresh prompt tokens, full price |
| real work: output | 96,346 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,780,054 | 11.8% | context stored for reuse (~1.25× input price) |
| cache read | 20,436,070 | 87.1% | context replayed from cache (~0.1× input price) |
| **total** | **23,472,173** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~75.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~33.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 159,703 | 96,346 | 2.8M | 20.4M | 23,472,173 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 23,472,173 tokens · $11.33 · 1.8h active · 19 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $5.65 | 143,760 | 1.3M | 11.7M | 89.3% |
| test-automation-lead | $2.92 | 35,569 | 879k | 2.7M | 74.9% |
| qa-engineer | $2.75 | 76,720 | 591k | 6.0M | 90.5% |

## Orchestrator (lead thread) composition

Lead: $2.92 — overhead incl. stages is 59% of the batch · real work 35,569 · cache 2.7M read / 879k write · hit rate 74.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.35 | 9,519 | 109k | 205k | 63.7% |
| gate | $0.44 | 10,495 | 117k | 673k | 84.3% |
| report | $0.46 | 14,500 | 118k | 451k | 78.1% |
| other | $2.55 | 62,056 | 599k | 5.4M | 89.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3775 | $3.79 | 59,619 | 42,547 | 821k | 8.5M | 9,416,690 | 90.6% | 40.1% |
| ELITEA-3786 | $0.82 | 8,616 | 13,130 | 137k | 2.5M | 2,666,598 | 94.5% | 11.4% |
