# Batch tokenomics — adjust-elitea-4635

Generated: 2026-11-17T06:40:40.703Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,558 | 1.4% | fresh prompt tokens, full price |
| real work: output | 12,089 | 0.5% | generated tokens — the most expensive kind |
| cache write | 333,310 | 14.5% | context stored for reuse (~1.25× input price) |
| cache read | 1,926,526 | 83.6% | context replayed from cache (~0.1× input price) |
| **total** | **2,303,483** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 84.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~27.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,558 | 12,089 | 333k | 1.9M | 2,303,483 |
**Total: 2,303,483 tokens · $1.33 · 0.1h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $0.51 | 15,375 | 127k | 716k | 83.9% |
| test-automation-lead | $0.51 | 15,358 | 120k | 969k | 88.1% |
| qa-engineer | $0.31 | 12,914 | 86k | 241k | 71.4% |

## Orchestrator (lead thread) composition

Lead: $0.51 — overhead incl. stages is 38% of the batch · real work 15,358 · cache 969k read / 120k write · hit rate 88.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4635 | $0.82 | 20,914 | 7,375 | 214k | 958k | 1,199,538 | 80.3% | 52.1% |
