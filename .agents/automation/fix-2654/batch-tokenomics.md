# Batch tokenomics — fix-2654

Generated: 2026-10-24T06:16:58.324Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,625 | 0.2% | fresh prompt tokens, full price |
| real work: output | 29,407 | 0.3% | generated tokens — the most expensive kind |
| cache write | 264,600 | 3.0% | context stored for reuse (~1.25× input price) |
| cache read | 8,561,138 | 96.4% | context replayed from cache (~0.1× input price) |
| **total** | **8,876,770** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 96.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~86.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~63.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,625 | 29,407 | 265k | 8.6M | 8,876,770 |
**Total: 8,876,770 tokens · $2.04 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.56 | 36,045 | 143k | 7.9M | 98.1% |
| qa-engineer | $0.48 | 14,987 | 121k | 682k | 83.8% |

## Orchestrator (lead thread) composition

Lead: $1.56 — overhead incl. stages is 76% of the batch · real work 36,045 · cache 7.9M read / 143k write · hit rate 98.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2034 | $0.48 | 10,499 | 4,488 | 121k | 682k | 818,249 | 83.8% | 9.2% |
