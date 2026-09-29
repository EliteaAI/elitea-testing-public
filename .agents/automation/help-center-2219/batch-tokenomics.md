# Batch tokenomics — help-center-2219

Generated: 2026-09-29T16:06:30.459Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 7,804 | 0.1% | fresh prompt tokens, full price |
| real work: output | 28,746 | 0.5% | generated tokens — the most expensive kind |
| cache write | 291,652 | 4.6% | context stored for reuse (~1.25× input price) |
| cache read | 5,974,832 | 94.8% | context replayed from cache (~0.1× input price) |
| **total** | **6,303,034** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 95.2%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~84.5% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~53.7% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 7,804 | 28,746 | 292k | 6.0M | 6,303,034 |
**Total: 6,303,034 tokens · n/a · 0.2h active · 0 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | n/a | 36,550 | 292k | 6.0M | 95.2% |

## Orchestrator (lead thread) composition

Lead: n/a · real work 36,550 · cache 6.0M read / 292k write · hit rate 95.2%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

