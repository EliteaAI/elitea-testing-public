# Batch tokenomics — fix-2321

Generated: 2026-09-16T14:36:02.980Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 146 | 0.0% | fresh prompt tokens, full price |
| real work: output | 70,572 | 0.6% | generated tokens — the most expensive kind |
| cache write | 539,010 | 4.2% | context stored for reuse (~1.25× input price) |
| cache read | 12,196,696 | 95.2% | context replayed from cache (~0.1× input price) |
| **total** | **12,806,424** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~54.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 146 | 70,572 | 539k | 12.2M | 12,806,424 |
**Total: 12,806,424 tokens · $12.01 · 0.5h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $6.71 | 34,288 | 208k | 7.6M | 97.3% |
| test-automation-engineer | $3.28 | 19,941 | 171k | 3.4M | 95.2% |
| qa-engineer | $2.01 | 16,489 | 160k | 1.2M | 88.4% |

## Orchestrator (lead thread) composition

Lead: $6.71 — overhead incl. stages is 56% of the batch · real work 34,288 · cache 7.6M read / 208k write · hit rate 97.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2056 | $5.30 | 64 | 36,366 | 331k | 4.6M | 5,011,466 | 93.3% | 39.1% |
