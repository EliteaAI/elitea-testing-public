# Batch tokenomics — fix-2641

Generated: 2026-10-23T12:41:44.210Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,864 | 0.6% | fresh prompt tokens, full price |
| real work: output | 25,713 | 0.5% | generated tokens — the most expensive kind |
| cache write | 366,280 | 6.6% | context stored for reuse (~1.25× input price) |
| cache read | 5,163,482 | 92.4% | context replayed from cache (~0.1× input price) |
| **total** | **5,587,339** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,864 | 25,713 | 366k | 5.2M | 5,587,339 |
**Total: 5,587,339 tokens · $1.93 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.95 | 25,114 | 141k | 3.4M | 95.8% |
| test-automation-engineer | $0.62 | 18,133 | 133k | 1.4M | 90.4% |
| qa-engineer | $0.36 | 14,330 | 92k | 362k | 77.9% |

## Orchestrator (lead thread) composition

Lead: $0.95 — overhead incl. stages is 49% of the batch · real work 25,114 · cache 3.4M read / 141k write · hit rate 95.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2356 | $0.67 | 15,671 | 7,726 | 159k | 1.0M | 1,221,678 | 85.6% | 21.9% |
| ELITEA-2357 | $0.31 | 5,182 | 3,885 | 66k | 678k | 753,105 | 90.4% | 13.5% |
