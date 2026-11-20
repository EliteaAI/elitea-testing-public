# Batch tokenomics — update-2992

Generated: 2026-11-20T08:59:43.465Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,826 | 0.6% | fresh prompt tokens, full price |
| real work: output | 19,477 | 0.4% | generated tokens — the most expensive kind |
| cache write | 479,908 | 9.5% | context stored for reuse (~1.25× input price) |
| cache read | 4,502,237 | 89.4% | context replayed from cache (~0.1× input price) |
| **total** | **5,033,448** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~38.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,826 | 19,477 | 480k | 4.5M | 5,033,448 |
**Total: 5,033,448 tokens · $2.13 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $0.92 | 20,349 | 182k | 2.6M | 93.1% |
| test-automation-lead | $0.82 | 15,982 | 207k | 1.3M | 85.9% |
| qa-engineer | $0.39 | 14,972 | 91k | 597k | 85.5% |

## Orchestrator (lead thread) composition

Lead: $0.82 — overhead incl. stages is 39% of the batch · real work 15,982 · cache 1.3M read / 207k write · hit rate 85.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1795 | $1.30 | 20,974 | 14,347 | 273k | 3.2M | 3,488,079 | 91.5% | 69.3% |
