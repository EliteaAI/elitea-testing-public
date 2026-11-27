# Batch tokenomics — chat-bg-4957-adj

Generated: 2026-11-27T18:16:58.957Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 63,090 | 0.4% | fresh prompt tokens, full price |
| real work: output | 65,158 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,699,771 | 10.8% | context stored for reuse (~1.25× input price) |
| cache read | 13,917,336 | 88.4% | context replayed from cache (~0.1× input price) |
| **total** | **15,745,355** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~35.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 63,090 | 65,158 | 1.7M | 13.9M | 15,745,355 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 15,745,355 tokens · $6.42 · 1.8h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $3.21 | 30,656 | 1.0M | 4.2M | 80.0% |
| qa-engineer | $1.92 | 60,073 | 376k | 6.0M | 93.7% |
| test-automation-engineer | $1.29 | 37,519 | 283k | 3.7M | 92.4% |

## Orchestrator (lead thread) composition

Lead: $3.21 — overhead incl. stages is 50% of the batch · real work 30,656 · cache 4.2M read / 1.0M write · hit rate 80.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4957 | $3.21 | 47,866 | 49,726 | 659k | 9.7M | 10,457,554 | 93.2% | 66.4% |
