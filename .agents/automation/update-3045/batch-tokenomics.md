# Batch tokenomics — update-3045

Generated: 2026-11-26T17:01:07.992Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 32,492 | 0.7% | fresh prompt tokens, full price |
| real work: output | 17,452 | 0.4% | generated tokens — the most expensive kind |
| cache write | 319,765 | 7.3% | context stored for reuse (~1.25× input price) |
| cache read | 4,040,094 | 91.6% | context replayed from cache (~0.1× input price) |
| **total** | **4,409,803** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~43.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 32,492 | 17,452 | 320k | 4.0M | 4,409,803 |
**Total: 4,409,803 tokens · $1.44 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.66 | 22,305 | 99k | 2.8M | 96.3% |
| test-automation-engineer | $0.43 | 14,406 | 122k | 700k | 84.1% |
| qa-engineer | $0.34 | 13,233 | 99k | 502k | 82.0% |

## Orchestrator (lead thread) composition

Lead: $0.66 — overhead incl. stages is 46% of the batch · real work 22,305 · cache 2.8M read / 99k write · hit rate 96.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3750 | $0.78 | 21,373 | 6,266 | 221k | 1.2M | 1,450,627 | 83.2% | 32.9% |
