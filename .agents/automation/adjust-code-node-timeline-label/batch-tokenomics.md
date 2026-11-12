# Batch tokenomics — adjust-code-node-timeline-label

Generated: 2026-11-12T15:15:14.633Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 53,956 | 0.6% | fresh prompt tokens, full price |
| real work: output | 39,505 | 0.5% | generated tokens — the most expensive kind |
| cache write | 734,429 | 8.4% | context stored for reuse (~1.25× input price) |
| cache read | 7,903,687 | 90.5% | context replayed from cache (~0.1× input price) |
| **total** | **8,731,577** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.9%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.7% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~40.3% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 53,956 | 39,505 | 734k | 7.9M | 8,731,577 |
**Total: 8,731,577 tokens · $3.47 · 0.7h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.69 | 32,816 | 337k | 4.3M | 92.6% |
| test-automation-engineer | $1.05 | 33,700 | 193k | 3.0M | 93.3% |
| qa-engineer | $0.74 | 26,945 | 205k | 569k | 71.6% |

## Orchestrator (lead thread) composition

Lead: $1.69 — overhead incl. stages is 58% of the batch · real work 32,816 · cache 4.3M read / 337k write · hit rate 92.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| other | $0.31 | 13,073 | 80k | 358k | 79.9% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2448 | $1.12 | 26,136 | 10,868 | 265k | 1.9M | 2,245,271 | 87.0% | 25.7% |
| ELITEA-2449 | $0.35 | 5,212 | 5,357 | 53k | 1.3M | 1,319,057 | 95.6% | 15.1% |
