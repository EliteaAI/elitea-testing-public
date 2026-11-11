# Batch tokenomics — adjust-2876-midturn-precondition

Generated: 2026-11-11T18:44:20.361Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 52,943 | 0.7% | fresh prompt tokens, full price |
| real work: output | 38,735 | 0.5% | generated tokens — the most expensive kind |
| cache write | 503,814 | 6.4% | context stored for reuse (~1.25× input price) |
| cache read | 7,228,825 | 92.4% | context replayed from cache (~0.1× input price) |
| **total** | **7,824,317** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 52,943 | 38,735 | 504k | 7.2M | 7,824,317 |
**Total: 7,824,317 tokens · $2.72 · 0.4h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.03 | 33,723 | 217k | 2.2M | 90.3% |
| test-automation-lead | $0.94 | 28,860 | 110k | 3.8M | 96.9% |
| qa-engineer | $0.76 | 29,095 | 177k | 1.2M | 86.0% |

## Orchestrator (lead thread) composition

Lead: $0.94 — overhead incl. stages is 35% of the batch · real work 28,860 · cache 3.8M read / 110k write · hit rate 96.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2876 | $1.78 | 41,856 | 20,962 | 394k | 3.4M | 3,889,386 | 88.7% | 49.7% |
