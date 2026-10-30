# Batch tokenomics — adjust-2448-2577

Generated: 2026-10-23T06:51:05.981Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,710 | 0.6% | fresh prompt tokens, full price |
| real work: output | 20,856 | 0.4% | generated tokens — the most expensive kind |
| cache write | 450,058 | 8.9% | context stored for reuse (~1.25× input price) |
| cache read | 4,547,374 | 90.0% | context replayed from cache (~0.1× input price) |
| **total** | **5,049,998** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~39.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,710 | 20,856 | 450k | 4.5M | 5,049,998 |
**Total: 5,049,998 tokens · $2.04 · 0.6h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.93 | 20,346 | 212k | 2.0M | 89.9% |
| test-automation-engineer | $0.78 | 18,906 | 156k | 2.1M | 92.7% |
| qa-engineer | $0.33 | 13,314 | 83k | 459k | 83.1% |

## Orchestrator (lead thread) composition

Lead: $0.93 — overhead incl. stages is 46% of the batch · real work 20,346 · cache 2.0M read / 212k write · hit rate 89.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2448 | $1.11 | 20,869 | 11,351 | 238k | 2.6M | 2,831,221 | 90.8% | 56.1% |
