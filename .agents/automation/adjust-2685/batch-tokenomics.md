# Batch tokenomics — adjust-2685

Generated: 2026-10-25T09:26:00.714Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 33,631 | 0.6% | fresh prompt tokens, full price |
| real work: output | 23,762 | 0.4% | generated tokens — the most expensive kind |
| cache write | 514,060 | 8.9% | context stored for reuse (~1.25× input price) |
| cache read | 5,208,595 | 90.1% | context replayed from cache (~0.1× input price) |
| **total** | **5,780,048** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~39.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 33,631 | 23,762 | 514k | 5.2M | 5,780,048 |
**Total: 5,780,048 tokens · $2.32 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.11 | 21,468 | 271k | 2.1M | 88.0% |
| test-automation-engineer | $0.77 | 19,483 | 137k | 2.5M | 94.4% |
| qa-engineer | $0.43 | 16,442 | 106k | 647k | 84.5% |

## Orchestrator (lead thread) composition

Lead: $1.11 — overhead incl. stages is 48% of the batch · real work 21,468 · cache 2.1M read / 271k write · hit rate 88.0%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2377 | $1.21 | 22,782 | 13,143 | 243k | 3.1M | 3,426,325 | 92.2% | 59.3% |
