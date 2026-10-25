# Batch tokenomics — adjust-elitea-2011

Generated: 2026-10-25T05:11:46.375Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,319 | 0.6% | fresh prompt tokens, full price |
| real work: output | 14,069 | 0.4% | generated tokens — the most expensive kind |
| cache write | 238,578 | 6.5% | context stored for reuse (~1.25× input price) |
| cache read | 3,373,740 | 92.5% | context replayed from cache (~0.1× input price) |
| **total** | **3,647,706** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~46.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,319 | 14,069 | 239k | 3.4M | 3,647,706 |
**Total: 3,647,706 tokens · $1.23 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.84 | 22,917 | 125k | 3.1M | 95.7% |
| qa-engineer | $0.39 | 12,471 | 114k | 320k | 72.0% |

## Orchestrator (lead thread) composition

Lead: $0.84 — overhead incl. stages is 68% of the batch · real work 22,917 · cache 3.1M read / 125k write · hit rate 95.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2011 | $0.39 | 10,498 | 1,973 | 114k | 320k | 445,867 | 72.0% | 12.2% |
