# Batch tokenomics — adjust-2941

Generated: 2026-11-12T12:30:37.258Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 255,920 | 0.6% | fresh prompt tokens, full price |
| real work: output | 214,477 | 0.5% | generated tokens — the most expensive kind |
| cache write | 4,109,132 | 9.1% | context stored for reuse (~1.25× input price) |
| cache read | 40,515,146 | 89.8% | context replayed from cache (~0.1× input price) |
| **total** | **45,094,675** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~38.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 255,920 | 214,477 | 4.1M | 40.5M | 45,094,675 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 45,094,675 tokens · $18.68 · 2.8h active · 30 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $8.98 | 250,684 | 1.6M | 25.7M | 93.6% |
| qa-engineer | $5.44 | 167,015 | 1.4M | 6.9M | 82.4% |
| test-automation-lead | $4.26 | 52,698 | 1.1M | 7.9M | 87.6% |

## Orchestrator (lead thread) composition

Lead: $4.26 — overhead incl. stages is 32% of the batch · real work 52,698 · cache 7.9M read / 1.1M write · hit rate 87.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.86 | 26,436 | 199k | 1.7M | 88.6% |
| gate | $0.44 | 10,579 | 117k | 679k | 84.4% |
| report | $0.44 | 13,723 | 118k | 335k | 72.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4632 | $12.68 | 197,936 | 169,025 | 2.6M | 29.9M | 32,864,607 | 91.5% | 72.9% |
