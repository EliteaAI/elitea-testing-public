# Batch tokenomics — adjust-2942

Generated: 2026-11-12T15:56:07.111Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 42,695 | 0.2% | fresh prompt tokens, full price |
| real work: output | 74,590 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,329,164 | 7.2% | context stored for reuse (~1.25× input price) |
| cache read | 16,926,889 | 92.1% | context replayed from cache (~0.1× input price) |
| **total** | **18,373,338** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 42,695 | 74,590 | 1.3M | 16.9M | 18,373,338 |
**Total: 18,373,338 tokens · $6.43 · 1.4h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $3.23 | 33,956 | 886k | 4.7M | 83.9% |
| test-automation-engineer | $2.77 | 67,362 | 347k | 11.4M | 96.9% |
| qa-engineer | $0.44 | 15,967 | 96k | 838k | 88.7% |

## Orchestrator (lead thread) composition

Lead: $3.23 — overhead incl. stages is 50% of the batch · real work 33,956 · cache 4.7M read / 886k write · hit rate 83.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2010 | $1.07 | 10,527 | 17,250 | 148k | 4.1M | 4,260,364 | 96.3% | 23.2% |
| ELITEA-2065 | $1.07 | 10,527 | 17,250 | 148k | 4.1M | 4,260,364 | 96.3% | 23.2% |
| ELITEA-2036 | $1.07 | 10,527 | 17,250 | 148k | 4.1M | 4,260,364 | 96.3% | 23.2% |
