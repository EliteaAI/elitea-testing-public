# Batch tokenomics — chat-export-menu-3779

Generated: 2026-10-21T01:58:49.468Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 123,188 | 0.9% | fresh prompt tokens, full price |
| real work: output | 54,672 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,712,946 | 13.2% | context stored for reuse (~1.25× input price) |
| cache read | 11,101,078 | 85.4% | context replayed from cache (~0.1× input price) |
| **total** | **12,991,884** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 123,188 | 54,672 | 1.7M | 11.1M | 12,991,884 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,991,884 tokens · $6.80 · 0.8h active · 15 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.78 | 74,698 | 647k | 5.7M | 89.1% |
| qa-engineer | $2.63 | 79,154 | 640k | 4.2M | 85.9% |
| test-automation-lead | $1.40 | 24,008 | 426k | 1.2M | 72.8% |

## Orchestrator (lead thread) composition

Lead: $1.40 — overhead incl. stages is 39% of the batch · real work 24,008 · cache 1.2M read / 426k write · hit rate 72.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.32 | 8,984 | 105k | 96k | 45.6% |
| gate | $0.52 | 12,291 | 118k | 1.2M | 90.8% |
| report | $0.41 | 12,751 | 114k | 324k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3779 | $4.15 | 78,463 | 41,363 | 950k | 8.2M | 9,311,925 | 88.9% | 71.7% |
