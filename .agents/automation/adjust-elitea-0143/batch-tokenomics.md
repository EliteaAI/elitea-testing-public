# Batch tokenomics — adjust-elitea-0143

Generated: 2026-11-18T09:12:02.911Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 76,762 | 0.7% | fresh prompt tokens, full price |
| real work: output | 46,453 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,108,245 | 10.2% | context stored for reuse (~1.25× input price) |
| cache read | 9,622,521 | 88.7% | context replayed from cache (~0.1× input price) |
| **total** | **10,853,981** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 76,762 | 46,453 | 1.1M | 9.6M | 10,853,981 |
**Total: 10,853,981 tokens · $4.79 · 1.1h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $2.33 | 35,169 | 504k | 6.1M | 92.2% |
| test-automation-engineer | $1.37 | 43,768 | 320k | 2.6M | 88.1% |
| qa-engineer | $1.08 | 44,278 | 284k | 944k | 74.8% |

## Orchestrator (lead thread) composition

Lead: $2.33 — overhead incl. stages is 49% of the batch · real work 35,169 · cache 6.1M read / 504k write · hit rate 92.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-0143 | $2.45 | 64,750 | 23,296 | 605k | 3.6M | 4,246,628 | 84.2% | 39.1% |
