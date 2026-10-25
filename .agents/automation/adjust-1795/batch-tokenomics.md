# Batch tokenomics — adjust-1795

Generated: 2026-10-25T06:11:55.844Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 22,020 | 0.3% | fresh prompt tokens, full price |
| real work: output | 21,095 | 0.3% | generated tokens — the most expensive kind |
| cache write | 244,613 | 3.8% | context stored for reuse (~1.25× input price) |
| cache read | 6,131,818 | 95.5% | context replayed from cache (~0.1× input price) |
| **total** | **6,419,546** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~58.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 22,020 | 21,095 | 245k | 6.1M | 6,419,546 |
**Total: 6,419,546 tokens · $1.63 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.25 | 30,551 | 132k | 5.9M | 97.6% |
| qa-engineer | $0.38 | 12,564 | 113k | 207k | 62.6% |

## Orchestrator (lead thread) composition

Lead: $1.25 — overhead incl. stages is 77% of the batch · real work 30,551 · cache 5.9M read / 132k write · hit rate 97.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1795 | $0.38 | 10,490 | 2,074 | 113k | 207k | 332,541 | 62.6% | 5.2% |
