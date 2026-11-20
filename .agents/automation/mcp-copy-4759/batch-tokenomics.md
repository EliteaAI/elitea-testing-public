# Batch tokenomics — mcp-copy-4759

Generated: 2026-11-20T13:47:30.886Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 94,736 | 0.8% | fresh prompt tokens, full price |
| real work: output | 45,971 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,761,370 | 14.6% | context stored for reuse (~1.25× input price) |
| cache read | 10,185,248 | 84.3% | context replayed from cache (~0.1× input price) |
| **total** | **12,087,325** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 94,736 | 45,971 | 1.8M | 10.2M | 12,087,325 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,087,325 tokens · $6.70 · 1.1h active · 12 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.77 | 61,990 | 719k | 4.4M | 85.3% |
| qa-engineer | $2.16 | 54,706 | 513k | 4.1M | 88.1% |
| test-automation-lead | $1.77 | 24,011 | 529k | 1.7M | 75.5% |

## Orchestrator (lead thread) composition

Lead: $1.77 — overhead incl. stages is 45% of the batch · real work 24,011 · cache 1.7M read / 529k write · hit rate 75.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,153 | 109k | 98k | 45.7% |
| gate | $0.48 | 11,831 | 118k | 912k | 87.9% |
| report | $0.41 | 12,956 | 116k | 215k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4759 | $3.71 | 51,534 | 31,222 | 891k | 7.3M | 8,250,185 | 88.5% | 68.3% |
