# Batch tokenomics — adjust-2916

Generated: 2026-11-11T12:10:38.499Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,630 | 0.4% | fresh prompt tokens, full price |
| real work: output | 44,484 | 0.6% | generated tokens — the most expensive kind |
| cache write | 550,811 | 6.9% | context stored for reuse (~1.25× input price) |
| cache read | 7,305,719 | 92.1% | context replayed from cache (~0.1× input price) |
| **total** | **7,932,644** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~43.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,630 | 44,484 | 551k | 7.3M | 7,932,644 |
**Total: 7,932,644 tokens · $2.88 · 0.5h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $1.48 | 41,817 | 194k | 5.3M | 96.3% |
| test-automation-lead | $0.97 | 18,612 | 257k | 1.4M | 84.0% |
| qa-engineer | $0.42 | 15,685 | 100k | 605k | 84.5% |

## Orchestrator (lead thread) composition

Lead: $0.97 — overhead incl. stages is 34% of the batch · real work 18,612 · cache 1.4M read / 257k write · hit rate 84.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2057 | $1.91 | 20,905 | 36,597 | 294k | 5.9M | 6,248,949 | 94.9% | 78.8% |
