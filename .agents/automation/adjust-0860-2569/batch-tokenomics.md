# Batch tokenomics — adjust-0860-2569

Generated: 2026-10-23T04:30:41.159Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 21,574 | 0.5% | fresh prompt tokens, full price |
| real work: output | 17,687 | 0.4% | generated tokens — the most expensive kind |
| cache write | 215,430 | 5.0% | context stored for reuse (~1.25× input price) |
| cache read | 4,039,589 | 94.1% | context replayed from cache (~0.1× input price) |
| **total** | **4,294,280** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~51.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 21,574 | 17,687 | 215k | 4.0M | 4,294,280 |
**Total: 4,294,280 tokens · $1.28 · 0.3h active · 1 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.88 | 25,888 | 102k | 3.7M | 97.1% |
| qa-engineer | $0.40 | 13,373 | 114k | 317k | 71.9% |

## Orchestrator (lead thread) composition

Lead: $0.88 — overhead incl. stages is 69% of the batch · real work 25,888 · cache 3.7M read / 102k write · hit rate 97.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0860 | $0.40 | 10,494 | 2,879 | 114k | 317k | 443,864 | 71.9% | 10.3% |
