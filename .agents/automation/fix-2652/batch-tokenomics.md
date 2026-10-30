# Batch tokenomics — fix-2652

Generated: 2026-10-24T05:30:06.154Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,664 | 0.4% | fresh prompt tokens, full price |
| real work: output | 20,002 | 0.4% | generated tokens — the most expensive kind |
| cache write | 220,093 | 4.3% | context stored for reuse (~1.25× input price) |
| cache read | 4,862,384 | 94.9% | context replayed from cache (~0.1× input price) |
| **total** | **5,124,143** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~55.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,664 | 20,002 | 220k | 4.9M | 5,124,143 |
**Total: 5,124,143 tokens · $1.41 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.98 | 28,267 | 102k | 4.4M | 97.5% |
| qa-engineer | $0.43 | 13,399 | 118k | 438k | 77.3% |

## Orchestrator (lead thread) composition

Lead: $0.98 — overhead incl. stages is 70% of the batch · real work 28,267 · cache 4.4M read / 102k write · hit rate 97.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2009 | $0.43 | 10,499 | 2,900 | 118k | 438k | 569,411 | 77.3% | 11.1% |
