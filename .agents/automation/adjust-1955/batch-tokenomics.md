# Batch tokenomics — adjust-1955

Generated: 2026-11-12T07:14:10.677Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,885 | 0.4% | fresh prompt tokens, full price |
| real work: output | 38,848 | 0.5% | generated tokens — the most expensive kind |
| cache write | 688,311 | 8.2% | context stored for reuse (~1.25× input price) |
| cache read | 7,586,422 | 90.9% | context replayed from cache (~0.1× input price) |
| **total** | **8,346,466** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~41.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,885 | 38,848 | 688k | 7.6M | 8,346,466 |
**Total: 8,346,466 tokens · $3.23 · 0.5h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.76 | 28,709 | 423k | 3.5M | 88.9% |
| test-automation-engineer | $1.05 | 27,383 | 164k | 3.5M | 95.2% |
| qa-engineer | $0.43 | 15,641 | 101k | 622k | 84.8% |

## Orchestrator (lead thread) composition

Lead: $1.76 — overhead incl. stages is 54% of the batch · real work 28,709 · cache 3.5M read / 423k write · hit rate 88.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1955 | $1.47 | 20,961 | 22,063 | 265k | 4.1M | 4,422,391 | 93.5% | 53.0% |
