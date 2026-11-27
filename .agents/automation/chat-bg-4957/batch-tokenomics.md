# Batch tokenomics — chat-bg-4957

Generated: 2026-11-27T13:41:12.744Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 41,488 | 0.3% | fresh prompt tokens, full price |
| real work: output | 49,812 | 0.4% | generated tokens — the most expensive kind |
| cache write | 1,225,456 | 10.2% | context stored for reuse (~1.25× input price) |
| cache read | 10,715,646 | 89.1% | context replayed from cache (~0.1× input price) |
| **total** | **12,032,402** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.4%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.9% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~37% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 41,488 | 49,812 | 1.2M | 10.7M | 12,032,402 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 12,032,402 tokens · $4.72 · 1.5h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $2.31 | 22,995 | 786k | 2.3M | 74.4% |
| qa-engineer | $1.57 | 45,897 | 286k | 5.4M | 94.7% |
| test-automation-engineer | $0.83 | 22,408 | 153k | 2.9M | 94.8% |

## Orchestrator (lead thread) composition

Lead: $2.31 — overhead incl. stages is 49% of the batch · real work 22,995 · cache 2.3M read / 786k write · hit rate 74.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4957 | $2.41 | 26,502 | 41,803 | 439k | 8.4M | 8,889,063 | 94.7% | 73.9% |
