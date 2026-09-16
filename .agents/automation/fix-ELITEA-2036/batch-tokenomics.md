# Batch tokenomics — fix-ELITEA-2036

Generated: 2026-09-16T21:15:02.022Z  ·  sessions: 2  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 68 | 0.0% | fresh prompt tokens, full price |
| real work: output | 29,614 | 0.6% | generated tokens — the most expensive kind |
| cache write | 312,486 | 5.9% | context stored for reuse (~1.25× input price) |
| cache read | 4,933,959 | 93.5% | context replayed from cache (~0.1× input price) |
| **total** | **5,276,127** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~47.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 68 | 29,614 | 312k | 4.9M | 5,276,127 |
**Total: 5,276,127 tokens · $6.33 · 0.1h active · 0 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $6.33 | 29,682 | 312k | 4.9M | 94.0% |

## Orchestrator (lead thread) composition

Lead: $6.33 — overhead incl. stages is 100% of the batch · real work 29,682 · cache 4.9M read / 312k write · hit rate 94.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

