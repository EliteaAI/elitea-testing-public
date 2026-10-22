# Batch tokenomics — chat-new-conv-folder-2504

Generated: 2026-10-22T11:09:54.572Z  ·  sessions: 2  ·  models: 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0, 1_eu.anthropic.claude-sonnet-5, 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 200,278 | 0.4% | fresh prompt tokens, full price |
| real work: output | 185,139 | 0.4% | generated tokens — the most expensive kind |
| cache write | 4,743,068 | 10.5% | context stored for reuse (~1.25× input price) |
| cache read | 39,974,013 | 88.6% | context replayed from cache (~0.1× input price) |
| **total** | **45,102,498** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 89.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~77.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~36.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 184,975 | 168,199 | 4.2M | 35.8M | 40,405,002 |
| 1_eu.anthropic.claude-sonnet-5 | 15,281 | 14,873 | 420k | 4.0M | 4,429,390 |
| 1_eu.anthropic.claude-haiku-4-5-20251001-v1:0 | 22 | 2,068 | 108k | 158k | 268,107 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 45,102,497 tokens · $20.20 · 3.3h active · 22 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $8.50 | 69,641 | 2.3M | 10.7M | 81.8% |
| test-automation-engineer | $6.46 | 172,354 | 1.2M | 18.2M | 93.2% |
| qa-engineer | $5.23 | 143,424 | 1.2M | 11.0M | 90.0% |

## Orchestrator (lead thread) composition

Lead: $8.50 — overhead incl. stages is 57% of the batch · real work 69,641 · cache 10.7M read / 2.3M write · hit rate 81.8%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.18 | 2,090 | 108k | 158k | 59.3% |
| gate | $0.67 | 12,530 | 173k | 1.2M | 86.7% |
| report | $0.54 | 20,665 | 128k | 350k | 72.0% |
| other | $1.65 | 44,193 | 309k | 4.9M | 93.6% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2757 | $8.65 | 122,110 | 114,189 | 1.7M | 22.7M | 24,574,256 | 92.6% | 54.5% |
