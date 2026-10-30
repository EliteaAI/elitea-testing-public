---
name: AI-response-timeout gate RED can be one model route, not the whole predict pipeline
description: Before classifying a chat-AI-response-timeout gate RED as "DEV outage, wait it out", check whether it is scoped to the one model the test's conversation defaults to
type: feedback
---

## What happened (#2459, 2026-10-19, batch builder-modules-chat-2459)

Two sibling cases (ELITEA-3370, ELITEA-3372) both hit a `wait_for_ai_response`
timeout at the same point — the "Thought for..." indicator stuck at 0%, no
Copy button, ever — sustained across 4+ hours and two independent
`batch-stabilize` rounds. The natural read is "DEV's whole AI backend is down,
nothing to do but wait."

The stabilize round-2 fixer disambiguated it properly: it switched the SAME
conversation to other models mid-session (Anthropic Claude 4.5 Sonnet,
Dial-GPT-5.4, Dial-GPT-5.6-Sol, and even Bedrock-GPT-5.6-Luna — the *same*
underlying model family via a different provider route) and all answered in
under 4 seconds. Only `Dial-GPT-5.6-Luna` (this suite's default model) hung.
That is a **provider-route-specific** incident, not a predict-pipeline-wide
outage — a materially different fact for triage, and for whether other,
unrelated batches/cases are safe to keep running in parallel.

## The technique

When a gate/implementer hits an AI-response timeout and no obvious product
cause is visible in the UI/network layer:

1. **Don't assume the whole pipeline is down from one model's symptom.** Open
   (or reuse) the same conversation and send the same prompt through 1-2 OTHER
   models in the catalog.
2. If other models answer normally, the incident is scoped to that one
   model/provider route — file it as such (name the exact model + route in the
   bug), and consider whether swapping the test's default model is a viable
   short-term unblock vs. waiting for the vendor route to recover.
3. If every model hangs identically, it's pipeline-wide — the "wait it out"
   framing is correct, and nothing in this suite can route around it.

## Why this matters for stabilize dispatches

`batch-stabilize` is bounded to 2 rounds and will spend a full round trying to
"fix" a cause even when the right answer is "nothing to fix, this is external"
— that's correct behavior (it still returns real diagnostic evidence, as it
did here), but it means the LEAD should do the model-isolation check itself,
or ask for it explicitly in the stabilize dispatch, rather than waiting for a
second round to discover it. It would have saved one full round+gate cycle
(~1.5h) here.
