# Batch tokenomics — chat-streaming-2181

Generated: 2026-10-22T04:58:46.627Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 231,394 | 0.7% | fresh prompt tokens, full price |
| real work: output | 147,951 | 0.5% | generated tokens — the most expensive kind |
| cache write | 3,269,778 | 10.4% | context stored for reuse (~1.25× input price) |
| cache read | 27,756,260 | 88.4% | context replayed from cache (~0.1× input price) |
| **total** | **31,405,383** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~35.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 231,394 | 147,951 | 3.3M | 27.8M | 31,405,383 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 31,405,383 tokens · $14.21 · 3.0h active · 19 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $5.82 | 203,932 | 1.2M | 14.1M | 91.6% |
| test-automation-lead | $4.35 | 48,986 | 1.1M | 8.0M | 87.4% |
| qa-engineer | $4.04 | 126,427 | 984k | 5.7M | 84.2% |

## Orchestrator (lead thread) composition

Lead: $4.35 — overhead incl. stages is 43% of the batch · real work 48,986 · cache 8.0M read / 1.1M write · hit rate 87.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,093 | 106k | 97k | 45.8% |
| gate | $0.60 | 13,101 | 119k | 1.8M | 93.5% |
| report | $0.45 | 15,659 | 119k | 216k | 62.9% |
| other | $0.33 | 12,347 | 83k | 483k | 83.8% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2181 | $8.16 | 172,325 | 107,834 | 1.7M | 17.1M | 19,136,959 | 90.1% | 60.9% |
