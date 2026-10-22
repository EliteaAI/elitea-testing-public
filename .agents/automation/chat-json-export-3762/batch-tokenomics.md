# Batch tokenomics — chat-json-export-3762

Generated: 2026-10-22T05:46:43.609Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 74,526 | 0.8% | fresh prompt tokens, full price |
| real work: output | 40,415 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,608,294 | 17.4% | context stored for reuse (~1.25× input price) |
| cache read | 7,519,970 | 81.4% | context replayed from cache (~0.1× input price) |
| **total** | **9,243,205** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 81.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~69.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~24.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 74,526 | 40,415 | 1.6M | 7.5M | 9,243,205 |
**Total: 9,243,205 tokens · $5.86 · 0.6h active · 7 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.29 | 52,023 | 593k | 3.5M | 84.7% |
| test-automation-lead | $2.20 | 24,566 | 657k | 2.3M | 77.4% |
| qa-engineer | $1.37 | 38,352 | 358k | 1.7M | 81.9% |

## Orchestrator (lead thread) composition

Lead: $2.20 — overhead incl. stages is 61% of the batch · real work 24,566 · cache 2.3M read / 657k write · hit rate 77.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.33 | 9,009 | 108k | 97k | 45.5% |
| gate | $0.61 | 13,550 | 120k | 1.8M | 93.5% |
| report | $0.42 | 13,801 | 116k | 214k | 63.3% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3762 | $2.30 | 34,146 | 19,869 | 608k | 3.1M | 3,728,705 | 82.7% | 40.3% |
