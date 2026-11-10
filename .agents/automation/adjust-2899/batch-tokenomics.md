# Batch tokenomics — adjust-2899

Generated: 2026-11-10T13:56:16.222Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 54,429 | 0.3% | fresh prompt tokens, full price |
| real work: output | 63,882 | 0.4% | generated tokens — the most expensive kind |
| cache write | 2,861,310 | 16.4% | context stored for reuse (~1.25× input price) |
| cache read | 14,471,527 | 82.9% | context replayed from cache (~0.1× input price) |
| **total** | **17,451,148** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 83.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~70.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~26.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 54,429 | 63,882 | 2.9M | 14.5M | 17,451,148 |
**Total: 17,451,148 tokens · $10.31 · 3.0h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $7.12 | 39,892 | 2.2M | 6.1M | 73.1% |
| test-automation-engineer | $2.73 | 63,000 | 547k | 7.4M | 92.8% |
| qa-engineer | $0.47 | 15,419 | 101k | 991k | 89.9% |

## Orchestrator (lead thread) composition

Lead: $7.12 — overhead incl. stages is 79% of the batch · real work 39,892 · cache 6.1M read / 2.2M write · hit rate 73.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.65 | 17,648 | 138k | 1.5M | 91.2% |
| other | $0.41 | 13,994 | 91k | 864k | 89.5% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2352 | $2.14 | 21,906 | 24,871 | 419k | 6.0M | 6,480,144 | 93.2% | 37.1% |
