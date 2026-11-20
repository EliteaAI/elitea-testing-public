# Batch tokenomics — skill-copy-4757

Generated: 2026-11-20T12:27:03.349Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 50,840 | 0.6% | fresh prompt tokens, full price |
| real work: output | 34,233 | 0.4% | generated tokens — the most expensive kind |
| cache write | 871,053 | 10.3% | context stored for reuse (~1.25× input price) |
| cache read | 7,471,857 | 88.7% | context replayed from cache (~0.1× input price) |
| **total** | **8,427,983** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 50,840 | 34,233 | 871k | 7.5M | 8,427,983 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 8,427,983 tokens · $3.71 · 0.6h active · 7 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.38 | 32,728 | 294k | 3.4M | 91.6% |
| test-automation-lead | $1.25 | 22,726 | 319k | 2.3M | 87.2% |
| qa-engineer | $1.08 | 29,619 | 258k | 1.8M | 86.6% |

## Orchestrator (lead thread) composition

Lead: $1.25 — overhead incl. stages is 34% of the batch · real work 22,726 · cache 2.3M read / 319k write · hit rate 87.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4757 | $2.45 | 36,270 | 26,077 | 552k | 5.2M | 5,801,923 | 89.8% | 68.8% |
