# Batch tokenomics — chat-bg-4953

Generated: 2026-11-27T11:22:02.447Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 65,686 | 0.3% | fresh prompt tokens, full price |
| real work: output | 121,912 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,640,097 | 6.6% | context stored for reuse (~1.25× input price) |
| cache read | 23,085,268 | 92.7% | context replayed from cache (~0.1× input price) |
| **total** | **24,912,963** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 65,686 | 121,912 | 1.6M | 23.1M | 24,912,963 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 24,912,963 tokens · $7.78 · 1.6h active · 7 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $2.89 | 31,997 | 908k | 4.0M | 81.3% |
| test-automation-engineer | $2.71 | 79,967 | 365k | 11.6M | 96.8% |
| qa-engineer | $2.18 | 75,634 | 367k | 7.5M | 95.0% |

## Orchestrator (lead thread) composition

Lead: $2.89 — overhead incl. stages is 37% of the batch · real work 31,997 · cache 4.0M read / 908k write · hit rate 81.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4953 | $4.89 | 49,906 | 105,695 | 732k | 19.1M | 19,958,474 | 96.1% | 80.1% |
