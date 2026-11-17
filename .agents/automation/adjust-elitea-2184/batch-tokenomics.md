# Batch tokenomics — adjust-elitea-2184

Generated: 2026-11-17T19:16:45.499Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,832 | 0.5% | fresh prompt tokens, full price |
| real work: output | 25,786 | 0.4% | generated tokens — the most expensive kind |
| cache write | 509,948 | 8.7% | context stored for reuse (~1.25× input price) |
| cache read | 5,276,408 | 90.3% | context replayed from cache (~0.1× input price) |
| **total** | **5,843,974** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~39.8% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,832 | 25,786 | 510k | 5.3M | 5,843,974 |
**Total: 5,843,974 tokens · $2.36 · 0.5h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.23 | 22,762 | 264k | 2.9M | 91.4% |
| test-automation-engineer | $0.77 | 21,163 | 155k | 1.9M | 91.9% |
| qa-engineer | $0.36 | 13,693 | 91k | 477k | 82.5% |

## Orchestrator (lead thread) composition

Lead: $1.23 — overhead incl. stages is 52% of the batch · real work 22,762 · cache 2.9M read / 264k write · hit rate 91.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2184 | $1.13 | 20,940 | 13,916 | 246k | 2.3M | 2,626,723 | 89.8% | 44.9% |
