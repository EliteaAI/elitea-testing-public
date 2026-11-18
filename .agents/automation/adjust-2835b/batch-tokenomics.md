# Batch tokenomics — adjust-2835b

Generated: 2026-11-18T16:25:36.287Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 67,499 | 0.5% | fresh prompt tokens, full price |
| real work: output | 59,520 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,514,476 | 10.9% | context stored for reuse (~1.25× input price) |
| cache read | 12,264,724 | 88.2% | context replayed from cache (~0.1× input price) |
| **total** | **13,906,219** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~35.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 67,499 | 59,520 | 1.5M | 12.3M | 13,906,219 |
**Total: 13,906,219 tokens · $6.32 · 1.5h active · 5 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.70 | 43,472 | 743k | 3.3M | 81.3% |
| test-automation-lead | $2.58 | 39,760 | 518k | 7.6M | 93.5% |
| qa-engineer | $1.04 | 43,787 | 254k | 1.3M | 82.0% |

## Orchestrator (lead thread) composition

Lead: $2.58 — overhead incl. stages is 41% of the batch · real work 39,760 · cache 7.6M read / 518k write · hit rate 93.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2016 | $3.74 | 53,150 | 34,109 | 997k | 4.6M | 5,705,380 | 81.5% | 41.0% |
