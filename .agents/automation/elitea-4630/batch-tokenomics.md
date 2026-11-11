# Batch tokenomics — elitea-4630

Generated: 2026-11-11T12:56:05.402Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 58,949 | 0.6% | fresh prompt tokens, full price |
| real work: output | 39,590 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,303,178 | 13.6% | context stored for reuse (~1.25× input price) |
| cache read | 8,168,023 | 85.4% | context replayed from cache (~0.1× input price) |
| **total** | **9,569,740** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 58,949 | 39,590 | 1.3M | 8.2M | 9,569,740 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 9,569,740 tokens · $5.07 · 1.3h active · 8 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $2.22 | 49,009 | 542k | 3.9M | 87.2% |
| test-automation-lead | $1.77 | 20,677 | 546k | 1.4M | 71.3% |
| test-automation-engineer | $1.08 | 28,853 | 215k | 2.9M | 92.6% |

## Orchestrator (lead thread) composition

Lead: $1.77 — overhead incl. stages is 35% of the batch · real work 20,677 · cache 1.4M read / 546k write · hit rate 71.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4630 | $3.30 | 43,733 | 34,129 | 757k | 6.8M | 7,606,555 | 89.4% | 79.5% |
