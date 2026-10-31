# Batch tokenomics — adjust-2801

Generated: 2026-10-31T05:46:03.857Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,728 | 0.6% | fresh prompt tokens, full price |
| real work: output | 25,239 | 0.5% | generated tokens — the most expensive kind |
| cache write | 526,376 | 9.5% | context stored for reuse (~1.25× input price) |
| cache read | 4,959,394 | 89.5% | context replayed from cache (~0.1× input price) |
| **total** | **5,542,737** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~37.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,728 | 25,239 | 526k | 5.0M | 5,542,737 |
**Total: 5,542,737 tokens · $2.34 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.20 | 22,601 | 276k | 2.6M | 90.2% |
| test-automation-engineer | $0.80 | 21,124 | 162k | 2.0M | 92.0% |
| qa-engineer | $0.34 | 13,242 | 89k | 359k | 78.4% |

## Orchestrator (lead thread) composition

Lead: $1.20 — overhead incl. stages is 51% of the batch · real work 22,601 · cache 2.6M read / 276k write · hit rate 90.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2014 | $1.14 | 20,873 | 13,493 | 251k | 2.3M | 2,616,273 | 89.6% | 47.2% |
