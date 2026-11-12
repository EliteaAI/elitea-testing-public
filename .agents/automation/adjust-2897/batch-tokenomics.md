# Batch tokenomics — adjust-2897

Generated: 2026-11-09T13:56:52.073Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,779 | 0.3% | fresh prompt tokens, full price |
| real work: output | 34,884 | 0.4% | generated tokens — the most expensive kind |
| cache write | 679,222 | 7.4% | context stored for reuse (~1.25× input price) |
| cache read | 8,410,315 | 91.9% | context replayed from cache (~0.1× input price) |
| **total** | **9,156,200** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,779 | 34,884 | 679k | 8.4M | 9,156,200 |
**Total: 9,156,200 tokens · $3.27 · 0.9h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.80 | 33,252 | 322k | 5.8M | 94.6% |
| test-automation-lead | $1.11 | 19,209 | 269k | 2.1M | 88.4% |
| qa-engineer | $0.36 | 14,202 | 89k | 473k | 82.7% |

## Orchestrator (lead thread) composition

Lead: $1.11 — overhead incl. stages is 34% of the batch · real work 19,209 · cache 2.1M read / 269k write · hit rate 88.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2440 | $0.90 | 5,213 | 11,413 | 161k | 2.9M | 3,080,527 | 94.6% | 33.6% |
| ELITEA-2442 | $1.26 | 15,707 | 15,121 | 249k | 3.4M | 3,655,904 | 92.7% | 39.9% |
