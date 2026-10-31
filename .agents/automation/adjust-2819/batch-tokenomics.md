# Batch tokenomics — adjust-2819

Generated: 2026-10-31T10:19:49.413Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 33,500 | 0.8% | fresh prompt tokens, full price |
| real work: output | 19,266 | 0.5% | generated tokens — the most expensive kind |
| cache write | 334,010 | 7.9% | context stored for reuse (~1.25× input price) |
| cache read | 3,839,366 | 90.8% | context replayed from cache (~0.1× input price) |
| **total** | **4,226,142** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~41.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 33,500 | 19,266 | 334k | 3.8M | 4,226,142 |
**Total: 4,226,142 tokens · $1.63 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.74 | 23,633 | 97k | 2.8M | 96.3% |
| test-automation-engineer | $0.53 | 14,168 | 140k | 768k | 83.7% |
| qa-engineer | $0.35 | 14,965 | 98k | 247k | 69.1% |

## Orchestrator (lead thread) composition

Lead: $0.74 — overhead incl. stages is 46% of the batch · real work 23,633 · cache 2.8M read / 97k write · hit rate 96.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2357 | $0.88 | 22,747 | 6,386 | 237k | 1.0M | 1,281,470 | 79.6% | 30.3% |
