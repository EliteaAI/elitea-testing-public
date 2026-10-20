# Batch tokenomics — chat-regenerate-2185

Generated: 2026-10-20T23:40:31.985Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 114,445 | 0.8% | fresh prompt tokens, full price |
| real work: output | 56,307 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,257,216 | 16.7% | context stored for reuse (~1.25× input price) |
| cache read | 11,070,119 | 82.0% | context replayed from cache (~0.1× input price) |
| **total** | **13,498,087** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 82.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~69.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~25.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 114,445 | 56,307 | 2.3M | 11.1M | 13,498,087 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 13,498,087 tokens · $8.30 · 2.1h active · 14 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.11 | 75,337 | 795k | 4.9M | 85.3% |
| qa-engineer | $2.61 | 69,650 | 629k | 4.6M | 87.3% |
| test-automation-lead | $2.58 | 25,765 | 834k | 1.5M | 64.4% |

## Orchestrator (lead thread) composition

Lead: $2.58 — overhead incl. stages is 49% of the batch · real work 25,765 · cache 1.5M read / 834k write · hit rate 64.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.32 | 9,080 | 105k | 96k | 45.7% |
| gate | $0.78 | 11,545 | 230k | 889k | 78.9% |
| report | $0.40 | 13,155 | 113k | 209k | 63.2% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2185 | $4.20 | 70,509 | 40,698 | 975k | 8.3M | 9,421,183 | 88.8% | 69.8% |
