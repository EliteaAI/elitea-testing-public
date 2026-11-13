# Batch tokenomics — adjust-elitea-2455

Generated: 2026-11-13T12:10:38.740Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 137,338 | 0.2% | fresh prompt tokens, full price |
| real work: output | 265,804 | 0.3% | generated tokens — the most expensive kind |
| cache write | 2,977,873 | 3.8% | context stored for reuse (~1.25× input price) |
| cache read | 75,412,291 | 95.7% | context replayed from cache (~0.1× input price) |
| **total** | **78,793,306** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 96.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~59.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5 | 42,607 | 138,694 | 595k | 53.5M | 54,280,470 |
| 1_eu.anthropic.claude-sonnet-5-5 | 94,709 | 125,042 | 2.3M | 21.8M | 24,244,729 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 22 | 2,068 | 108k | 158k | 268,107 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 78,793,306 tokens · $25.44 · 2.7h active · 12.5 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $19.70 | 320,051 | 1.4M | 68.5M | 97.9% |
| test-automation-lead | $4.32 | 39,427 | 1.2M | 5.3M | 81.5% |
| qa-engineer | $1.41 | 43,664 | 422k | 1.6M | 77.8% |

## Orchestrator (lead thread) composition

Lead: $4.32 — overhead incl. stages is 21% of the batch · real work 39,427 · cache 5.3M read / 1.2M write · hit rate 81.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.18 | 2,090 | 108k | 158k | 59.3% |
| gate | $0.33 | 6,265 | 86k | 589k | 86.7% |
| report | $0.54 | 20,665 | 128k | 350k | 72.0% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2455 | $20.06 | 103,429 | 231,266 | 1.5M | 69.0M | 70,795,151 | 97.8% | 89.8% |
