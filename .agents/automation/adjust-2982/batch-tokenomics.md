# Batch tokenomics — adjust-2982

Generated: 2026-11-18T18:22:25.222Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 34,236 | 0.5% | fresh prompt tokens, full price |
| real work: output | 24,124 | 0.4% | generated tokens — the most expensive kind |
| cache write | 535,708 | 8.0% | context stored for reuse (~1.25× input price) |
| cache read | 6,092,845 | 91.1% | context replayed from cache (~0.1× input price) |
| **total** | **6,686,913** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 34,236 | 24,124 | 536k | 6.1M | 6,686,913 |
**Total: 6,686,913 tokens · $2.48 · 0.5h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.29 | 24,906 | 296k | 2.9M | 90.3% |
| test-automation-engineer | $0.90 | 20,963 | 158k | 3.0M | 94.7% |
| qa-engineer | $0.30 | 12,491 | 82k | 238k | 72.0% |

## Orchestrator (lead thread) composition

Lead: $1.29 — overhead incl. stages is 52% of the batch · real work 24,906 · cache 2.9M read / 296k write · hit rate 90.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2017 | $0.60 | 10,525 | 6,202 | 120k | 1.6M | 1,745,769 | 92.5% | 26.1% |
| ELITEA-2058 | $0.60 | 10,525 | 6,202 | 120k | 1.6M | 1,745,769 | 92.5% | 26.1% |
