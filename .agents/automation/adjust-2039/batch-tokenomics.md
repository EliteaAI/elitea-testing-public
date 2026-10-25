# Batch tokenomics — adjust-2039

Generated: 2026-10-25T04:51:04.230Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 31,734 | 0.7% | fresh prompt tokens, full price |
| real work: output | 19,453 | 0.4% | generated tokens — the most expensive kind |
| cache write | 321,963 | 7.0% | context stored for reuse (~1.25× input price) |
| cache read | 4,197,370 | 91.8% | context replayed from cache (~0.1× input price) |
| **total** | **4,570,520** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 92.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~81.2% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~44.1% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 31,734 | 19,453 | 322k | 4.2M | 4,570,520 |
**Total: 4,570,520 tokens · $1.66 · 0.1h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $0.87 | 25,116 | 114k | 3.1M | 96.2% |
| test-automation-engineer | $0.48 | 13,768 | 123k | 703k | 84.1% |
| qa-engineer | $0.31 | 12,303 | 85k | 352k | 78.7% |

## Orchestrator (lead thread) composition

Lead: $0.87 — overhead incl. stages is 52% of the batch · real work 25,116 · cache 3.1M read / 114k write · hit rate 96.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-2039 | $0.79 | 20,852 | 5,219 | 208k | 1.1M | 1,289,136 | 82.2% | 28.2% |
