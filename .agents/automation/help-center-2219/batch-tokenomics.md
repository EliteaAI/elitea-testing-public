# Batch tokenomics — help-center-2219

Generated: 2026-09-30T16:47:46.930Z  ·  sessions: 1  ·  models: —  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 48,192 | 0.1% | fresh prompt tokens, full price |
| real work: output | 224,363 | 0.6% | generated tokens — the most expensive kind |
| cache write | 1,149,038 | 3.2% | context stored for reuse (~1.25× input price) |
| cache read | 34,876,244 | 96.1% | context replayed from cache (~0.1× input price) |
| **total** | **36,297,837** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 96.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~86.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~57.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 48,192 | 224,363 | 1.1M | 34.9M | 36,297,837 |
**Total: 36,297,837 tokens · $30.47 · 1.2h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $17.14 | 154,018 | 510k | 21.5M | 97.5% |
| qa-engineer | $13.32 | 118,537 | 639k | 13.3M | 95.3% |
| session | $0.00 | 0 | 0 | 0 | n/a |

## Orchestrator (lead thread) composition

Lead: $0.00 — overhead incl. stages is 0% of the batch · real work 0 · cache 0 read / 0 write · hit rate n/a
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2219 | $30.47 | 48,192 | 224,363 | 1.1M | 34.9M | 36,297,837 | 96.7% | 100.0% |
