# Batch tokenomics — elitea-4718

Generated: 2026-11-18T13:56:34.791Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 122,428 | 0.5% | fresh prompt tokens, full price |
| real work: output | 130,800 | 0.6% | generated tokens — the most expensive kind |
| cache write | 2,406,664 | 10.5% | context stored for reuse (~1.25× input price) |
| cache read | 20,277,768 | 88.4% | context replayed from cache (~0.1× input price) |
| **total** | **22,937,660** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~34.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 122,428 | 130,800 | 2.4M | 20.3M | 22,937,660 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 22,937,660 tokens · $10.56 · 1.8h active · 15 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $4.15 | 116,725 | 825k | 9.6M | 91.6% |
| test-automation-engineer | $3.88 | 109,124 | 775k | 9.1M | 91.7% |
| test-automation-lead | $2.53 | 27,379 | 807k | 1.7M | 66.7% |

## Orchestrator (lead thread) composition

Lead: $2.53 — overhead incl. stages is 36% of the batch · real work 27,379 · cache 1.7M read / 807k write · hit rate 66.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.34 | 9,112 | 109k | 99k | 45.6% |
| gate | $0.49 | 11,630 | 117k | 1.0M | 89.0% |
| report | $0.43 | 14,491 | 118k | 217k | 63.1% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4718 | $6.77 | 77,403 | 113,213 | 1.3M | 17.3M | 18,730,032 | 92.8% | 81.7% |
