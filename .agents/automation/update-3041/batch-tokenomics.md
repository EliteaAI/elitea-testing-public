# Batch tokenomics — update-3041

Generated: 2026-11-26T15:57:11.480Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,403 | 0.5% | fresh prompt tokens, full price |
| real work: output | 17,679 | 0.3% | generated tokens — the most expensive kind |
| cache write | 474,331 | 7.7% | context stored for reuse (~1.25× input price) |
| cache read | 5,620,356 | 91.5% | context replayed from cache (~0.1× input price) |
| **total** | **6,144,769** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,403 | 17,679 | 474k | 5.6M | 6,144,769 |
**Total: 6,144,769 tokens · $2.01 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $0.90 | 19,631 | 159k | 3.9M | 95.9% |
| test-automation-lead | $0.81 | 16,853 | 231k | 1.3M | 84.6% |
| qa-engineer | $0.30 | 13,598 | 85k | 357k | 78.9% |

## Orchestrator (lead thread) composition

Lead: $0.81 — overhead incl. stages is 40% of the batch · real work 16,853 · cache 1.3M read / 231k write · hit rate 84.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1794 | $0.60 | 10,706 | 5,909 | 122k | 2.1M | 2,282,201 | 94.2% | 37.1% |
| ELITEA-1896 | $0.60 | 10,706 | 5,909 | 122k | 2.1M | 2,282,201 | 94.2% | 37.1% |
