# Batch tokenomics — adjust-elitea-1182

Generated: 2026-11-16T14:39:28.191Z  ·  sessions: 3  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 66,802 | 0.5% | fresh prompt tokens, full price |
| real work: output | 51,737 | 0.4% | generated tokens — the most expensive kind |
| cache write | 806,715 | 6.1% | context stored for reuse (~1.25× input price) |
| cache read | 12,314,655 | 93.0% | context replayed from cache (~0.1× input price) |
| **total** | **13,239,909** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 93.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~82.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~48% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 66,802 | 51,737 | 807k | 12.3M | 13,239,909 |
**Total: 13,239,909 tokens · $4.29 · 0.8h active · 3 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $2.71 | 68,187 | 464k | 9.0M | 94.8% |
| qa-engineer | $1.06 | 35,552 | 220k | 2.2M | 90.2% |
| test-automation-engineer | $0.53 | 14,800 | 123k | 1.1M | 88.8% |

## Orchestrator (lead thread) composition

Lead: $2.71 — overhead incl. stages is 79% of the batch · real work 68,187 · cache 9.0M read / 464k write · hit rate 94.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.70 | 21,438 | 133k | 1.8M | 92.5% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1182 | $0.88 | 20,929 | 7,985 | 210k | 1.5M | 1,766,308 | 86.9% | 13.3% |
