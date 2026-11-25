# Batch tokenomics — elitea-4863-chat-starters-limit

Generated: 2026-11-25T11:48:42.196Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 106,531 | 0.7% | fresh prompt tokens, full price |
| real work: output | 57,691 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,966,752 | 13.6% | context stored for reuse (~1.25× input price) |
| cache read | 12,358,513 | 85.3% | context replayed from cache (~0.1× input price) |
| **total** | **14,489,487** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 106,531 | 57,691 | 2.0M | 12.4M | 14,489,487 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 14,489,487 tokens · $6.96 · 1.2h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.98 | 72,797 | 751k | 7.2M | 90.1% |
| qa-engineer | $2.18 | 67,028 | 607k | 3.5M | 84.3% |
| test-automation-lead | $1.80 | 24,397 | 609k | 1.7M | 72.5% |

## Orchestrator (lead thread) composition

Lead: $1.80 — overhead incl. stages is 49% of the batch · real work 24,397 · cache 1.7M read / 609k write · hit rate 72.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.30 | 9,240 | 108k | 99k | 45.8% |
| gate | $0.62 | 14,233 | 128k | 2.3M | 94.3% |
| report | $0.66 | 13,904 | 231k | 104k | 30.3% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4863 | $3.58 | 61,592 | 40,856 | 890k | 8.2M | 9,222,586 | 89.6% | 63.7% |
