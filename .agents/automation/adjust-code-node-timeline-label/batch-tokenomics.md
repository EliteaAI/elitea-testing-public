# Batch tokenomics — adjust-code-node-timeline-label

Generated: 2026-11-12T15:15:07.961Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 53,897 | 0.6% | fresh prompt tokens, full price |
| real work: output | 37,842 | 0.4% | generated tokens — the most expensive kind |
| cache write | 733,772 | 8.6% | context stored for reuse (~1.25× input price) |
| cache read | 7,743,524 | 90.4% | context replayed from cache (~0.1× input price) |
| **total** | **8,569,035** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.8%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~40% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 53,897 | 37,842 | 734k | 7.7M | 8,569,035 |
**Total: 8,569,035 tokens · $3.44 · 0.7h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.66 | 31,094 | 336k | 4.2M | 92.3% |
| test-automation-engineer | $1.05 | 33,700 | 193k | 3.0M | 93.3% |
| qa-engineer | $0.74 | 26,945 | 205k | 569k | 71.6% |

## Orchestrator (lead thread) composition

Lead: $1.66 — overhead incl. stages is 57% of the batch · real work 31,094 · cache 4.2M read / 336k write · hit rate 92.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| other | $0.31 | 13,073 | 80k | 358k | 79.9% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2448 | $1.12 | 26,136 | 10,868 | 265k | 1.9M | 2,245,271 | 87.0% | 26.2% |
| ELITEA-2449 | $0.35 | 5,212 | 5,357 | 53k | 1.3M | 1,319,057 | 95.6% | 15.4% |
