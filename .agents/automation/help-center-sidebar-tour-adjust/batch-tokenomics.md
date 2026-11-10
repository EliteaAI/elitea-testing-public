# Batch tokenomics — help-center-sidebar-tour-adjust

Generated: 2026-11-10T09:24:14.810Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,669 | 0.4% | fresh prompt tokens, full price |
| real work: output | 24,398 | 0.4% | generated tokens — the most expensive kind |
| cache write | 281,930 | 4.6% | context stored for reuse (~1.25× input price) |
| cache read | 5,806,376 | 94.7% | context replayed from cache (~0.1× input price) |
| **total** | **6,134,373** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~53.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,669 | 24,398 | 282k | 5.8M | 6,134,373 |
**Total: 6,134,373 tokens · $1.75 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.32 | 32,521 | 168k | 5.3M | 96.7% |
| qa-engineer | $0.43 | 13,546 | 114k | 544k | 81.4% |

## Orchestrator (lead thread) composition

Lead: $1.32 — overhead incl. stages is 75% of the batch · real work 32,521 · cache 5.3M read / 168k write · hit rate 96.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3754 | $0.43 | 10,494 | 3,052 | 114k | 544k | 671,609 | 81.4% | 10.9% |
