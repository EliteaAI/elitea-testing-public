# Batch tokenomics — adjust-2799

Generated: 2026-10-31T05:05:46.049Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,517 | 0.3% | fresh prompt tokens, full price |
| real work: output | 23,401 | 0.3% | generated tokens — the most expensive kind |
| cache write | 379,058 | 5.5% | context stored for reuse (~1.25× input price) |
| cache read | 6,429,430 | 93.8% | context replayed from cache (~0.1× input price) |
| **total** | **6,853,406** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~51.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,517 | 23,401 | 379k | 6.4M | 6,853,406 |
**Total: 6,853,406 tokens · $2.08 · 0.5h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.67 | 31,973 | 263k | 6.0M | 95.6% |
| qa-engineer | $0.42 | 12,945 | 116k | 435k | 77.5% |

## Orchestrator (lead thread) composition

Lead: $1.67 — overhead incl. stages is 80% of the batch · real work 31,973 · cache 6.0M read / 263k write · hit rate 95.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2008 | $0.42 | 10,490 | 2,455 | 116k | 435k | 563,917 | 77.5% | 8.2% |
