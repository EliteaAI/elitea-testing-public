# Batch tokenomics — adjust-2757

Generated: 2026-10-30T06:06:01.596Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,287 | 0.3% | fresh prompt tokens, full price |
| real work: output | 32,599 | 0.3% | generated tokens — the most expensive kind |
| cache write | 370,536 | 3.9% | context stored for reuse (~1.25× input price) |
| cache read | 9,063,913 | 95.4% | context replayed from cache (~0.1× input price) |
| **total** | **9,499,335** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~57.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,287 | 32,599 | 371k | 9.1M | 9,499,335 |
**Total: 9,499,335 tokens · $2.45 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.63 | 36,894 | 150k | 8.2M | 98.1% |
| qa-engineer | $0.82 | 27,992 | 220k | 830k | 77.5% |

## Orchestrator (lead thread) composition

Lead: $1.63 — overhead incl. stages is 66% of the batch · real work 36,894 · cache 8.2M read / 150k write · hit rate 98.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2059 | $0.82 | 20,981 | 7,011 | 220k | 830k | 1,078,255 | 77.5% | 11.4% |
