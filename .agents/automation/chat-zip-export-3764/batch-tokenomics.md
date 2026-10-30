# Batch tokenomics — chat-zip-export-3764

Generated: 2026-10-21T01:31:30.090Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 142,358 | 1.1% | fresh prompt tokens, full price |
| real work: output | 61,714 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,954,334 | 14.6% | context stored for reuse (~1.25× input price) |
| cache read | 11,272,659 | 83.9% | context replayed from cache (~0.1× input price) |
| **total** | **13,431,065** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 142,358 | 61,714 | 2.0M | 11.3M | 13,431,065 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 13,431,065 tokens · $7.63 · 1.1h active · 15 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.11 | 100,434 | 709k | 6.1M | 88.6% |
| qa-engineer | $2.86 | 79,083 | 729k | 4.1M | 84.1% |
| test-automation-lead | $1.67 | 24,555 | 516k | 1.1M | 66.6% |

## Orchestrator (lead thread) composition

Lead: $1.67 — overhead incl. stages is 39% of the batch · real work 24,555 · cache 1.1M read / 516k write · hit rate 66.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.34 | 9,283 | 106k | 201k | 63.8% |
| gate | $0.50 | 11,915 | 116k | 1.1M | 90.0% |
| report | $0.44 | 15,418 | 117k | 213k | 62.9% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3764 | $4.69 | 98,133 | 44,768 | 1.1M | 8.7M | 9,913,505 | 87.9% | 73.8% |
