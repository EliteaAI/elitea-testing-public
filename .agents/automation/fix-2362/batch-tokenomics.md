# Batch tokenomics — fix-2362

Generated: 2026-09-18T13:00:25.174Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 240 | 0.0% | fresh prompt tokens, full price |
| real work: output | 118,191 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,133,125 | 4.9% | context stored for reuse (~1.25× input price) |
| cache read | 21,857,750 | 94.6% | context replayed from cache (~0.1× input price) |
| **total** | **23,109,306** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~52.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 240 | 118,191 | 1.1M | 21.9M | 23,109,306 |
**Total: 23,109,306 tokens · $21.78 · 1.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $11.22 | 57,200 | 732k | 10.4M | 93.4% |
| test-automation-lead | $7.54 | 41,004 | 217k | 8.7M | 97.6% |
| qa-engineer | $3.01 | 20,227 | 184k | 2.7M | 93.6% |

## Orchestrator (lead thread) composition

Lead: $7.54 — overhead incl. stages is 35% of the batch · real work 41,004 · cache 8.7M read / 217k write · hit rate 97.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1140 | $14.24 | 146 | 77,281 | 916k | 13.2M | 14,147,324 | 93.5% | 61.2% |
