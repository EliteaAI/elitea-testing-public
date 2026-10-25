# Batch tokenomics — adjust-0864-r2

Generated: 2026-10-25T04:10:57.372Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,551 | 0.4% | fresh prompt tokens, full price |
| real work: output | 19,869 | 0.4% | generated tokens — the most expensive kind |
| cache write | 350,254 | 6.6% | context stored for reuse (~1.25× input price) |
| cache read | 4,915,239 | 92.6% | context replayed from cache (~0.1× input price) |
| **total** | **5,306,913** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,551 | 19,869 | 350k | 4.9M | 5,306,913 |
**Total: 5,306,913 tokens · $1.77 · 0.4h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.37 | 28,145 | 235k | 4.6M | 94.9% |
| qa-engineer | $0.40 | 13,275 | 115k | 321k | 71.9% |

## Orchestrator (lead thread) composition

Lead: $1.37 — overhead incl. stages is 77% of the batch · real work 28,145 · cache 4.6M read / 235k write · hit rate 94.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0864 | $0.40 | 10,500 | 2,775 | 115k | 321k | 448,845 | 71.9% | 8.5% |
