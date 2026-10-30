# Batch tokenomics — chat-stop-button-2182

Generated: 2026-10-20T21:29:23.070Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 143,593 | 0.7% | fresh prompt tokens, full price |
| real work: output | 96,162 | 0.5% | generated tokens — the most expensive kind |
| cache write | 2,429,120 | 12.2% | context stored for reuse (~1.25× input price) |
| cache read | 17,246,352 | 86.6% | context replayed from cache (~0.1× input price) |
| **total** | **19,915,227** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~75.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~32% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 143,593 | 96,162 | 2.4M | 17.2M | 19,915,227 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 19,915,227 tokens · $9.95 · 2.0h active · 17 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $3.90 | 113,111 | 822k | 8.5M | 90.6% |
| test-automation-engineer | $3.55 | 101,093 | 789k | 7.5M | 89.9% |
| test-automation-lead | $2.50 | 25,551 | 819k | 1.2M | 58.4% |

## Orchestrator (lead thread) composition

Lead: $2.50 — overhead incl. stages is 37% of the batch · real work 25,551 · cache 1.2M read / 819k write · hit rate 58.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.32 | 9,007 | 105k | 96k | 45.6% |
| gate | $0.46 | 11,157 | 114k | 884k | 87.8% |
| report | $0.40 | 13,098 | 113k | 209k | 63.2% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2182 | $6.26 | 99,664 | 81,278 | 1.3M | 14.9M | 16,341,584 | 91.5% | 82.1% |
