# Batch tokenomics — builder-modules-chat-2459

Generated: 2026-10-30T11:47:22.238Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 577,435 | 0.1% | fresh prompt tokens, full price |
| real work: output | 1,657,774 | 0.4% | generated tokens — the most expensive kind |
| cache write | 13,860,544 | 3.0% | context stored for reuse (~1.25× input price) |
| cache read | 450,485,710 | 96.6% | context replayed from cache (~0.1× input price) |
| **total** | **466,581,463** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 96.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~86.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~63.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5 | 460,353 | 1,520,228 | 6.8M | 420.4M | 429,111,407 |
| 1_eu.anthropic.claude-sonnet-5-5 | 116,982 | 128,755 | 6.8M | 29.1M | 36,218,249 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 100 | 8,791 | 256k | 987k | 1,251,807 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 466,581,463 tokens · $153.01 · 20.9h active · 25 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $97.20 | 1,644,848 | 7.2M | 294.1M | 97.5% |
| test-automation-lead | $31.14 | 180,436 | 5.5M | 72.7M | 92.9% |
| qa-engineer | $24.67 | 409,925 | 1.1M | 83.7M | 98.5% |

## Orchestrator (lead thread) composition

Lead: $31.14 — overhead incl. stages is 33% of the batch · real work 180,436 · cache 72.7M read / 5.5M write · hit rate 92.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.17 | 2,137 | 86k | 323k | 78.9% |
| gate | $4.89 | 88,720 | 204k | 16.4M | 98.6% |
| report | $0.19 | 5,687 | 87k | 336k | 79.5% |
| other | $14.28 | 322,766 | 889k | 41.9M | 97.7% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3370 | $33.17 | 221,534 | 426,590 | 2.5M | 98.8M | 101,932,979 | 97.3% | 21.8% |
| ELITEA-3372 | $69.18 | 176,147 | 811,192 | 4.5M | 220.1M | 225,595,044 | 97.9% | 48.4% |
