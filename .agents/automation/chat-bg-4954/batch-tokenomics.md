# Batch tokenomics — chat-bg-4954

Generated: 2026-11-27T19:51:25.854Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 158,720 | 0.3% | fresh prompt tokens, full price |
| real work: output | 223,871 | 0.4% | generated tokens — the most expensive kind |
| cache write | 6,096,487 | 11.4% | context stored for reuse (~1.25× input price) |
| cache read | 47,005,266 | 87.9% | context replayed from cache (~0.1× input price) |
| **total** | **53,484,344** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~76.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~34.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 158,720 | 223,871 | 6.1M | 47.0M | 53,484,344 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 53,484,344 tokens · $22.53 · 5.2h active · 16 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $10.62 | 51,511 | 3.7M | 9.1M | 71.0% |
| test-automation-engineer | $9.24 | 252,636 | 1.7M | 31.5M | 94.5% |
| qa-engineer | $2.67 | 78,444 | 640k | 6.4M | 90.3% |

## Orchestrator (lead thread) composition

Lead: $10.62 — overhead incl. stages is 53% of the batch · real work 51,511 · cache 9.1M read / 3.7M write · hit rate 71.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.61 | 18,503 | 219k | 198k | 45.5% |
| gate | $0.42 | 11,258 | 119k | 800k | 86.3% |
| report | $0.40 | 13,904 | 118k | 336k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4954 | $10.48 | 107,203 | 180,212 | 1.9M | 36.5M | 38,748,845 | 94.7% | 72.4% |
