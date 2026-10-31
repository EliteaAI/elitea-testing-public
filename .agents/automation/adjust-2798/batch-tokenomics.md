# Batch tokenomics — adjust-2798

Generated: 2026-10-31T04:34:00.317Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,095 | 0.4% | fresh prompt tokens, full price |
| real work: output | 36,651 | 0.4% | generated tokens — the most expensive kind |
| cache write | 370,523 | 4.1% | context stored for reuse (~1.25× input price) |
| cache read | 8,679,257 | 95.2% | context replayed from cache (~0.1× input price) |
| **total** | **9,118,526** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~56.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,095 | 36,651 | 371k | 8.7M | 9,118,526 |
**Total: 9,118,526 tokens · $2.45 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.55 | 39,388 | 146k | 7.4M | 97.9% |
| test-automation-engineer | $0.48 | 14,283 | 126k | 581k | 81.0% |
| qa-engineer | $0.43 | 15,075 | 98k | 742k | 87.2% |

## Orchestrator (lead thread) composition

Lead: $1.55 — overhead incl. stages is 63% of the batch · real work 39,388 · cache 7.4M read / 146k write · hit rate 97.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2034 | $0.90 | 20,846 | 8,512 | 224k | 1.3M | 1,577,076 | 84.4% | 17.3% |
