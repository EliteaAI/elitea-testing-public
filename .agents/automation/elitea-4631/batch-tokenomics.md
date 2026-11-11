# Batch tokenomics — elitea-4631

Generated: 2026-11-11T13:38:32.414Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 132,556 | 0.7% | fresh prompt tokens, full price |
| real work: output | 72,377 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,125,621 | 11.5% | context stored for reuse (~1.25× input price) |
| cache read | 16,201,551 | 87.4% | context replayed from cache (~0.1× input price) |
| **total** | **18,532,105** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~76.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~34% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 132,556 | 72,377 | 2.1M | 16.2M | 18,532,105 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 18,532,105 tokens · $8.72 · 1.2h active · 19 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.56 | 82,460 | 746k | 9.5M | 92.3% |
| qa-engineer | $3.38 | 92,979 | 853k | 4.9M | 84.3% |
| test-automation-lead | $1.78 | 29,494 | 527k | 1.8M | 76.5% |

## Orchestrator (lead thread) composition

Lead: $1.78 — overhead incl. stages is 35% of the batch · real work 29,494 · cache 1.8M read / 527k write · hit rate 76.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 8,938 | 107k | 97k | 45.6% |
| gate | $0.50 | 11,605 | 118k | 1.1M | 89.9% |
| report | $0.41 | 12,712 | 115k | 214k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4631 | $5.70 | 85,474 | 56,710 | 1.3M | 13.0M | 14,369,576 | 90.6% | 77.5% |
