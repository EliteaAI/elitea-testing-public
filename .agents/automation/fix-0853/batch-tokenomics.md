# Batch tokenomics — fix-0853

Generated: 2026-10-25T04:33:56.127Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,402 | 0.8% | fresh prompt tokens, full price |
| real work: output | 14,851 | 0.5% | generated tokens — the most expensive kind |
| cache write | 203,569 | 7.4% | context stored for reuse (~1.25× input price) |
| cache read | 2,506,283 | 91.3% | context replayed from cache (~0.1× input price) |
| **total** | **2,746,105** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~41.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,402 | 14,851 | 204k | 2.5M | 2,746,105 |
**Total: 2,746,105 tokens · $1.05 · 0.1h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.64 | 23,225 | 88k | 2.2M | 95.7% |
| qa-engineer | $0.40 | 13,028 | 115k | 323k | 71.9% |

## Orchestrator (lead thread) composition

Lead: $0.64 — overhead incl. stages is 61% of the batch · real work 23,225 · cache 2.2M read / 88k write · hit rate 95.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0853 | $0.40 | 10,494 | 2,534 | 115k | 323k | 451,058 | 71.9% | 16.4% |
