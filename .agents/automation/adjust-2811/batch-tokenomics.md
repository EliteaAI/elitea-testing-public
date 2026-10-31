# Batch tokenomics — adjust-2811

Generated: 2026-10-31T08:26:24.539Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,299 | 0.7% | fresh prompt tokens, full price |
| real work: output | 12,953 | 0.4% | generated tokens — the most expensive kind |
| cache write | 241,387 | 8.1% | context stored for reuse (~1.25× input price) |
| cache read | 2,715,090 | 90.8% | context replayed from cache (~0.1× input price) |
| **total** | **2,990,729** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~41.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,299 | 12,953 | 241k | 2.7M | 2,990,729 |
**Total: 2,990,729 tokens · $1.15 · 0.1h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.73 | 20,985 | 122k | 2.4M | 94.7% |
| qa-engineer | $0.42 | 13,267 | 119k | 327k | 71.6% |

## Orchestrator (lead thread) composition

Lead: $0.73 — overhead incl. stages is 64% of the batch · real work 20,985 · cache 2.4M read / 122k write · hit rate 94.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2035 | $0.42 | 10,485 | 2,782 | 119k | 327k | 459,202 | 71.6% | 15.4% |
