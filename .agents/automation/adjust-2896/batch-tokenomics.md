# Batch tokenomics — adjust-2896

Generated: 2026-11-09T13:17:21.202Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 55,935 | 0.4% | fresh prompt tokens, full price |
| real work: output | 74,066 | 0.5% | generated tokens — the most expensive kind |
| cache write | 1,432,258 | 9.9% | context stored for reuse (~1.25× input price) |
| cache read | 12,903,805 | 89.2% | context replayed from cache (~0.1× input price) |
| **total** | **14,466,064** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~78.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 55,935 | 74,066 | 1.4M | 12.9M | 14,466,064 |
**Total: 14,466,064 tokens · $6.30 · 2.5h active · 4 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $2.78 | 66,478 | 639k | 5.2M | 88.6% |
| test-automation-lead | $1.88 | 26,513 | 530k | 2.3M | 80.8% |
| test-automation-engineer | $1.63 | 37,010 | 264k | 5.4M | 95.2% |

## Orchestrator (lead thread) composition

Lead: $1.88 — overhead incl. stages is 57% of the batch · real work 26,513 · cache 2.3M read / 530k write · hit rate 80.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $1.72 | 29,136 | 408k | 3.4M | 89.1% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1791 | $2.69 | 31,486 | 42,866 | 494k | 7.2M | 7,780,393 | 93.2% | 53.8% |
