# Batch tokenomics — fix-2287-elitea-1901

Generated: 2026-09-14T21:09:57.325Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 134 | 0.0% | fresh prompt tokens, full price |
| real work: output | 53,172 | 0.5% | generated tokens — the most expensive kind |
| cache write | 498,705 | 4.2% | context stored for reuse (~1.25× input price) |
| cache read | 11,190,196 | 95.3% | context replayed from cache (~0.1× input price) |
| **total** | **11,742,207** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~55.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 134 | 53,172 | 499k | 11.2M | 11,742,207 |
**Total: 11,742,207 tokens · $10.80 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $7.37 | 40,467 | 203k | 8.7M | 97.7% |
| test-automation-engineer | $3.43 | 12,839 | 296k | 2.5M | 89.5% |

## Orchestrator (lead thread) composition

Lead: $7.37 — overhead incl. stages is 68% of the batch · real work 40,467 · cache 8.7M read / 203k write · hit rate 97.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1901 | $3.43 | 40 | 12,799 | 296k | 2.5M | 2,833,892 | 89.5% | 24.1% |
