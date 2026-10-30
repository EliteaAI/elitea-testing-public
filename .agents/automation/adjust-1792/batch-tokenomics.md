# Batch tokenomics — adjust-1792

Generated: 2026-10-25T06:38:46.273Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,503 | 0.7% | fresh prompt tokens, full price |
| real work: output | 12,549 | 0.4% | generated tokens — the most expensive kind |
| cache write | 210,929 | 6.8% | context stored for reuse (~1.25× input price) |
| cache read | 2,867,230 | 92.1% | context replayed from cache (~0.1× input price) |
| **total** | **3,112,211** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,503 | 12,549 | 211k | 2.9M | 3,112,211 |
**Total: 3,112,211 tokens · $1.08 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.69 | 21,634 | 98k | 2.5M | 95.9% |
| qa-engineer | $0.39 | 12,418 | 113k | 318k | 72.0% |

## Orchestrator (lead thread) composition

Lead: $0.69 — overhead incl. stages is 64% of the batch · real work 21,634 · cache 2.5M read / 98k write · hit rate 95.9%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1792 | $0.39 | 10,494 | 1,924 | 113k | 318k | 443,458 | 72.0% | 14.2% |
