# Batch tokenomics — chat-regenerate-2184

Generated: 2026-10-20T22:31:38.380Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 71,646 | 0.8% | fresh prompt tokens, full price |
| real work: output | 37,130 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,337,045 | 14.8% | context stored for reuse (~1.25× input price) |
| cache read | 7,569,291 | 84.0% | context replayed from cache (~0.1× input price) |
| **total** | **9,015,112** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 71,646 | 37,130 | 1.3M | 7.6M | 9,015,112 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 9,015,112 tokens · $5.08 · 1.3h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.82 | 43,147 | 455k | 3.2M | 86.8% |
| test-automation-lead | $1.80 | 22,553 | 541k | 1.7M | 75.9% |
| qa-engineer | $1.46 | 43,076 | 341k | 2.6M | 87.7% |

## Orchestrator (lead thread) composition

Lead: $1.80 — overhead incl. stages is 35% of the batch · real work 22,553 · cache 1.7M read / 541k write · hit rate 75.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2184 | $3.27 | 57,263 | 28,960 | 796k | 5.8M | 6,706,480 | 87.2% | 74.4% |
