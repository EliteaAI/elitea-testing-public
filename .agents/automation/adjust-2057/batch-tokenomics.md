# Batch tokenomics — adjust-2057

Generated: 2026-10-24T05:19:01.629Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,750 | 0.5% | fresh prompt tokens, full price |
| real work: output | 28,094 | 0.4% | generated tokens — the most expensive kind |
| cache write | 329,962 | 5.1% | context stored for reuse (~1.25× input price) |
| cache read | 6,110,301 | 94.0% | context replayed from cache (~0.1× input price) |
| **total** | **6,501,107** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~51.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,750 | 28,094 | 330k | 6.1M | 6,501,107 |
**Total: 6,501,107 tokens · $1.99 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.95 | 24,186 | 112k | 4.0M | 97.0% |
| test-automation-engineer | $0.71 | 22,584 | 133k | 1.7M | 92.3% |
| qa-engineer | $0.33 | 14,074 | 85k | 350k | 78.6% |

## Orchestrator (lead thread) composition

Lead: $0.95 — overhead incl. stages is 48% of the batch · real work 24,186 · cache 4.0M read / 112k write · hit rate 97.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2057 | $1.04 | 20,864 | 15,794 | 217k | 2.1M | 2,319,367 | 89.7% | 35.7% |
