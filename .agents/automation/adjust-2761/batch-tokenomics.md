# Batch tokenomics — adjust-2761

Generated: 2026-10-30T08:15:45.219Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,518 | 0.5% | fresh prompt tokens, full price |
| real work: output | 19,174 | 0.4% | generated tokens — the most expensive kind |
| cache write | 261,889 | 5.8% | context stored for reuse (~1.25× input price) |
| cache read | 4,199,014 | 93.3% | context replayed from cache (~0.1× input price) |
| **total** | **4,501,595** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~48.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,518 | 19,174 | 262k | 4.2M | 4,501,595 |
**Total: 4,501,595 tokens · $1.44 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.94 | 25,949 | 122k | 3.7M | 96.6% |
| qa-engineer | $0.50 | 14,743 | 140k | 461k | 75.5% |

## Orchestrator (lead thread) composition

Lead: $0.94 — overhead incl. stages is 65% of the batch · real work 25,949 · cache 3.7M read / 122k write · hit rate 96.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2009 | $0.50 | 10,498 | 4,245 | 140k | 461k | 615,787 | 75.5% | 13.7% |
