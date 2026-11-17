# Batch tokenomics — adjust-elitea-3370

Generated: 2026-11-17T17:01:09.123Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,443 | 0.5% | fresh prompt tokens, full price |
| real work: output | 14,358 | 0.3% | generated tokens — the most expensive kind |
| cache write | 269,252 | 6.4% | context stored for reuse (~1.25× input price) |
| cache read | 3,894,747 | 92.7% | context replayed from cache (~0.1× input price) |
| **total** | **4,199,800** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~47.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,443 | 14,358 | 269k | 3.9M | 4,199,800 |
**Total: 4,199,800 tokens · $1.40 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.01 | 22,225 | 154k | 3.7M | 95.7% |
| qa-engineer | $0.40 | 13,576 | 115k | 208k | 62.4% |

## Orchestrator (lead thread) composition

Lead: $1.01 — overhead incl. stages is 72% of the batch · real work 22,225 · cache 3.7M read / 154k write · hit rate 95.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3370 | $0.40 | 10,527 | 3,049 | 115k | 208k | 336,773 | 62.4% | 8.0% |
