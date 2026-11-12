# Batch tokenomics — adjust-2950

Generated: 2026-11-12T17:16:23.908Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 42,419 | 0.2% | fresh prompt tokens, full price |
| real work: output | 93,492 | 0.5% | generated tokens — the most expensive kind |
| cache write | 913,663 | 4.6% | context stored for reuse (~1.25× input price) |
| cache read | 18,797,352 | 94.7% | context replayed from cache (~0.1× input price) |
| **total** | **19,846,926** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~53.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 42,419 | 93,492 | 914k | 18.8M | 19,846,926 |
**Total: 19,846,926 tokens · $5.70 · 1.1h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.65 | 95,385 | 369k | 16.1M | 97.6% |
| test-automation-lead | $1.59 | 22,874 | 443k | 1.9M | 81.0% |
| qa-engineer | $0.46 | 17,652 | 101k | 749k | 87.0% |

## Orchestrator (lead thread) composition

Lead: $1.59 — overhead incl. stages is 28% of the batch · real work 22,874 · cache 1.9M read / 443k write · hit rate 81.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2444 | $2.06 | 15,752 | 40,767 | 235k | 8.4M | 8,720,928 | 97.1% | 43.9% |
| ELITEA-2443 | $2.06 | 15,752 | 40,767 | 235k | 8.4M | 8,720,928 | 97.1% | 43.9% |
