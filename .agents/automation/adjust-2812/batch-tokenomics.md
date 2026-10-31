# Batch tokenomics — adjust-2812

Generated: 2026-10-31T08:46:17.857Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,759 | 0.7% | fresh prompt tokens, full price |
| real work: output | 18,570 | 0.4% | generated tokens — the most expensive kind |
| cache write | 324,707 | 7.0% | context stored for reuse (~1.25× input price) |
| cache read | 4,237,751 | 91.9% | context replayed from cache (~0.1× input price) |
| **total** | **4,612,787** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.4% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,759 | 18,570 | 325k | 4.2M | 4,612,787 |
**Total: 4,612,787 tokens · $1.66 · 0.2h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 23,173 | 110k | 3.5M | 96.7% |
| test-automation-engineer | $0.46 | 14,520 | 125k | 470k | 77.6% |
| qa-engineer | $0.32 | 12,636 | 90k | 238k | 70.3% |

## Orchestrator (lead thread) composition

Lead: $0.88 — overhead incl. stages is 53% of the batch · real work 23,173 · cache 3.5M read / 110k write · hit rate 96.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2046 | $0.78 | 20,847 | 6,309 | 215k | 707k | 949,345 | 75.0% | 20.6% |
