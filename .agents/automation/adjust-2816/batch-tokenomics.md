# Batch tokenomics — adjust-2816

Generated: 2026-10-31T09:29:25.182Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,725 | 0.6% | fresh prompt tokens, full price |
| real work: output | 17,307 | 0.3% | generated tokens — the most expensive kind |
| cache write | 352,669 | 7.0% | context stored for reuse (~1.25× input price) |
| cache read | 4,656,319 | 92.1% | context replayed from cache (~0.1× input price) |
| **total** | **5,058,020** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,725 | 17,307 | 353k | 4.7M | 5,058,020 |
**Total: 5,058,020 tokens · $1.74 · 0.1h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.76 | 20,900 | 104k | 3.1M | 96.4% |
| test-automation-engineer | $0.62 | 14,984 | 150k | 1.2M | 88.5% |
| qa-engineer | $0.36 | 13,148 | 98k | 360k | 76.8% |

## Orchestrator (lead thread) composition

Lead: $0.76 — overhead incl. stages is 44% of the batch · real work 20,900 · cache 3.1M read / 104k write · hit rate 96.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2006 | $0.98 | 20,856 | 7,276 | 248k | 1.6M | 1,865,403 | 85.5% | 36.9% |
