# Batch tokenomics — social-folders-critical

Generated: 2026-09-15T15:48:51.055Z  ·  sessions: 1  ·  models: claude-haiku-4-5-20251001, claude-opus-5  ·  companion of batch-report (delivery view)

## Composition — where the tokens went

| kind | tokens | share | what it is |
|---|---|---|---|
| real work: input | 941 | 0.0% | fresh prompt tokens, full price |
| real work: output | 417,590 | 0.5% | generated tokens — the most expensive kind |
| cache write | 2,557,942 | 3.0% | context stored for reuse (~1.25× input price) |
| cache read | 82,777,006 | 96.5% | context replayed from cache (~0.1× input price) |
| **total** | **85,753,479** | 100% | raw sum — dominated by the cheapest kind |

**Cache hit rate: 97.0%** — share of all prompt tokens replayed from cache versus processed fresh (input + cache write are the fresh processing).
**Cache savings: ~86.6% of prompt cost** — what the same prompt volume would have cost uncached (all tokens at 1× input price) versus as billed (write 1.25×, read 0.1×).
**Cache-read cost share: ~61% of spend** (public-list ratios: in 1× / out 5× / write 1.25× / read 0.1×) — the dollar-weighted view the cross-factory dataset reports.

## By model

| model | input | output | cache write | cache read | total |
|---|---|---|---|---|---|
| claude-opus-5 | 782 | 392,059 | 2.2M | 81.1M | 83,666,488 |
| claude-haiku-4-5-20251001 | 159 | 25,531 | 348k | 1.7M | 2,086,991 |
**Total: 85,753,479 tokens · $66.04 · 4.1h active · 12 dispatches** — judge by composition and hit rate, not by the big number.

## By role

| role | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| test-automation-engineer | $33.69 | 219,203 | 1.3M | 44.2M | 97.1% |
| qa-engineer | $17.65 | 124,837 | 933k | 19.1M | 95.3% |
| test-automation-lead | $14.70 | 74,491 | 309k | 19.5M | 98.4% |

## Orchestrator (lead thread) composition

Lead: $14.70 — overhead incl. stages is 29% of the batch · real work 74,491 · cache 19.5M read / 309k write · hit rate 98.4%
A high lead share with a high hit rate is orchestration overhead working as designed (context replayed per turn), not runaway spend.

## By stage (overhead)

| stage | cost | real work | cache write | cache read | hit rate |
|---|---|---|---|---|---|
| triage | $0.21 | 4,077 | 113k | 527k | 82.4% |
| gate | $2.37 | 13,368 | 169k | 2.0M | 92.0% |
| report | $0.30 | 19,131 | 131k | 367k | 73.7% |
| other | $1.84 | 11,502 | 165k | 1.0M | 86.3% |

## Per case (direct; clustered cases are an even split)

| case | cost | input | output | cache write | cache read | total | hit rate | share |
|---|---|---|---|---|---|---|---|---|
| ELITEA-3208 | $24.19 | 324 | 152,918 | 1.0M | 28.5M | 29,675,345 | 96.5% | 34.6% |
| ELITEA-3209 | $11.21 | 156 | 71,205 | 322k | 15.4M | 15,838,240 | 98.0% | 18.5% |
| ELITEA-3210 | $11.21 | 156 | 71,205 | 322k | 15.4M | 15,838,240 | 98.0% | 18.5% |
