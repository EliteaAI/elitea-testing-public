# Batch tokenomics — adjust-3750

Generated: 2026-10-25T07:31:28.019Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 23,634 | 0.5% | fresh prompt tokens, full price |
| real work: output | 16,317 | 0.4% | generated tokens — the most expensive kind |
| cache write | 229,707 | 5.2% | context stored for reuse (~1.25× input price) |
| cache read | 4,166,847 | 93.9% | context replayed from cache (~0.1× input price) |
| **total** | **4,436,505** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~51.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 23,634 | 16,317 | 230k | 4.2M | 4,436,505 |
**Total: 4,436,505 tokens · $1.32 · 0.2h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 24,706 | 102k | 3.8M | 97.1% |
| qa-engineer | $0.45 | 15,245 | 127k | 339k | 70.8% |

## Orchestrator (lead thread) composition

Lead: $0.88 — overhead incl. stages is 66% of the batch · real work 24,706 · cache 3.8M read / 102k write · hit rate 97.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | $0.45 | 12,389 | 2,856 | 127k | 339k | 481,796 | 70.8% | 10.9% |
