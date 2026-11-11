# Batch tokenomics — skills-4635

Generated: 2026-11-11T17:58:12.369Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 112,237 | 0.8% | fresh prompt tokens, full price |
| real work: output | 63,372 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,866,064 | 13.6% | context stored for reuse (~1.25× input price) |
| cache read | 11,652,323 | 85.1% | context replayed from cache (~0.1× input price) |
| **total** | **13,693,996** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 85.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~73.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~29.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 112,237 | 63,372 | 1.9M | 11.7M | 13,693,996 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 13,693,996 tokens · $7.36 · 1.2h active · 14 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $3.05 | 77,308 | 733k | 5.7M | 88.0% |
| qa-engineer | $2.62 | 73,499 | 623k | 4.3M | 86.7% |
| test-automation-lead | $1.69 | 24,802 | 510k | 1.6M | 74.7% |

## Orchestrator (lead thread) composition

Lead: $1.69 — overhead incl. stages is 40% of the batch · real work 24,802 · cache 1.6M read / 510k write · hit rate 74.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.34 | 9,059 | 108k | 206k | 63.8% |
| gate | $0.47 | 10,588 | 118k | 913k | 87.9% |
| report | $0.45 | 14,797 | 118k | 334k | 72.5% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4635 | $4.41 | 68,571 | 47,792 | 1.0M | 8.6M | 9,765,330 | 88.9% | 71.3% |
