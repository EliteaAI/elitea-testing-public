# Batch tokenomics — schedule-ui-2981

Generated: 2026-11-18T17:53:24.844Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 58,892 | 0.3% | fresh prompt tokens, full price |
| real work: output | 118,335 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,410,616 | 6.4% | context stored for reuse (~1.25× input price) |
| cache read | 20,508,973 | 92.8% | context replayed from cache (~0.1× input price) |
| **total** | **22,096,816** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 58,892 | 118,335 | 1.4M | 20.5M | 22,096,816 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 22,096,816 tokens · $7.57 · 1.6h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $3.32 | 96,001 | 455k | 11.3M | 95.9% |
| test-automation-lead | $2.27 | 27,633 | 673k | 2.3M | 76.7% |
| test-automation-engineer | $1.98 | 53,593 | 282k | 7.0M | 95.9% |

## Orchestrator (lead thread) composition

Lead: $2.27 — overhead incl. stages is 30% of the batch · real work 27,633 · cache 2.3M read / 673k write · hit rate 76.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2007 | $2.65 | 21,580 | 53,218 | 369k | 9.1M | 9,565,491 | 95.9% | 43.3% |
| ELITEA-2008 | $2.65 | 21,580 | 53,218 | 369k | 9.1M | 9,565,491 | 95.9% | 43.3% |
