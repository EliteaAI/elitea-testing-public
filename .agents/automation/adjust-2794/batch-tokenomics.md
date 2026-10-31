# Batch tokenomics — adjust-2794

Generated: 2026-10-31T03:51:34.220Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,746 | 0.3% | fresh prompt tokens, full price |
| real work: output | 29,068 | 0.4% | generated tokens — the most expensive kind |
| cache write | 321,685 | 4.2% | context stored for reuse (~1.25× input price) |
| cache read | 7,348,101 | 95.2% | context replayed from cache (~0.1× input price) |
| **total** | **7,720,600** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~56.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,746 | 29,068 | 322k | 7.3M | 7,720,600 |
**Total: 7,720,600 tokens · $2.06 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.59 | 35,774 | 196k | 6.9M | 97.1% |
| qa-engineer | $0.47 | 15,040 | 125k | 454k | 77.0% |

## Orchestrator (lead thread) composition

Lead: $1.59 — overhead incl. stages is 77% of the batch · real work 35,774 · cache 6.9M read / 196k write · hit rate 97.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2038 | $0.47 | 10,491 | 4,549 | 125k | 454k | 594,687 | 77.0% | 7.7% |
