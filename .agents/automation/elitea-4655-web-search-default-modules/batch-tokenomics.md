# Batch tokenomics — elitea-4655-web-search-default-modules

Generated: 2026-11-11T20:42:54.851Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 139,586 | 0.6% | fresh prompt tokens, full price |
| real work: output | 99,455 | 0.4% | generated tokens — the most expensive kind |
| cache write | 3,030,290 | 12.9% | context stored for reuse (~1.25× input price) |
| cache read | 20,291,220 | 86.1% | context replayed from cache (~0.1× input price) |
| **total** | **23,560,551** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 86.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~74.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~31.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 139,586 | 99,455 | 3.0M | 20.3M | 23,560,551 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 23,560,551 tokens · $11.99 · 2.7h active · 17 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $5.00 | 110,145 | 1.1M | 11.4M | 90.7% |
| qa-engineer | $3.73 | 102,197 | 851k | 7.3M | 88.8% |
| test-automation-lead | $3.26 | 26,699 | 1.1M | 1.6M | 59.7% |

## Orchestrator (lead thread) composition

Lead: $3.26 — overhead incl. stages is 38% of the batch · real work 26,699 · cache 1.6M read / 1.1M write · hit rate 59.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,035 | 107k | 98k | 45.9% |
| gate | $0.52 | 12,046 | 119k | 1.3M | 90.8% |
| report | $0.42 | 13,110 | 117k | 217k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4655 | $7.47 | 94,407 | 83,744 | 1.6M | 17.1M | 18,901,399 | 90.9% | 80.2% |
