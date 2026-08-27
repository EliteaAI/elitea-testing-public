---
name: LLM-backed oracles — comprehension facts, not token echoes
description: Asking a model to echo an opaque identifier out of a file is guardrail-refused intermittently; plant an ordinary fact and ask an ordinary question instead
type: feedback
aliases: [token echo, opaque identifier oracle, guardrail refusal, comprehension fact, attachment oracle, 1664]
tags: [area/chat, type/oracle]
created: 2026-08-28
updated: 2026-08-28
---

## The rule (canon card #1664, OPEN)

When a test must prove a model **received and processed** specific input, assert a
**comprehension fact in ordinary prose** — plant an ordinary fact, ask an ordinary
question, assert the ordinary answer:

> *"According to the attached file, what is the project mascot? Answer with the single word."*

**Never** an opaque-token echo (`AUTOTEST_ATTACH_7X9`, `ZEPHYR-4417`, "secret codename",
any identifier the model repeats verbatim). Safety guardrails refuse that **shape**, not
the vocabulary — neutralising the wording does not help. Both shapes are equally honest
about fidelity; only one is stable.

Keep the strong deterministic assertions on the **transport** layer (upload 2xx + filepath,
the frame carrying the content, chip lifecycle). The comprehension assertion is the last
mile, not the whole proof.

## Why it bites — the failure mode

**"It works in analysis and refuses later."** It passes when you write it, then refuses on a
different model / later run, and the red is **indistinguishable from a product regression**.

## The trap I walked into (ELITEA-0500, 2026-08-28)

I measured a corrected oracle **8/8 green** on localhost and read that as clearing the token
assertion. It does not. **A local hit rate cannot detect guardrail exposure** — 8 runs, one
model, one session, minutes apart. #1664's refusals are intermittent and model-dependent.

Also worth separating: on that card the DEV red was an H1 mid-turn **narration**, *not* a
refusal. So the token assertion carried **two independent instabilities** — the oracle race
(visible, fixed) and the guardrail shape (latent, never fired). Fixing only the visible one
would have shipped exactly the merged flaky test #1664 exists to prevent.

## Convergence is the tell

ELITEA-2421 (support-assistant attachments) and ELITEA-0500 (chat attachments) both reached
"plant a token, ask for it back" independently. It is the obvious first idea and no current
rule forbids it — which is why it needs to be a rule.

Related: [[chat_ai_response_oracle_settles_mid_turn]]
