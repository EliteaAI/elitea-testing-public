# Batch tokenomics — adjust-2743

Generated: 2026-10-27T08:06:42.856Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,601 | 0.5% | fresh prompt tokens, full price |
| real work: output | 20,126 | 0.5% | generated tokens — the most expensive kind |
| cache write | 219,677 | 5.2% | context stored for reuse (~1.25× input price) |
| cache read | 3,938,294 | 93.8% | context replayed from cache (~0.1× input price) |
| **total** | **4,199,698** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~49.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,601 | 20,126 | 220k | 3.9M | 4,199,698 |
**Total: 4,199,698 tokens · $1.31 · 0.4h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.92 | 28,795 | 106k | 3.7M | 97.0% |
| qa-engineer | $0.39 | 12,932 | 114k | 208k | 62.6% |

## Orchestrator (lead thread) composition

Lead: $0.92 — overhead incl. stages is 70% of the batch · real work 28,795 · cache 3.7M read / 106k write · hit rate 97.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2360 | $0.39 | 10,491 | 2,441 | 114k | 208k | 335,180 | 62.6% | 8.0% |
