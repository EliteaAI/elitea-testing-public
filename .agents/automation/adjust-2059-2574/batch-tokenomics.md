# Batch tokenomics — adjust-2059-2574

Generated: 2026-10-23T05:47:26.841Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 33,101 | 0.3% | fresh prompt tokens, full price |
| real work: output | 40,271 | 0.4% | generated tokens — the most expensive kind |
| cache write | 516,428 | 4.7% | context stored for reuse (~1.25× input price) |
| cache read | 10,458,818 | 94.7% | context replayed from cache (~0.1× input price) |
| **total** | **11,048,618** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~54.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 33,101 | 40,271 | 516k | 10.5M | 11,048,618 |
**Total: 11,048,618 tokens · $3.09 · 0.8h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.69 | 34,668 | 266k | 6.2M | 95.7% |
| test-automation-engineer | $0.98 | 23,511 | 149k | 3.7M | 95.9% |
| qa-engineer | $0.41 | 15,193 | 101k | 504k | 81.8% |

## Orchestrator (lead thread) composition

Lead: $1.69 — overhead incl. stages is 55% of the batch · real work 34,668 · cache 6.2M read / 266k write · hit rate 95.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2059 | $1.39 | 20,898 | 17,806 | 250k | 4.2M | 4,504,356 | 94.0% | 40.8% |
