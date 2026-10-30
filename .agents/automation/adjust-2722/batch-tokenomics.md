# Batch tokenomics — adjust-2722

Generated: 2026-10-27T06:48:24.543Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 47,506 | 0.5% | fresh prompt tokens, full price |
| real work: output | 38,077 | 0.4% | generated tokens — the most expensive kind |
| cache write | 600,858 | 5.8% | context stored for reuse (~1.25× input price) |
| cache read | 9,588,858 | 93.3% | context replayed from cache (~0.1× input price) |
| **total** | **10,275,299** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~49.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 47,506 | 38,077 | 601k | 9.6M | 10,275,299 |
**Total: 10,275,299 tokens · $3.23 · 0.6h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.44 | 33,418 | 231k | 5.3M | 95.5% |
| test-automation-engineer | $1.42 | 37,968 | 277k | 3.8M | 92.8% |
| qa-engineer | $0.37 | 14,197 | 92k | 481k | 82.4% |

## Orchestrator (lead thread) composition

Lead: $1.44 — overhead incl. stages is 45% of the batch · real work 33,418 · cache 5.3M read / 231k write · hit rate 95.5%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1954 | $1.79 | 31,233 | 20,932 | 370k | 4.3M | 4,750,262 | 91.5% | 46.2% |
