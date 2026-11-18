# Batch tokenomics — pipelines-router-node-2033

Generated: 2026-11-18T16:56:26.609Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 40,371 | 0.5% | fresh prompt tokens, full price |
| real work: output | 36,322 | 0.5% | generated tokens — the most expensive kind |
| cache write | 802,975 | 10.0% | context stored for reuse (~1.25× input price) |
| cache read | 7,162,122 | 89.1% | context replayed from cache (~0.1× input price) |
| **total** | **8,041,790** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 40,371 | 36,322 | 803k | 7.2M | 8,041,790 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 8,041,790 tokens · $3.50 · 0.6h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.43 | 24,436 | 368k | 2.4M | 86.1% |
| qa-engineer | $1.37 | 35,401 | 289k | 3.1M | 90.9% |
| test-automation-engineer | $0.70 | 16,856 | 146k | 1.7M | 91.9% |

## Orchestrator (lead thread) composition

Lead: $1.43 — overhead incl. stages is 41% of the batch · real work 24,436 · cache 2.4M read / 368k write · hit rate 86.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2033 | $2.07 | 25,864 | 26,393 | 435k | 4.8M | 5,286,625 | 91.2% | 65.7% |
