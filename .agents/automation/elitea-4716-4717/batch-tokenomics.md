# Batch tokenomics — elitea-4716-4717

Generated: 2026-11-18T12:49:20.961Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 83,158 | 0.3% | fresh prompt tokens, full price |
| real work: output | 142,784 | 0.6% | generated tokens — the most expensive kind |
| cache write | 1,723,361 | 7.2% | context stored for reuse (~1.25× input price) |
| cache read | 21,908,157 | 91.8% | context replayed from cache (~0.1× input price) |
| **total** | **23,857,460** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 83,158 | 142,784 | 1.7M | 21.9M | 23,857,460 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 23,857,460 tokens · $8.93 · 1.9h active · 9 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.14 | 92,271 | 432k | 10.7M | 95.9% |
| qa-engineer | $3.11 | 101,820 | 520k | 8.2M | 93.6% |
| test-automation-lead | $2.68 | 31,851 | 771k | 3.1M | 79.6% |

## Orchestrator (lead thread) composition

Lead: $2.68 — overhead incl. stages is 30% of the batch · real work 31,851 · cache 3.1M read / 771k write · hit rate 79.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4716 | $3.12 | 33,016 | 64,030 | 476k | 9.4M | 9,994,023 | 94.9% | 41.9% |
| ELITEA-4717 | $3.12 | 33,016 | 64,030 | 476k | 9.4M | 9,994,023 | 94.9% | 41.9% |
