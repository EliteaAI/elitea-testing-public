# Batch tokenomics — fix-2653

Generated: 2026-10-24T05:52:47.641Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,791 | 0.5% | fresh prompt tokens, full price |
| real work: output | 27,919 | 0.4% | generated tokens — the most expensive kind |
| cache write | 524,365 | 8.0% | context stored for reuse (~1.25× input price) |
| cache read | 6,011,303 | 91.1% | context replayed from cache (~0.1× input price) |
| **total** | **6,595,378** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,791 | 27,919 | 524k | 6.0M | 6,595,378 |
**Total: 6,595,378 tokens · $2.48 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.31 | 26,659 | 253k | 3.8M | 93.5% |
| test-automation-engineer | $0.77 | 18,768 | 163k | 1.8M | 91.4% |
| qa-engineer | $0.41 | 14,283 | 109k | 391k | 76.7% |

## Orchestrator (lead thread) composition

Lead: $1.31 — overhead incl. stages is 53% of the batch · real work 26,659 · cache 3.8M read / 253k write · hit rate 93.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2014 | $0.59 | 10,436 | 6,090 | 136k | 1.1M | 1,265,757 | 88.4% | 19.2% |
| ELITEA-2036 | $0.59 | 10,436 | 6,090 | 136k | 1.1M | 1,265,757 | 88.4% | 19.2% |
