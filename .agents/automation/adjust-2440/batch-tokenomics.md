# Batch tokenomics — adjust-2440

Generated: 2026-10-25T07:44:39.989Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,986 | 0.8% | fresh prompt tokens, full price |
| real work: output | 15,118 | 0.4% | generated tokens — the most expensive kind |
| cache write | 304,226 | 7.8% | context stored for reuse (~1.25× input price) |
| cache read | 3,557,543 | 91.0% | context replayed from cache (~0.1× input price) |
| **total** | **3,908,873** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~80.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~42.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,986 | 15,118 | 304k | 3.6M | 3,908,873 |
**Total: 3,908,873 tokens · $1.46 · 0.2h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.71 | 20,536 | 101k | 2.8M | 96.1% |
| test-automation-engineer | $0.43 | 13,379 | 118k | 445k | 77.7% |
| qa-engineer | $0.33 | 13,189 | 85k | 351k | 78.5% |

## Orchestrator (lead thread) composition

Lead: $0.71 — overhead incl. stages is 48% of the batch · real work 20,536 · cache 2.8M read / 101k write · hit rate 96.1%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2440 | $0.76 | 20,838 | 5,730 | 203k | 796k | 1,025,585 | 78.0% | 26.2% |
