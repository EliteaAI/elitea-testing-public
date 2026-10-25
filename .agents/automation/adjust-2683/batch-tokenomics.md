# Batch tokenomics — adjust-2683

Generated: 2026-10-25T08:55:53.318Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,084 | 0.3% | fresh prompt tokens, full price |
| real work: output | 32,524 | 0.3% | generated tokens — the most expensive kind |
| cache write | 516,374 | 5.5% | context stored for reuse (~1.25× input price) |
| cache read | 8,820,039 | 93.8% | context replayed from cache (~0.1× input price) |
| **total** | **9,401,021** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.1%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~51.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,084 | 32,524 | 516k | 8.8M | 9,401,021 |
**Total: 9,401,021 tokens · $2.82 · 0.6h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.30 | 22,875 | 266k | 3.7M | 93.1% |
| test-automation-engineer | $1.16 | 27,773 | 161k | 4.6M | 96.4% |
| qa-engineer | $0.36 | 13,960 | 90k | 469k | 82.4% |

## Orchestrator (lead thread) composition

Lead: $1.30 — overhead incl. stages is 46% of the batch · real work 22,875 · cache 3.7M read / 266k write · hit rate 93.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1140 | $0.94 | 15,705 | 12,142 | 170k | 2.8M | 2,970,223 | 93.7% | 31.6% |
| ELITEA-1141 | $0.58 | 5,208 | 8,679 | 80k | 2.3M | 2,397,746 | 96.4% | 25.5% |
