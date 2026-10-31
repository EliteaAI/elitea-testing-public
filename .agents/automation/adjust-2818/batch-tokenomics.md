# Batch tokenomics — adjust-2818

Generated: 2026-10-31T09:55:05.671Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,651 | 0.8% | fresh prompt tokens, full price |
| real work: output | 14,707 | 0.4% | generated tokens — the most expensive kind |
| cache write | 427,474 | 10.7% | context stored for reuse (~1.25× input price) |
| cache read | 3,516,530 | 88.1% | context replayed from cache (~0.1× input price) |
| **total** | **3,990,362** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 88.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~76.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~35.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,651 | 14,707 | 427k | 3.5M | 3,990,362 |
**Total: 3,990,362 tokens · $1.79 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.78 | 15,785 | 213k | 1.1M | 82.9% |
| test-automation-engineer | $0.71 | 18,088 | 130k | 2.2M | 94.0% |
| qa-engineer | $0.30 | 12,485 | 85k | 237k | 71.4% |

## Orchestrator (lead thread) composition

Lead: $0.78 — overhead incl. stages is 44% of the batch · real work 15,785 · cache 1.1M read / 213k write · hit rate 82.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | $1.01 | 20,868 | 9,705 | 215k | 2.4M | 2,680,666 | 91.2% | 67.2% |
