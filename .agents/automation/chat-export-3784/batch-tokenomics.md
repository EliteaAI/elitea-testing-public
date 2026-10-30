# Batch tokenomics — chat-export-3784

Generated: 2026-10-20T19:54:28.784Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 67,530 | 0.9% | fresh prompt tokens, full price |
| real work: output | 36,961 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,026,980 | 13.2% | context stored for reuse (~1.25× input price) |
| cache read | 6,656,741 | 85.5% | context replayed from cache (~0.1× input price) |
| **total** | **7,788,212** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~74.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 67,530 | 36,961 | 1.0M | 6.7M | 7,788,212 |
**Total: 7,788,212 tokens · $4.13 · 0.5h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.93 | 53,619 | 477k | 3.1M | 85.9% |
| qa-engineer | $1.13 | 30,592 | 264k | 2.0M | 87.9% |
| test-automation-lead | $1.07 | 20,280 | 286k | 1.5M | 83.4% |

## Orchestrator (lead thread) composition

Lead: $1.07 — overhead incl. stages is 47% of the batch · real work 20,280 · cache 1.5M read / 286k write · hit rate 83.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| gate | $0.44 | 10,767 | 113k | 769k | 86.4% |
| report | $0.43 | 13,769 | 114k | 323k | 72.5% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3784 | $2.20 | 36,414 | 23,261 | 514k | 4.1M | 4,633,046 | 88.1% | 59.5% |
