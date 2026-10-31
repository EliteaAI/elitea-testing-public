# Batch tokenomics — adjust-2809

Generated: 2026-10-31T08:10:45.691Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 33,719 | 0.8% | fresh prompt tokens, full price |
| real work: output | 20,127 | 0.5% | generated tokens — the most expensive kind |
| cache write | 335,854 | 8.1% | context stored for reuse (~1.25× input price) |
| cache read | 3,732,992 | 90.5% | context replayed from cache (~0.1× input price) |
| **total** | **4,122,692** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 91.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.8% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~40.2% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 33,719 | 20,127 | 336k | 3.7M | 4,122,692 |
**Total: 4,122,692 tokens · $1.63 · 0.2h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.65 | 20,872 | 96k | 2.3M | 95.6% |
| test-automation-engineer | $0.59 | 16,853 | 143k | 904k | 85.5% |
| qa-engineer | $0.39 | 16,121 | 97k | 491k | 81.8% |

## Orchestrator (lead thread) composition

Lead: $0.65 — overhead incl. stages is 40% of the batch · real work 20,872 · cache 2.3M read / 96k write · hit rate 95.6%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2039 | $0.98 | 22,748 | 10,226 | 240k | 1.4M | 1,668,034 | 84.2% | 40.5% |
