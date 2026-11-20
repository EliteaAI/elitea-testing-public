# Batch tokenomics — update-2991

Generated: 2026-11-20T08:33:28.388Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 41,579 | 0.5% | fresh prompt tokens, full price |
| real work: output | 36,325 | 0.4% | generated tokens — the most expensive kind |
| cache write | 747,038 | 9.1% | context stored for reuse (~1.25× input price) |
| cache read | 7,405,949 | 90.0% | context replayed from cache (~0.1× input price) |
| **total** | **8,230,891** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~39% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 41,579 | 36,325 | 747k | 7.4M | 8,230,891 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 8,230,891 tokens · $3.36 · 0.7h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $1.54 | 37,465 | 293k | 4.3M | 93.3% |
| test-automation-lead | $1.21 | 25,396 | 313k | 1.9M | 85.4% |
| test-automation-engineer | $0.61 | 15,043 | 141k | 1.2M | 88.9% |

## Orchestrator (lead thread) composition

Lead: $1.21 — overhead incl. stages is 36% of the batch · real work 25,396 · cache 1.9M read / 313k write · hit rate 85.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1794 | $1.07 | 12,929 | 13,325 | 217k | 2.7M | 2,988,113 | 92.3% | 36.3% |
| ELITEA-1896 | $1.07 | 12,929 | 13,325 | 217k | 2.7M | 2,988,113 | 92.3% | 36.3% |
