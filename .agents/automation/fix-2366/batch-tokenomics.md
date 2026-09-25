# Batch tokenomics — fix-2366

Generated: 2026-09-18T14:28:07.915Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 424 | 0.0% | fresh prompt tokens, full price |
| real work: output | 214,749 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,086,844 | 2.3% | context stored for reuse (~1.25× input price) |
| cache read | 45,246,158 | 97.2% | context replayed from cache (~0.1× input price) |
| **total** | **46,548,175** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 97.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~87.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~65% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 424 | 214,749 | 1.1M | 45.2M | 46,548,175 |
**Total: 46,548,175 tokens · $35.85 · 1.4h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $17.01 | 112,823 | 469k | 22.5M | 98.0% |
| test-automation-lead | $14.36 | 65,939 | 282k | 19.8M | 98.6% |
| qa-engineer | $4.47 | 36,411 | 336k | 2.9M | 89.7% |

## Orchestrator (lead thread) composition

Lead: $14.36 — overhead incl. stages is 40% of the batch · real work 65,939 · cache 19.8M read / 282k write · hit rate 98.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2056 | $21.48 | 248 | 148,986 | 804k | 25.5M | 26,414,667 | 96.9% | 56.7% |
