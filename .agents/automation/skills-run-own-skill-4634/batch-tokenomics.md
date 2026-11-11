# Batch tokenomics — skills-run-own-skill-4634

Generated: 2026-11-11T17:05:43.029Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 105,787 | 0.6% | fresh prompt tokens, full price |
| real work: output | 79,350 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,926,833 | 10.7% | context stored for reuse (~1.25× input price) |
| cache read | 15,820,268 | 88.2% | context replayed from cache (~0.1× input price) |
| **total** | **17,932,238** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~35.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 105,787 | 79,350 | 1.9M | 15.8M | 17,932,238 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 17,932,238 tokens · $8.17 · 1.4h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $3.40 | 93,855 | 772k | 6.6M | 88.8% |
| test-automation-engineer | $2.57 | 64,321 | 502k | 7.1M | 93.0% |
| test-automation-lead | $2.19 | 26,961 | 653k | 2.1M | 75.9% |

## Orchestrator (lead thread) composition

Lead: $2.19 — overhead incl. stages is 36% of the batch · real work 26,961 · cache 2.1M read / 653k write · hit rate 75.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,064 | 108k | 98k | 45.6% |
| report | $0.41 | 12,122 | 115k | 330k | 72.7% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4634 | $5.23 | 70,642 | 66,348 | 1.0M | 13.3M | 14,463,856 | 92.2% | 80.7% |
