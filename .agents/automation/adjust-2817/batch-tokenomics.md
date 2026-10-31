# Batch tokenomics — adjust-2817

Generated: 2026-10-31T09:41:21.623Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,648 | 0.9% | fresh prompt tokens, full price |
| real work: output | 14,383 | 0.4% | generated tokens — the most expensive kind |
| cache write | 322,329 | 9.4% | context stored for reuse (~1.25× input price) |
| cache read | 3,061,204 | 89.3% | context replayed from cache (~0.1× input price) |
| **total** | **3,429,564** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~37.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,648 | 14,383 | 322k | 3.1M | 3,429,564 |
**Total: 3,429,564 tokens · $1.48 · 0.2h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.65 | 19,651 | 91k | 2.3M | 95.8% |
| test-automation-engineer | $0.51 | 13,521 | 145k | 502k | 76.3% |
| qa-engineer | $0.31 | 12,859 | 86k | 239k | 71.3% |

## Orchestrator (lead thread) composition

Lead: $0.65 — overhead incl. stages is 44% of the batch · real work 19,651 · cache 2.3M read / 91k write · hit rate 95.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | $0.82 | 20,840 | 5,540 | 231k | 741k | 998,552 | 74.6% | 29.1% |
