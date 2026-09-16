# Batch tokenomics — fix-2318

Generated: 2026-09-16T14:06:22.526Z  ·  sessions: 1  ·  models: claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 92 | 0.0% | fresh prompt tokens, full price |
| real work: output | 33,016 | 0.4% | generated tokens — the most expensive kind |
| cache write | 193,741 | 2.3% | context stored for reuse (~1.25× input price) |
| cache read | 8,219,010 | 97.3% | context replayed from cache (~0.1× input price) |
| **total** | **8,445,859** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 97.7%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~87.4% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~66.9% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 92 | 33,016 | 194k | 8.2M | 8,445,859 |
**Total: 8,445,859 tokens · $6.87 · 0.2h active · 0 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-lead | $6.87 | 33,108 | 194k | 8.2M | 97.7% |

## Orchestrator (lead thread) composition

Lead: $6.87 — overhead incl. stages is 100% of the batch · real work 33,108 · cache 8.2M read / 194k write · hit rate 97.7%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

