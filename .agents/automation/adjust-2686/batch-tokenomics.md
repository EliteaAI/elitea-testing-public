# Batch tokenomics — adjust-2686

Generated: 2026-10-25T09:41:53.094Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,642 | 0.7% | fresh prompt tokens, full price |
| real work: output | 17,122 | 0.4% | generated tokens — the most expensive kind |
| cache write | 330,439 | 7.8% | context stored for reuse (~1.25× input price) |
| cache read | 3,850,369 | 91.0% | context replayed from cache (~0.1× input price) |
| **total** | **4,229,572** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,642 | 17,122 | 330k | 3.9M | 4,229,572 |
**Total: 4,229,572 tokens · $1.61 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.74 | 21,231 | 96k | 2.8M | 96.4% |
| test-automation-engineer | $0.54 | 14,555 | 146k | 649k | 80.6% |
| qa-engineer | $0.33 | 12,978 | 88k | 353k | 78.2% |

## Orchestrator (lead thread) composition

Lead: $0.74 — overhead incl. stages is 46% of the batch · real work 21,231 · cache 2.8M read / 96k write · hit rate 96.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2378 | $0.87 | 20,845 | 6,688 | 234k | 1.0M | 1,263,901 | 79.7% | 29.9% |
