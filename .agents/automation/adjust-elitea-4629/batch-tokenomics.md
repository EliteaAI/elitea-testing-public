# Batch tokenomics — adjust-elitea-4629

Generated: 2026-11-13T11:32:03.618Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,672 | 0.6% | fresh prompt tokens, full price |
| real work: output | 12,722 | 0.4% | generated tokens — the most expensive kind |
| cache write | 249,625 | 6.9% | context stored for reuse (~1.25× input price) |
| cache read | 3,315,112 | 92.1% | context replayed from cache (~0.1× input price) |
| **total** | **3,599,131** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,672 | 12,722 | 250k | 3.3M | 3,599,131 |
**Total: 3,599,131 tokens · $1.24 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.82 | 21,078 | 133k | 2.9M | 95.2% |
| qa-engineer | $0.42 | 13,316 | 116k | 437k | 77.5% |

## Orchestrator (lead thread) composition

Lead: $0.82 — overhead incl. stages is 66% of the batch · real work 21,078 · cache 2.9M read / 133k write · hit rate 95.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4629 | $0.42 | 10,534 | 2,782 | 116k | 437k | 566,430 | 77.5% | 15.7% |
