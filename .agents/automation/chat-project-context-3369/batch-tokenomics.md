# Batch tokenomics — chat-project-context-3369

Generated: 2026-10-30T10:39:46.909Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 124,625 | 0.6% | fresh prompt tokens, full price |
| real work: output | 84,292 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,709,622 | 13.8% | context stored for reuse (~1.25× input price) |
| cache read | 16,758,391 | 85.2% | context replayed from cache (~0.1× input price) |
| **total** | **19,676,930** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~29.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 124,625 | 84,292 | 2.7M | 16.8M | 19,676,930 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 19,676,930 tokens · $10.50 · 1.6h active · 15 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $4.19 | 40,510 | 1.3M | 4.5M | 77.7% |
| test-automation-engineer | $3.21 | 81,187 | 705k | 7.5M | 90.9% |
| qa-engineer | $3.09 | 87,220 | 750k | 4.8M | 85.6% |

## Orchestrator (lead thread) composition

Lead: $4.19 — overhead incl. stages is 52% of the batch · real work 40,510 · cache 4.5M read / 1.3M write · hit rate 77.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 8,963 | 107k | 98k | 45.9% |
| gate | $0.49 | 11,622 | 117k | 1.0M | 89.0% |
| report | $0.44 | 14,845 | 118k | 216k | 63.0% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3369 | $5.05 | 76,865 | 56,112 | 1.1M | 11.0M | 12,215,106 | 90.2% | 62.1% |
