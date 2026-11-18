# Batch tokenomics — elitea-4714

Generated: 2026-11-18T10:55:28.410Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 112,734 | 0.5% | fresh prompt tokens, full price |
| real work: output | 116,391 | 0.5% | generated tokens — the most expensive kind |
| cache write | 2,325,689 | 9.5% | context stored for reuse (~1.25× input price) |
| cache read | 21,803,154 | 89.5% | context replayed from cache (~0.1× input price) |
| **total** | **24,357,968** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~37.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 112,734 | 116,391 | 2.3M | 21.8M | 24,357,968 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 24,357,968 tokens · $10.35 · 2.6h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $4.54 | 125,985 | 930k | 11.1M | 91.7% |
| test-automation-lead | $3.49 | 33,399 | 983k | 4.8M | 82.8% |
| qa-engineer | $2.31 | 69,741 | 413k | 5.9M | 93.1% |

## Orchestrator (lead thread) composition

Lead: $3.49 — overhead incl. stages is 34% of the batch · real work 33,399 · cache 4.8M read / 983k write · hit rate 82.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4714 | $6.86 | 97,903 | 97,823 | 1.3M | 17.0M | 18,549,450 | 92.2% | 76.2% |
