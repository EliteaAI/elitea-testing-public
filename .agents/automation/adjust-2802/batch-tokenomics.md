# Batch tokenomics — adjust-2802

Generated: 2026-10-31T06:27:50.142Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 22,024 | 0.4% | fresh prompt tokens, full price |
| real work: output | 22,243 | 0.4% | generated tokens — the most expensive kind |
| cache write | 356,177 | 6.5% | context stored for reuse (~1.25× input price) |
| cache read | 5,115,894 | 92.7% | context replayed from cache (~0.1× input price) |
| **total** | **5,516,338** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 22,024 | 22,243 | 356k | 5.1M | 5,516,338 |
**Total: 5,516,338 tokens · $1.84 · 0.5h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.46 | 31,774 | 244k | 4.9M | 95.1% |
| qa-engineer | $0.38 | 12,493 | 112k | 206k | 62.7% |

## Orchestrator (lead thread) composition

Lead: $1.46 — overhead incl. stages is 79% of the batch · real work 31,774 · cache 4.9M read / 244k write · hit rate 95.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2378 | $0.38 | 10,491 | 2,002 | 112k | 206k | 330,966 | 62.7% | 6.0% |
