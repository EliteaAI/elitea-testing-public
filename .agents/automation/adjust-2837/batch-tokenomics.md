# Batch tokenomics — adjust-2837

Generated: 2026-11-01T04:53:13.245Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,839 | 0.4% | fresh prompt tokens, full price |
| real work: output | 30,161 | 0.4% | generated tokens — the most expensive kind |
| cache write | 487,047 | 6.5% | context stored for reuse (~1.25× input price) |
| cache read | 6,984,753 | 92.7% | context replayed from cache (~0.1× input price) |
| **total** | **7,533,800** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,839 | 30,161 | 487k | 7.0M | 7,533,800 |
**Total: 7,533,800 tokens · $2.53 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.25 | 23,876 | 250k | 3.4M | 92.9% |
| test-automation-engineer | $0.94 | 24,374 | 147k | 3.2M | 95.4% |
| qa-engineer | $0.35 | 13,750 | 90k | 358k | 78.1% |

## Orchestrator (lead thread) composition

Lead: $1.25 — overhead incl. stages is 49% of the batch · real work 23,876 · cache 3.4M read / 250k write · hit rate 92.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0852 | $1.28 | 20,869 | 17,255 | 237k | 3.6M | 3,865,243 | 93.3% | 51.3% |
