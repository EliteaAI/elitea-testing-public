# Batch tokenomics — adjust-2760

Generated: 2026-10-30T08:04:09.558Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,111 | 0.5% | fresh prompt tokens, full price |
| real work: output | 28,850 | 0.4% | generated tokens — the most expensive kind |
| cache write | 531,844 | 7.8% | context stored for reuse (~1.25× input price) |
| cache read | 6,206,907 | 91.3% | context replayed from cache (~0.1× input price) |
| **total** | **6,799,712** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,111 | 28,850 | 532k | 6.2M | 6,799,712 |
**Total: 6,799,712 tokens · $2.53 · 0.6h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.67 | 32,544 | 315k | 4.9M | 93.8% |
| test-automation-engineer | $0.50 | 14,422 | 121k | 926k | 87.6% |
| qa-engineer | $0.36 | 13,995 | 96k | 357k | 77.0% |

## Orchestrator (lead thread) composition

Lead: $1.67 — overhead incl. stages is 66% of the batch · real work 32,544 · cache 4.9M read / 315k write · hit rate 93.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2019 | $0.29 | 6,954 | 2,518 | 72k | 428k | 509,543 | 84.3% | 7.5% |
| ELITEA-2045 | $0.29 | 6,954 | 2,518 | 72k | 428k | 509,543 | 84.3% | 7.5% |
| ELITEA-2057 | $0.29 | 6,954 | 2,518 | 72k | 428k | 509,543 | 84.3% | 7.5% |
