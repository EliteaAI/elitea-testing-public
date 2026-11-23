# Batch tokenomics — attachments-switch-4791

Generated: 2026-11-23T19:43:46.839Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 105,090 | 0.6% | fresh prompt tokens, full price |
| real work: output | 78,012 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,820,559 | 10.0% | context stored for reuse (~1.25× input price) |
| cache read | 16,180,823 | 89.0% | context replayed from cache (~0.1× input price) |
| **total** | **18,184,484** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 105,090 | 78,012 | 1.8M | 16.2M | 18,184,484 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 18,184,484 tokens · $7.20 · 1.3h active · 13 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $2.82 | 86,366 | 622k | 7.5M | 91.8% |
| test-automation-engineer | $2.48 | 69,169 | 608k | 6.1M | 90.4% |
| test-automation-lead | $1.90 | 27,567 | 590k | 2.6M | 80.9% |

## Orchestrator (lead thread) composition

Lead: $1.90 — overhead incl. stages is 43% of the batch · real work 27,567 · cache 2.6M read / 590k write · hit rate 80.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.31 | 9,235 | 109k | 99k | 45.7% |
| gate | $0.53 | 12,892 | 121k | 1.6M | 92.6% |
| report | $0.37 | 12,406 | 116k | 216k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4791 | $4.10 | 60,455 | 60,547 | 884k | 11.7M | 12,656,390 | 92.5% | 69.6% |
