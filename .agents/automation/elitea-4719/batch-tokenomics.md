# Batch tokenomics — elitea-4719

Generated: 2026-11-18T14:26:32.961Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 58,389 | 0.6% | fresh prompt tokens, full price |
| real work: output | 57,000 | 0.5% | generated tokens — the most expensive kind |
| cache write | 973,092 | 9.2% | context stored for reuse (~1.25× input price) |
| cache read | 9,462,692 | 89.7% | context replayed from cache (~0.1× input price) |
| **total** | **10,551,173** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~37.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 58,389 | 57,000 | 973k | 9.5M | 10,551,173 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 10,551,173 tokens · $4.50 · 0.7h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $1.99 | 54,822 | 422k | 4.1M | 90.2% |
| test-automation-engineer | $1.43 | 39,053 | 257k | 4.0M | 93.6% |
| test-automation-lead | $1.08 | 21,514 | 294k | 1.3M | 80.9% |

## Orchestrator (lead thread) composition

Lead: $1.08 — overhead incl. stages is 24% of the batch · real work 21,514 · cache 1.3M read / 294k write · hit rate 80.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4719 | $3.42 | 43,015 | 50,860 | 679k | 8.2M | 8,928,235 | 91.9% | 84.6% |
