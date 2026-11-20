# Batch tokenomics — pipe-copy-4756

Generated: 2026-11-20T12:00:32.779Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 103,720 | 0.9% | fresh prompt tokens, full price |
| real work: output | 50,723 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,972,942 | 16.3% | context stored for reuse (~1.25× input price) |
| cache read | 9,946,221 | 82.4% | context replayed from cache (~0.1× input price) |
| **total** | **12,073,606** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 82.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~70.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~26% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 103,720 | 50,723 | 2.0M | 9.9M | 12,073,606 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,073,606 tokens · $7.33 · 1.1h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.71 | 68,430 | 633k | 5.4M | 88.9% |
| qa-engineer | $2.58 | 60,673 | 735k | 2.4M | 75.8% |
| test-automation-lead | $2.04 | 25,340 | 605k | 2.1M | 77.3% |

## Orchestrator (lead thread) composition

Lead: $2.04 — overhead incl. stages is 45% of the batch · real work 25,340 · cache 2.1M read / 605k write · hit rate 77.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.35 | 9,240 | 109k | 207k | 63.7% |
| gate | $0.51 | 11,934 | 118k | 1.1M | 90.0% |
| report | $0.40 | 12,489 | 116k | 216k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4756 | $4.03 | 60,134 | 35,306 | 1.0M | 6.3M | 7,381,053 | 85.2% | 61.1% |
