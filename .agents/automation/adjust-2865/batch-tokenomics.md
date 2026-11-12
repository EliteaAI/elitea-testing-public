# Batch tokenomics — adjust-2865

Generated: 2026-11-03T05:39:42.246Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,970 | 0.6% | fresh prompt tokens, full price |
| real work: output | 23,643 | 0.4% | generated tokens — the most expensive kind |
| cache write | 337,903 | 6.3% | context stored for reuse (~1.25× input price) |
| cache read | 5,003,068 | 92.7% | context replayed from cache (~0.1× input price) |
| **total** | **5,396,584** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,970 | 23,643 | 338k | 5.0M | 5,396,584 |
**Total: 5,396,584 tokens · $1.83 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.91 | 24,394 | 114k | 3.7M | 96.7% |
| test-automation-engineer | $0.52 | 14,745 | 135k | 733k | 83.5% |
| qa-engineer | $0.40 | 16,474 | 89k | 587k | 85.5% |

## Orchestrator (lead thread) composition

Lead: $0.91 — overhead incl. stages is 50% of the batch · real work 24,394 · cache 3.7M read / 114k write · hit rate 96.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0062 | $0.92 | 20,842 | 10,377 | 223k | 1.3M | 1,575,051 | 84.4% | 29.2% |
