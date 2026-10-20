# Batch tokenomics — chat-project-context-3368

Generated: 2026-10-20T16:33:08.249Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 163,195 | 1.3% | fresh prompt tokens, full price |
| real work: output | 50,812 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,380,064 | 10.9% | context stored for reuse (~1.25× input price) |
| cache read | 11,016,358 | 87.4% | context replayed from cache (~0.1× input price) |
| **total** | **12,610,429** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~76.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~34% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 163,195 | 50,812 | 1.4M | 11.0M | 12,610,429 |
**Total: 12,610,429 tokens · $5.92 · 1.2h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $2.77 | 38,958 | 646k | 6.2M | 90.4% |
| test-automation-engineer | $2.09 | 124,515 | 503k | 3.1M | 83.3% |
| qa-engineer | $1.07 | 50,534 | 231k | 1.7M | 86.6% |

## Orchestrator (lead thread) composition

Lead: $2.77 — overhead incl. stages is 63% of the batch · real work 38,958 · cache 6.2M read / 646k write · hit rate 90.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| other | $0.97 | 63,193 | 234k | 1.4M | 82.4% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3368 | $1.61 | 80,121 | 10,017 | 389k | 2.3M | 2,746,480 | 82.8% | 21.8% |
| ELITEA-3315 | $0.58 | 10,506 | 11,212 | 111k | 1.2M | 1,308,355 | 90.6% | 10.4% |
