# Batch tokenomics — adjust-2568

Generated: 2026-10-23T04:05:14.285Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,624 | 0.4% | fresh prompt tokens, full price |
| real work: output | 20,298 | 0.4% | generated tokens — the most expensive kind |
| cache write | 238,819 | 4.2% | context stored for reuse (~1.25× input price) |
| cache read | 5,366,369 | 95.0% | context replayed from cache (~0.1× input price) |
| **total** | **5,647,110** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~56% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,624 | 20,298 | 239k | 5.4M | 5,647,110 |
**Total: 5,647,110 tokens · $1.52 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.11 | 28,718 | 123k | 5.0M | 97.4% |
| qa-engineer | $0.41 | 13,204 | 116k | 321k | 71.8% |

## Orchestrator (lead thread) composition

Lead: $1.11 — overhead incl. stages is 73% of the batch · real work 28,718 · cache 5.0M read / 123k write · hit rate 97.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2030 | $0.41 | 10,497 | 2,707 | 116k | 321k | 449,546 | 71.8% | 8.0% |
