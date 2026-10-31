# Batch tokenomics — adjust-2805

Generated: 2026-10-31T07:16:10.343Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 34,845 | 0.3% | fresh prompt tokens, full price |
| real work: output | 43,487 | 0.4% | generated tokens — the most expensive kind |
| cache write | 530,468 | 4.8% | context stored for reuse (~1.25× input price) |
| cache read | 10,363,846 | 94.5% | context replayed from cache (~0.1× input price) |
| **total** | **10,972,646** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~53.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 34,845 | 43,487 | 530k | 10.4M | 10,972,646 |
**Total: 10,972,646 tokens · $3.15 · 0.8h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.79 | 39,336 | 260k | 6.9M | 96.2% |
| test-automation-engineer | $0.90 | 22,976 | 159k | 2.7M | 94.1% |
| qa-engineer | $0.47 | 16,020 | 111k | 736k | 85.8% |

## Orchestrator (lead thread) composition

Lead: $1.79 — overhead incl. stages is 57% of the batch · real work 39,336 · cache 6.9M read / 260k write · hit rate 96.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1866 | $1.37 | 20,888 | 18,108 | 270k | 3.5M | 3,763,728 | 92.2% | 34.3% |
