# Batch tokenomics — chat-stop-generation-2183

Generated: 2026-10-20T21:50:48.120Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 40,000 | 0.7% | fresh prompt tokens, full price |
| real work: output | 24,998 | 0.4% | generated tokens — the most expensive kind |
| cache write | 800,195 | 13.4% | context stored for reuse (~1.25× input price) |
| cache read | 5,119,264 | 85.5% | context replayed from cache (~0.1× input price) |
| **total** | **5,984,457** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~74.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~30.5% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 40,000 | 24,998 | 800k | 5.1M | 5,984,457 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 5,984,457 tokens · $3.15 · 0.6h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.21 | 21,984 | 311k | 2.0M | 85.7% |
| qa-engineer | $1.05 | 29,011 | 250k | 1.8M | 86.7% |
| test-automation-engineer | $0.89 | 14,003 | 239k | 1.4M | 85.1% |

## Orchestrator (lead thread) composition

Lead: $1.21 — overhead incl. stages is 38% of the batch · real work 21,984 · cache 2.0M read / 311k write · hit rate 85.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2183 | $1.94 | 25,671 | 17,343 | 489k | 3.2M | 3,696,066 | 86.0% | 61.8% |
