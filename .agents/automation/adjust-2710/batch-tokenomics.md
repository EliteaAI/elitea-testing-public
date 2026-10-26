# Batch tokenomics — adjust-2710

Generated: 2026-10-26T07:49:50.829Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,733 | 0.9% | fresh prompt tokens, full price |
| real work: output | 14,099 | 0.4% | generated tokens — the most expensive kind |
| cache write | 326,429 | 8.8% | context stored for reuse (~1.25× input price) |
| cache read | 3,346,610 | 90.0% | context replayed from cache (~0.1× input price) |
| **total** | **3,718,871** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~39.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,733 | 14,099 | 326k | 3.3M | 3,718,871 |
**Total: 3,718,871 tokens · $1.49 · 0.1h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $0.64 | 15,969 | 147k | 1.3M | 89.5% |
| test-automation-lead | $0.54 | 17,119 | 95k | 1.7M | 94.0% |
| qa-engineer | $0.32 | 12,744 | 84k | 352k | 78.7% |

## Orchestrator (lead thread) composition

Lead: $0.54 — overhead incl. stages is 36% of the batch · real work 17,119 · cache 1.7M read / 95k write · hit rate 94.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2058 | $0.95 | 21,001 | 7,712 | 232k | 1.7M | 1,953,572 | 87.0% | 52.5% |
