# Batch tokenomics — toolkit-copy-4758

Generated: 2026-11-20T12:59:11.936Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 94,487 | 0.9% | fresh prompt tokens, full price |
| real work: output | 43,616 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,523,903 | 14.3% | context stored for reuse (~1.25× input price) |
| cache read | 9,018,451 | 84.4% | context replayed from cache (~0.1× input price) |
| **total** | **10,680,457** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 94,487 | 43,616 | 1.5M | 9.0M | 10,680,457 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 10,680,457 tokens · $5.87 · 0.8h active · 12 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.68 | 66,195 | 623k | 5.6M | 89.4% |
| qa-engineer | $1.77 | 48,097 | 487k | 1.8M | 77.9% |
| test-automation-lead | $1.42 | 23,811 | 414k | 1.6M | 78.4% |

## Orchestrator (lead thread) composition

Lead: $1.42 — overhead incl. stages is 46% of the batch · real work 23,811 · cache 1.6M read / 414k write · hit rate 78.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,127 | 109k | 98k | 45.6% |
| gate | $0.49 | 11,519 | 119k | 1.0M | 89.0% |
| report | $0.42 | 13,116 | 116k | 330k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4758 | $3.20 | 51,497 | 29,033 | 766k | 6.0M | 6,837,399 | 88.0% | 64.0% |
