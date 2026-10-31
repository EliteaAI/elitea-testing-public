# Batch tokenomics — adjust-2800

Generated: 2026-10-31T05:25:24.646Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,671 | 0.5% | fresh prompt tokens, full price |
| real work: output | 28,225 | 0.5% | generated tokens — the most expensive kind |
| cache write | 521,892 | 9.0% | context stored for reuse (~1.25× input price) |
| cache read | 5,249,007 | 90.0% | context replayed from cache (~0.1× input price) |
| **total** | **5,830,795** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 90.5%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~79.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~38.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,671 | 28,225 | 522k | 5.2M | 5,830,795 |
**Total: 5,830,795 tokens · $2.39 · 0.4h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.26 | 22,836 | 290k | 2.8M | 90.3% |
| test-automation-engineer | $0.78 | 22,190 | 144k | 2.1M | 93.1% |
| qa-engineer | $0.35 | 14,870 | 88k | 356k | 78.3% |

## Orchestrator (lead thread) composition

Lead: $1.26 — overhead incl. stages is 53% of the batch · real work 22,836 · cache 2.8M read / 290k write · hit rate 90.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2041 | $1.13 | 20,867 | 16,193 | 232k | 2.4M | 2,708,146 | 90.6% | 46.4% |
