# Batch tokenomics — chat-send-button-2505

Generated: 2026-10-22T11:32:31.237Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 113,389 | 0.4% | fresh prompt tokens, full price |
| real work: output | 91,364 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,788,538 | 10.8% | context stored for reuse (~1.25× input price) |
| cache read | 22,864,544 | 88.4% | context replayed from cache (~0.1× input price) |
| **total** | **25,857,835** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 103,180 | 79,381 | 2.4M | 20.1M | 22,636,802 |
| 1_eu.anthropic.claude-sonnet-5 | 10,187 | 9,915 | 280k | 2.7M | 2,952,925 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 22 | 2,068 | 108k | 158k | 268,107 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 25,857,835 tokens · $11.59 · 2.3h active · 11.67 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $5.68 | 50,558 | 1.6M | 7.2M | 82.1% |
| test-automation-engineer | $3.50 | 87,468 | 631k | 11.4M | 94.3% |
| qa-engineer | $2.41 | 66,729 | 607k | 4.2M | 86.9% |

## Orchestrator (lead thread) composition

Lead: $5.68 — overhead incl. stages is 54% of the batch · real work 50,558 · cache 7.2M read / 1.6M write · hit rate 82.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.18 | 2,090 | 108k | 158k | 59.3% |
| gate | $0.44 | 8,354 | 115k | 785k | 86.7% |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2466 | $5.29 | 79,372 | 64,381 | 1.0M | 14.7M | 15,840,060 | 93.1% | 61.3% |
