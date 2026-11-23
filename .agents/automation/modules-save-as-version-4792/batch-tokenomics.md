# Batch tokenomics — modules-save-as-version-4792

Generated: 2026-11-23T20:07:40.610Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5, <synthetic>  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 40,040 | 0.7% | fresh prompt tokens, full price |
| real work: output | 22,518 | 0.4% | generated tokens — the most expensive kind |
| cache write | 696,713 | 12.2% | context stored for reuse (~1.25× input price) |
| cache read | 4,950,076 | 86.7% | context replayed from cache (~0.1× input price) |
| **total** | **5,709,347** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 87.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~75.3% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~32.6% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 40,040 | 22,518 | 697k | 5.0M | 5,709,347 |
| <synthetic> | 0 | 0 | 0 | 0 | 0 |
**Total: 5,709,347 tokens · $2.54 · 0.5h active · 6 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| qa-engineer | $0.98 | 27,526 | 264k | 1.9M | 86.8% |
| test-automation-lead | $0.97 | 19,875 | 296k | 1.4M | 82.2% |
| test-automation-engineer | $0.59 | 15,157 | 137k | 1.7M | 91.9% |

## Orchestrator (lead thread) composition

Lead: $0.97 — overhead incl. stages is 38% of the batch · real work 19,875 · cache 1.4M read / 296k write · hit rate 82.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | n/a | 0 | 0 | 0 | n/a |
| report | n/a | 0 | 0 | 0 | n/a |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-4792 | $1.57 | 25,908 | 16,775 | 401k | 3.5M | 3,961,678 | 89.2% | 69.4% |
