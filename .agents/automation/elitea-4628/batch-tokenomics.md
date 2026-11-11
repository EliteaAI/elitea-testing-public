# Batch tokenomics — elitea-4628

Generated: 2026-11-11T09:21:15.218Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 94,007 | 0.7% | fresh prompt tokens, full price |
| real work: output | 56,991 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,686,687 | 13.3% | context stored for reuse (~1.25× input price) |
| cache read | 10,800,235 | 85.5% | context replayed from cache (~0.1× input price) |
| **total** | **12,637,920** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 94,007 | 56,991 | 1.7M | 10.8M | 12,637,920 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,637,920 tokens · $6.68 · 1.1h active · 12 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.76 | 67,610 | 623k | 6.1M | 90.2% |
| qa-engineer | $2.06 | 59,550 | 501k | 3.0M | 84.7% |
| test-automation-lead | $1.86 | 23,838 | 562k | 1.7M | 74.6% |

## Orchestrator (lead thread) composition

Lead: $1.86 — overhead incl. stages is 47% of the batch · real work 23,838 · cache 1.7M read / 562k write · hit rate 74.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,062 | 107k | 97k | 45.7% |
| gate | $0.49 | 11,812 | 118k | 1.0M | 89.0% |
| report | $0.43 | 13,296 | 115k | 328k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4628 | $3.57 | 51,185 | 41,805 | 784k | 7.6M | 8,526,307 | 90.2% | 67.5% |
