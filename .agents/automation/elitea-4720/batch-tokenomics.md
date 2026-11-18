# Batch tokenomics — elitea-4720

Generated: 2026-11-18T15:21:04.079Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 104,588 | 0.6% | fresh prompt tokens, full price |
| real work: output | 110,115 | 0.6% | generated tokens — the most expensive kind |
| cache write | 1,978,390 | 10.5% | context stored for reuse (~1.25× input price) |
| cache read | 16,608,293 | 88.3% | context replayed from cache (~0.1× input price) |
| **total** | **18,801,386** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~34.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 104,588 | 110,115 | 2.0M | 16.6M | 18,801,386 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 18,801,386 tokens · $8.73 · 1.3h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.38 | 85,212 | 686k | 8.4M | 92.0% |
| qa-engineer | $3.30 | 104,432 | 658k | 6.6M | 90.4% |
| test-automation-lead | $2.05 | 25,059 | 634k | 1.6M | 70.9% |

## Orchestrator (lead thread) composition

Lead: $2.05 — overhead incl. stages is 37% of the batch · real work 25,059 · cache 1.6M read / 634k write · hit rate 70.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.34 | 9,360 | 109k | 98k | 45.6% |
| gate | $0.44 | 10,795 | 117k | 677k | 84.4% |
| report | $0.42 | 12,404 | 115k | 331k | 72.7% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4720 | $5.49 | 60,251 | 96,834 | 1.0M | 13.9M | 15,071,762 | 92.9% | 80.2% |
