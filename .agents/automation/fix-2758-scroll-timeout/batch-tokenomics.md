# Batch tokenomics — fix-2758-scroll-timeout

Generated: 2026-10-30T07:00:16.804Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 36,134 | 0.2% | fresh prompt tokens, full price |
| real work: output | 135,177 | 0.7% | generated tokens — the most expensive kind |
| cache write | 1,041,299 | 5.2% | context stored for reuse (~1.25× input price) |
| cache read | 18,774,596 | 93.9% | context replayed from cache (~0.1× input price) |
| **total** | **19,987,206** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.6%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~83.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~48.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 36,134 | 135,177 | 1.0M | 18.8M | 19,987,206 |
**Total: 19,987,206 tokens · $6.52 · 1.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.09 | 87,989 | 438k | 9.2M | 95.4% |
| test-automation-lead | $2.18 | 34,685 | 459k | 5.8M | 92.4% |
| qa-engineer | $1.26 | 48,637 | 145k | 3.8M | 96.1% |

## Orchestrator (lead thread) composition

Lead: $2.18 — overhead incl. stages is 33% of the batch · real work 34,685 · cache 5.8M read / 459k write · hit rate 92.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2064 | $1.45 | 7,304 | 38,238 | 194k | 4.3M | 4,574,488 | 95.6% | 22.9% |
| ELITEA-2037 | $1.45 | 7,304 | 38,238 | 194k | 4.3M | 4,574,488 | 95.6% | 22.9% |
| ELITEA-2010 | $1.45 | 7,304 | 38,238 | 194k | 4.3M | 4,574,488 | 95.6% | 22.9% |
