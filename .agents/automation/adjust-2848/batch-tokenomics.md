# Batch tokenomics — adjust-2848

Generated: 2026-11-12T07:26:47.413Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,903 | 0.4% | fresh prompt tokens, full price |
| real work: output | 33,706 | 0.4% | generated tokens — the most expensive kind |
| cache write | 576,069 | 7.0% | context stored for reuse (~1.25× input price) |
| cache read | 7,604,236 | 92.2% | context replayed from cache (~0.1× input price) |
| **total** | **8,246,914** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~45.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,903 | 33,706 | 576k | 7.6M | 8,246,914 |
**Total: 8,246,914 tokens · $2.86 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.84 | 34,420 | 337k | 5.8M | 94.3% |
| test-automation-engineer | $0.63 | 17,534 | 145k | 1.2M | 88.6% |
| qa-engineer | $0.39 | 14,655 | 94k | 603k | 85.3% |

## Orchestrator (lead thread) composition

Lead: $1.84 — overhead incl. stages is 64% of the batch · real work 34,420 · cache 5.8M read / 337k write · hit rate 94.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1954 | $1.03 | 20,937 | 11,252 | 239k | 1.8M | 2,082,529 | 87.4% | 25.3% |
