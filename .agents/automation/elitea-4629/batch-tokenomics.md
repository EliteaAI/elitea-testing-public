# Batch tokenomics — elitea-4629

Generated: 2026-11-11T10:43:52.839Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 105,850 | 0.7% | fresh prompt tokens, full price |
| real work: output | 75,618 | 0.5% | generated tokens — the most expensive kind |
| cache write | 2,243,094 | 14.4% | context stored for reuse (~1.25× input price) |
| cache read | 13,141,957 | 84.4% | context replayed from cache (~0.1× input price) |
| **total** | **15,566,519** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 105,850 | 75,618 | 2.2M | 13.1M | 15,566,519 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 15,566,519 tokens · $8.68 · 2.1h active · 15 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $3.28 | 93,784 | 790k | 4.9M | 85.4% |
| test-automation-engineer | $2.80 | 61,656 | 606k | 6.9M | 91.5% |
| test-automation-lead | $2.60 | 26,028 | 847k | 1.3M | 60.7% |

## Orchestrator (lead thread) composition

Lead: $2.60 — overhead incl. stages is 30% of the batch · real work 26,028 · cache 1.3M read / 847k write · hit rate 60.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4629 | $6.08 | 87,361 | 68,079 | 1.4M | 11.8M | 13,356,289 | 88.8% | 85.8% |
