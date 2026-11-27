# Batch tokenomics — adjust-4953

Generated: 2026-11-27T18:39:46.086Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 110,084 | 0.3% | fresh prompt tokens, full price |
| real work: output | 174,003 | 0.5% | generated tokens — the most expensive kind |
| cache write | 2,629,472 | 7.3% | context stored for reuse (~1.25× input price) |
| cache read | 32,972,341 | 91.9% | context replayed from cache (~0.1× input price) |
| **total** | **35,885,900** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~43.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 110,084 | 174,003 | 2.6M | 33.0M | 35,885,900 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 35,885,900 tokens · $11.83 · 2.2h active · 11 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $4.62 | 47,232 | 1.4M | 7.6M | 84.1% |
| test-automation-engineer | $4.25 | 127,044 | 656k | 16.6M | 96.0% |
| qa-engineer | $2.96 | 109,811 | 563k | 8.8M | 93.4% |

## Orchestrator (lead thread) composition

Lead: $4.62 — overhead incl. stages is 42% of the batch · real work 47,232 · cache 7.6M read / 1.4M write · hit rate 84.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |
| other | $0.33 | 13,922 | 93k | 495k | 82.7% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4953 | $6.88 | 81,943 | 140,990 | 1.1M | 24.9M | 26,243,178 | 95.4% | 73.1% |
