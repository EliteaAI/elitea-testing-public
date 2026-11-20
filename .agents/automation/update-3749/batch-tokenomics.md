# Batch tokenomics — update-3749

Generated: 2026-11-20T08:07:59.479Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,930 | 0.3% | fresh prompt tokens, full price |
| real work: output | 48,374 | 0.5% | generated tokens — the most expensive kind |
| cache write | 583,295 | 6.0% | context stored for reuse (~1.25× input price) |
| cache read | 9,008,564 | 93.1% | context replayed from cache (~0.1× input price) |
| **total** | **9,672,163** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~47.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,930 | 48,374 | 583k | 9.0M | 9,672,163 |
**Total: 9,672,163 tokens · $3.20 · 0.6h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.77 | 45,712 | 218k | 6.9M | 96.8% |
| test-automation-lead | $1.03 | 18,575 | 268k | 1.6M | 85.4% |
| qa-engineer | $0.40 | 16,017 | 97k | 493k | 82.2% |

## Orchestrator (lead thread) composition

Lead: $1.03 — overhead incl. stages is 32% of the batch · real work 18,575 · cache 1.6M read / 268k write · hit rate 85.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | $2.17 | 21,025 | 40,704 | 315k | 7.4M | 7,752,008 | 95.6% | 80.1% |
