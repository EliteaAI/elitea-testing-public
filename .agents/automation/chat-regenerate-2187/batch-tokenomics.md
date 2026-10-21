# Batch tokenomics — chat-regenerate-2187

Generated: 2026-10-21T00:51:46.008Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 129,951 | 0.9% | fresh prompt tokens, full price |
| real work: output | 57,154 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,191,559 | 15.9% | context stored for reuse (~1.25× input price) |
| cache read | 11,406,524 | 82.7% | context replayed from cache (~0.1× input price) |
| **total** | **13,785,188** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 83.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~70.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~26.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 129,951 | 57,154 | 2.2M | 11.4M | 13,785,188 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 13,785,188 tokens · $8.20 · 1.5h active · 16 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.81 | 90,513 | 909k | 7.6M | 88.7% |
| qa-engineer | $2.38 | 69,701 | 656k | 2.4M | 77.3% |
| test-automation-lead | $2.01 | 26,891 | 626k | 1.4M | 68.8% |

## Orchestrator (lead thread) composition

Lead: $2.01 — overhead incl. stages is 40% of the batch · real work 26,891 · cache 1.4M read / 626k write · hit rate 68.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.32 | 9,030 | 105k | 96k | 45.7% |
| gate | $0.52 | 12,292 | 117k | 1.2M | 90.8% |
| report | $0.43 | 14,717 | 115k | 211k | 63.0% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2187 | $4.92 | 85,306 | 38,869 | 1.2M | 8.4M | 9,784,085 | 86.5% | 71.0% |
