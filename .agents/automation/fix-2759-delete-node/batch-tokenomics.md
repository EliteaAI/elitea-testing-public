# Batch tokenomics — fix-2759-delete-node

Generated: 2026-10-30T07:23:46.467Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,070 | 0.4% | fresh prompt tokens, full price |
| real work: output | 24,269 | 0.3% | generated tokens — the most expensive kind |
| cache write | 339,990 | 4.6% | context stored for reuse (~1.25× input price) |
| cache read | 6,977,967 | 94.6% | context replayed from cache (~0.1× input price) |
| **total** | **7,374,296** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~54.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,070 | 24,269 | 340k | 7.0M | 7,374,296 |
**Total: 7,374,296 tokens · $2.04 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.29 | 30,028 | 137k | 6.2M | 97.7% |
| qa-engineer | $0.40 | 13,543 | 114k | 319k | 72.0% |
| test-automation-engineer | $0.35 | 12,768 | 90k | 485k | 82.9% |

## Orchestrator (lead thread) composition

Lead: $1.29 — overhead incl. stages is 63% of the batch · real work 30,028 · cache 6.2M read / 137k write · hit rate 97.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2060 | $0.75 | 20,831 | 5,480 | 203k | 804k | 1,033,709 | 78.2% | 14.0% |
