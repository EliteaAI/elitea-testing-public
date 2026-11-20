# Batch tokenomics — update-2994

Generated: 2026-11-20T11:20:35.333Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 57,597 | 0.7% | fresh prompt tokens, full price |
| real work: output | 32,666 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,083,844 | 13.6% | context stored for reuse (~1.25× input price) |
| cache read | 6,773,113 | 85.2% | context replayed from cache (~0.1× input price) |
| **total** | **7,947,220** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 57,597 | 32,666 | 1.1M | 6.8M | 7,947,220 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 7,947,220 tokens · $4.23 · 0.8h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.63 | 20,673 | 484k | 1.6M | 76.8% |
| qa-engineer | $1.60 | 42,153 | 378k | 3.0M | 88.0% |
| test-automation-engineer | $1.00 | 27,437 | 222k | 2.2M | 90.1% |

## Orchestrator (lead thread) composition

Lead: $1.63 — overhead incl. stages is 39% of the batch · real work 20,673 · cache 1.6M read / 484k write · hit rate 76.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4755 | $2.60 | 42,992 | 26,598 | 599k | 5.1M | 5,792,511 | 88.9% | 72.9% |
