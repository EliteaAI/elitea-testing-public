# Batch tokenomics — adjust-2866

Generated: 2026-11-03T06:11:56.032Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,835 | 0.5% | fresh prompt tokens, full price |
| real work: output | 22,546 | 0.4% | generated tokens — the most expensive kind |
| cache write | 759,966 | 12.2% | context stored for reuse (~1.25× input price) |
| cache read | 5,408,994 | 86.9% | context replayed from cache (~0.1× input price) |
| **total** | **6,223,341** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~75.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~33.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,835 | 22,546 | 760k | 5.4M | 6,223,341 |
**Total: 6,223,341 tokens · $3.00 · 0.8h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.41 | 23,712 | 300k | 3.9M | 92.6% |
| test-automation-engineer | $1.25 | 17,301 | 375k | 1.1M | 73.4% |
| qa-engineer | $0.34 | 13,368 | 85k | 468k | 83.0% |

## Orchestrator (lead thread) composition

Lead: $1.41 — overhead incl. stages is 47% of the batch · real work 23,712 · cache 3.9M read / 300k write · hit rate 92.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1891 | $0.79 | 10,429 | 4,906 | 230k | 767k | 1,012,832 | 76.1% | 16.3% |
| ELITEA-1892 | $0.79 | 10,429 | 4,906 | 230k | 767k | 1,012,832 | 76.1% | 16.3% |
