# Batch tokenomics — adjust-2943

Generated: 2026-11-12T11:59:50.270Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,670 | 0.3% | fresh prompt tokens, full price |
| real work: output | 57,197 | 0.5% | generated tokens — the most expensive kind |
| cache write | 477,985 | 4.0% | context stored for reuse (~1.25× input price) |
| cache read | 11,333,187 | 95.2% | context replayed from cache (~0.1× input price) |
| **total** | **11,900,039** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~85.1% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~55.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,670 | 57,197 | 478k | 11.3M | 11,900,039 |
**Total: 11,900,039 tokens · $3.26 · 0.9h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $2.08 | 56,552 | 176k | 9.7M | 98.1% |
| test-automation-lead | $0.77 | 16,798 | 202k | 1.1M | 84.4% |
| qa-engineer | $0.41 | 15,517 | 100k | 493k | 81.7% |

## Orchestrator (lead thread) composition

Lead: $0.77 — overhead incl. stages is 24% of the batch · real work 16,798 · cache 1.1M read / 202k write · hit rate 84.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3744 | $2.49 | 21,021 | 51,048 | 276k | 10.2M | 10,534,110 | 97.2% | 88.5% |
