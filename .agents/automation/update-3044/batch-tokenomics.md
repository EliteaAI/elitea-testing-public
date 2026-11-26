# Batch tokenomics — update-3044

Generated: 2026-11-26T16:44:19.687Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,436 | 0.9% | fresh prompt tokens, full price |
| real work: output | 13,571 | 0.4% | generated tokens — the most expensive kind |
| cache write | 293,823 | 8.5% | context stored for reuse (~1.25× input price) |
| cache read | 3,128,122 | 90.2% | context replayed from cache (~0.1× input price) |
| **total** | **3,467,952** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~40.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,436 | 13,571 | 294k | 3.1M | 3,467,952 |
**Total: 3,467,952 tokens · $1.25 · 0.2h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $0.51 | 15,233 | 129k | 1.2M | 89.8% |
| test-automation-lead | $0.43 | 17,050 | 77k | 1.5M | 94.6% |
| qa-engineer | $0.31 | 13,724 | 88k | 361k | 78.5% |

## Orchestrator (lead thread) composition

Lead: $0.43 — overhead incl. stages is 34% of the batch · real work 17,050 · cache 1.5M read / 77k write · hit rate 94.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | $0.82 | 21,369 | 7,588 | 217k | 1.6M | 1,828,489 | 86.9% | 52.7% |
