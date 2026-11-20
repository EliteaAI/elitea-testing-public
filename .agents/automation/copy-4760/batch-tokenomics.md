# Batch tokenomics — copy-4760

Generated: 2026-11-20T14:07:43.955Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 94,702 | 1.0% | fresh prompt tokens, full price |
| real work: output | 39,090 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,373,930 | 15.0% | context stored for reuse (~1.25× input price) |
| cache read | 7,665,951 | 83.6% | context replayed from cache (~0.1× input price) |
| **total** | **9,173,673** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 83.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~71.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~27.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 94,702 | 39,090 | 1.4M | 7.7M | 9,173,673 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 9,173,673 tokens · $5.26 · 0.5h active · 12 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.41 | 62,334 | 600k | 4.1M | 86.5% |
| qa-engineer | $1.66 | 48,092 | 446k | 1.9M | 79.4% |
| test-automation-lead | $1.19 | 23,366 | 328k | 1.7M | 83.0% |

## Orchestrator (lead thread) composition

Lead: $1.19 — overhead incl. stages is 47% of the batch · real work 23,366 · cache 1.7M read / 328k write · hit rate 83.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,186 | 108k | 98k | 45.7% |
| gate | $0.55 | 12,953 | 120k | 1.4M | 91.5% |
| report | $0.41 | 13,325 | 116k | 215k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4760 | $2.77 | 51,486 | 23,476 | 701k | 4.3M | 5,055,339 | 85.0% | 55.1% |
