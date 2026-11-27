# Batch tokenomics — chat-ask-4955-adj

Generated: 2026-11-27T17:50:26.680Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 98,211 | 0.5% | fresh prompt tokens, full price |
| real work: output | 85,241 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,017,761 | 9.7% | context stored for reuse (~1.25× input price) |
| cache read | 18,672,766 | 89.5% | context replayed from cache (~0.1× input price) |
| **total** | **20,873,979** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~38% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 98,211 | 85,241 | 2.0M | 18.7M | 20,873,979 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 20,873,979 tokens · $7.99 · 0.9h active · 9 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.42 | 95,208 | 697k | 10.8M | 93.6% |
| test-automation-lead | $3.12 | 38,044 | 901k | 5.8M | 86.4% |
| qa-engineer | $1.45 | 50,200 | 419k | 2.0M | 81.4% |

## Orchestrator (lead thread) composition

Lead: $3.12 — overhead incl. stages is 48% of the batch · real work 38,044 · cache 5.8M read / 901k write · hit rate 86.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.32 | 9,338 | 109k | 208k | 63.8% |
| report | $0.39 | 13,347 | 117k | 332k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4955 | $4.16 | 65,274 | 57,449 | 891k | 12.3M | 13,316,619 | 92.8% | 63.8% |
