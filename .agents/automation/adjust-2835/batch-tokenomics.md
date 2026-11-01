# Batch tokenomics — adjust-2835

Generated: 2026-11-01T04:11:14.774Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,042 | 0.6% | fresh prompt tokens, full price |
| real work: output | 20,624 | 0.4% | generated tokens — the most expensive kind |
| cache write | 382,973 | 7.7% | context stored for reuse (~1.25× input price) |
| cache read | 4,536,972 | 91.2% | context replayed from cache (~0.1× input price) |
| **total** | **4,972,611** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,042 | 20,624 | 383k | 4.5M | 4,972,611 |
**Total: 4,972,611 tokens · $1.87 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.89 | 21,830 | 143k | 3.0M | 95.1% |
| test-automation-engineer | $0.64 | 17,223 | 152k | 1.2M | 87.9% |
| qa-engineer | $0.34 | 13,613 | 89k | 356k | 78.2% |

## Orchestrator (lead thread) composition

Lead: $0.89 — overhead incl. stages is 47% of the batch · real work 21,830 · cache 3.0M read / 143k write · hit rate 95.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2016 | $0.99 | 20,857 | 9,979 | 240k | 1.5M | 1,802,306 | 85.4% | 36.2% |
