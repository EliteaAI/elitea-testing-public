# Batch tokenomics — adjust-2943

Generated: 2026-11-12T12:00:07.335Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,676 | 0.3% | fresh prompt tokens, full price |
| real work: output | 57,798 | 0.5% | generated tokens — the most expensive kind |
| cache write | 480,413 | 3.9% | context stored for reuse (~1.25× input price) |
| cache read | 11,712,231 | 95.4% | context replayed from cache (~0.1× input price) |
| **total** | **12,282,118** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~56% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,676 | 57,798 | 480k | 11.7M | 12,282,118 |
**Total: 12,282,118 tokens · $3.31 · 0.9h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.08 | 56,552 | 176k | 9.7M | 98.1% |
| test-automation-lead | $0.83 | 17,405 | 204k | 1.5M | 87.7% |
| qa-engineer | $0.41 | 15,517 | 100k | 493k | 81.7% |

## Orchestrator (lead thread) composition

Lead: $0.83 — overhead incl. stages is 25% of the batch · real work 17,405 · cache 1.5M read / 204k write · hit rate 87.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3744 | $2.49 | 21,021 | 51,048 | 276k | 10.2M | 10,534,110 | 97.2% | 85.8% |
