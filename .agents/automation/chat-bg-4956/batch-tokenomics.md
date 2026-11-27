# Batch tokenomics — chat-bg-4956

Generated: 2026-11-27T12:48:48.435Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 76,615 | 0.6% | fresh prompt tokens, full price |
| real work: output | 57,211 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,707,876 | 14.3% | context stored for reuse (~1.25× input price) |
| cache read | 10,100,319 | 84.6% | context replayed from cache (~0.1× input price) |
| **total** | **11,942,021** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~72.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~28.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 76,615 | 57,211 | 1.7M | 10.1M | 11,942,021 |
**Total: 11,942,021 tokens · $6.02 · 1.1h active · 7 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.41 | 63,435 | 632k | 4.7M | 87.6% |
| test-automation-lead | $1.98 | 21,948 | 683k | 1.6M | 69.4% |
| qa-engineer | $1.63 | 48,443 | 393k | 3.8M | 90.0% |

## Orchestrator (lead thread) composition

Lead: $1.98 — overhead incl. stages is 59% of the batch · real work 21,948 · cache 1.6M read / 683k write · hit rate 69.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.30 | 9,309 | 109k | 99k | 45.6% |
| gate | $0.89 | 14,758 | 252k | 1.8M | 87.5% |
| report | $0.37 | 12,626 | 117k | 217k | 63.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4956 | $2.47 | 35,179 | 40,006 | 547k | 6.4M | 6,988,404 | 91.6% | 58.5% |
