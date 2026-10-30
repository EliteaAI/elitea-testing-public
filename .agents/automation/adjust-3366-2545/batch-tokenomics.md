# Batch tokenomics — adjust-3366-2545

Generated: 2026-10-21T13:43:54.846Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 60,040 | 1.0% | fresh prompt tokens, full price |
| real work: output | 21,948 | 0.4% | generated tokens — the most expensive kind |
| cache write | 399,115 | 6.8% | context stored for reuse (~1.25× input price) |
| cache read | 5,391,128 | 91.8% | context replayed from cache (~0.1× input price) |
| **total** | **5,872,231** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 60,040 | 21,948 | 399k | 5.4M | 5,872,231 |
**Total: 5,872,231 tokens · $2.06 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.92 | 24,972 | 146k | 3.3M | 95.4% |
| test-automation-engineer | $0.73 | 42,355 | 154k | 1.5M | 88.8% |
| qa-engineer | $0.41 | 14,661 | 100k | 610k | 84.7% |

## Orchestrator (lead thread) composition

Lead: $0.92 — overhead incl. stages is 45% of the batch · real work 24,972 · cache 3.3M read / 146k write · hit rate 95.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3366 | $1.14 | 46,891 | 10,125 | 253k | 2.1M | 2,429,033 | 87.6% | 41.4% |
