# Batch tokenomics — elitea-4715

Generated: 2026-11-18T11:35:52.111Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 40,507 | 0.3% | fresh prompt tokens, full price |
| real work: output | 61,898 | 0.5% | generated tokens — the most expensive kind |
| cache write | 949,641 | 7.4% | context stored for reuse (~1.25× input price) |
| cache read | 11,859,445 | 91.9% | context replayed from cache (~0.1× input price) |
| **total** | **12,911,491** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.3%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~43.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 40,507 | 61,898 | 950k | 11.9M | 12,911,491 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,911,491 tokens · $4.71 · 0.8h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $1.80 | 50,642 | 307k | 5.0M | 94.0% |
| test-automation-lead | $1.74 | 24,646 | 468k | 2.6M | 84.3% |
| test-automation-engineer | $1.17 | 27,117 | 175k | 4.2M | 95.8% |

## Orchestrator (lead thread) composition

Lead: $1.74 — overhead incl. stages is 37% of the batch · real work 24,646 · cache 2.6M read / 468k write · hit rate 84.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4715 | $2.97 | 25,899 | 51,860 | 482k | 9.3M | 9,821,358 | 94.8% | 76.1% |
