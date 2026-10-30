# Batch tokenomics — adjust-3749

Generated: 2026-10-25T07:01:48.690Z  ·  sessions: 1  ·  models: 1_eu.anthropic.claude-sonnet-5-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 33,235 | 0.5% | fresh prompt tokens, full price |
| real work: output | 23,395 | 0.3% | generated tokens — the most expensive kind |
| cache write | 344,890 | 4.8% | context stored for reuse (~1.25× input price) |
| cache read | 6,747,982 | 94.4% | context replayed from cache (~0.1× input price) |
| **total** | **7,149,502** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 94.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.0% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~53.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| 1_eu.anthropic.claude-sonnet-5-5 | 33,235 | 23,395 | 345k | 6.7M | 7,149,502 |
**Total: 7,149,502 tokens · $2.05 · 0.3h active · 2 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $1.17 | 28,773 | 133k | 5.2M | 97.3% |
| test-automation-engineer | $0.54 | 14,912 | 123k | 1.2M | 89.8% |
| qa-engineer | $0.34 | 12,945 | 89k | 360k | 78.3% |

## Orchestrator (lead thread) composition

Lead: $1.17 — overhead incl. stages is 57% of the batch · real work 28,773 · cache 5.2M read / 133k write · hit rate 97.3%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3749 | $0.88 | 20,850 | 7,007 | 212k | 1.5M | 1,771,485 | 86.8% | 24.8% |
