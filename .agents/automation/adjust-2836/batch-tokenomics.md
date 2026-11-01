# Batch tokenomics — adjust-2836

Generated: 2026-11-01T04:28:02.685Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 43,614 | 0.6% | fresh prompt tokens, full price |
| real work: output | 29,925 | 0.4% | generated tokens — the most expensive kind |
| cache write | 450,322 | 6.6% | context stored for reuse (~1.25× input price) |
| cache read | 6,305,638 | 92.3% | context replayed from cache (~0.1× input price) |
| **total** | **6,829,499** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 43,614 | 29,925 | 450k | 6.3M | 6,829,499 |
**Total: 6,829,499 tokens · $2.36 · 0.4h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.07 | 32,406 | 124k | 4.4M | 97.0% |
| qa-engineer | $0.88 | 28,643 | 216k | 1.4M | 85.6% |
| test-automation-engineer | $0.41 | 12,490 | 110k | 524k | 81.3% |

## Orchestrator (lead thread) composition

Lead: $1.07 — overhead incl. stages is 45% of the batch · real work 32,406 · cache 4.4M read / 124k write · hit rate 97.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2005 | $1.29 | 31,400 | 9,733 | 326k | 1.9M | 2,307,172 | 84.4% | 33.8% |
