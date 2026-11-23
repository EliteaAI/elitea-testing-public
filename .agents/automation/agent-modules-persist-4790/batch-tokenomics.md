# Batch tokenomics — agent-modules-persist-4790

Generated: 2026-11-23T18:48:47.108Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 121,944 | 0.5% | fresh prompt tokens, full price |
| real work: output | 85,046 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,384,811 | 10.4% | context stored for reuse (~1.25× input price) |
| cache read | 20,300,922 | 88.7% | context replayed from cache (~0.1× input price) |
| **total** | **22,892,723** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 121,944 | 85,046 | 2.4M | 20.3M | 22,892,723 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 22,892,723 tokens · $9.11 · 1.4h active · 16 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.78 | 96,007 | 882k | 10.9M | 92.1% |
| test-automation-lead | $2.73 | 29,321 | 895k | 3.2M | 78.0% |
| qa-engineer | $2.60 | 81,662 | 608k | 6.1M | 90.4% |

## Orchestrator (lead thread) composition

Lead: $2.73 — overhead incl. stages is 57% of the batch · real work 29,321 · cache 3.2M read / 895k write · hit rate 78.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.31 | 9,229 | 109k | 99k | 45.6% |
| gate | $1.80 | 41,992 | 378k | 6.4M | 94.1% |
| report | $0.37 | 12,846 | 116k | 216k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4790 | $3.90 | 60,430 | 53,172 | 887k | 10.3M | 11,345,441 | 91.6% | 49.6% |
