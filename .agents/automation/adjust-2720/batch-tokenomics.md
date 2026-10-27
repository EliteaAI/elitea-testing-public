# Batch tokenomics — adjust-2720

Generated: 2026-10-27T06:18:07.378Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 42,372 | 0.5% | fresh prompt tokens, full price |
| real work: output | 39,532 | 0.4% | generated tokens — the most expensive kind |
| cache write | 563,887 | 6.3% | context stored for reuse (~1.25× input price) |
| cache read | 8,267,948 | 92.8% | context replayed from cache (~0.1× input price) |
| **total** | **8,913,739** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 42,372 | 39,532 | 564k | 8.3M | 8,913,739 |
**Total: 8,913,739 tokens · $2.99 · 0.9h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.43 | 30,819 | 249k | 4.6M | 94.6% |
| test-automation-engineer | $1.22 | 37,386 | 227k | 3.3M | 93.1% |
| qa-engineer | $0.34 | 13,699 | 89k | 355k | 78.2% |

## Orchestrator (lead thread) composition

Lead: $1.43 — overhead incl. stages is 59% of the batch · real work 30,819 · cache 4.6M read / 249k write · hit rate 94.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| other | $0.34 | 13,699 | 89k | 355k | 78.2% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2007 | $0.29 | 3,461 | 4,357 | 47k | 916k | 970,851 | 94.7% | 10.9% |
| ELITEA-2042 | $0.29 | 3,461 | 4,357 | 47k | 916k | 970,851 | 94.7% | 10.9% |
| ELITEA-2045 | $0.65 | 13,811 | 7,939 | 132k | 1.5M | 1,669,854 | 91.2% | 18.7% |
