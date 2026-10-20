# Batch tokenomics — chat-new-conv-2455

Generated: 2026-10-20T15:41:34.629Z  ·  sessions: 3  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-opus-5-5, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 446,090 | 0.3% | fresh prompt tokens, full price |
| real work: output | 549,077 | 0.4% | generated tokens — the most expensive kind |
| cache write | 11,010,489 | 7.2% | context stored for reuse (~1.25× input price) |
| cache read | 141,171,362 | 92.2% | context replayed from cache (~0.1× input price) |
| **total** | **153,177,018** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 369,117 | 361,511 | 9.1M | 75.5M | 85,363,225 |
| 1_eu.anthropic.claude-sonnet-5 | 65,528 | 161,003 | 1.2M | 59.5M | 60,924,553 |
| 1_eu.anthropic.claude-opus-5-5 | 11,423 | 24,495 | 531k | 6.1M | 6,621,133 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 22 | 2,068 | 108k | 158k | 268,107 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 153,177,018 tokens · $61.65 · 9.9h active · 42 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $30.31 | 587,966 | 3.4M | 100.6M | 96.5% |
| test-automation-lead | $17.75 | 119,259 | 5.1M | 18.7M | 78.4% |
| qa-engineer | $8.75 | 252,024 | 2.0M | 15.8M | 88.1% |
| session | $4.84 | 35,918 | 531k | 6.1M | 91.8% |

## Orchestrator (lead thread) composition

Lead: $22.59 — overhead incl. stages is 57% of the batch · real work 155,177 · cache 24.7M read / 5.6M write · hit rate 81.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.52 | 11,382 | 214k | 359k | 61.7% |
| gate | $2.10 | 36,712 | 574k | 3.1M | 83.9% |
| report | $0.98 | 35,697 | 244k | 562k | 68.3% |
| other | $8.83 | 242,730 | 1.7M | 23.6M | 92.7% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2455 | $26.63 | 187,440 | 326,029 | 2.6M | 88.8M | 91,924,020 | 96.9% | 60.0% |
