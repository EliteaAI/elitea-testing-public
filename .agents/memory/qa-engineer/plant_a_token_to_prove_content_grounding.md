---
name: Plant a token to prove content-grounding
description: Prove an LLM really consumed an upload/context by planting a unique per-run token in it and asserting it comes back
type: feedback
aliases: [content grounding assertion, does the model read the file, summarize this is unassertable, unique token oracle, attachment processed assertion]
tags: [area/assertions, type/technique]
created: 2026-08-22
updated: 2026-08-22
---

## The problem

TMS cases routinely say *"verify the assistant returns a response that references or
processes the file content"*, with a prompt like *"Summarize the content of this file"*.
A free-form summary has **no deterministic observable**. Every assertion anyone writes
over it is one of two failures:

- vacuous — `assert reply != ""` passes even if the model never saw the file;
- flaky — keyword-guessing at an LLM's phrasing, red on paraphrase.

## The fix

Make the *test data* the oracle. Plant a **unique, per-run token** inside the artifact the
system must consume, and ask for it back verbatim:

```python
TOKEN = f"ZEPHYR-{uuid4().hex[:6].upper()}"
file.write_text(f"The secret project codename is {TOKEN}.\n")
# prompt: "Read the attached file and reply with ONLY the secret codename it contains."
expect(last_assistant_item()).to_contain_text(TOKEN)
```

One assertion, fully deterministic, and it proves the **whole chain** — upload → storage →
prompt assembly → model — because the token exists nowhere else in the system. It is
strictly *stronger* than the case's own bar: a summary can be faked by echoing the prompt;
the token cannot.

**Per-run, not fixed.** A constant token is satisfied by the previous run's message on any
surface that restores conversation history — green on run 1, and green for the wrong
reason afterwards.

## Why this is not a substitution

The test authors the *input*, which is normal test data. Every asserted value still comes
from the system (`.agents/testing.md` § How to test a NONDETERMINISTIC producer without
substituting it). Contrast a fabricated response, which proves only the test's own payload.

## Scope

Any "did it really consume X" question: file attachments, RAG/artifact indexing, agent
instructions, toolkit context, pipeline state hand-off.

Declare it in the AFS — it deviates from the case's literal prompt wording, so it is a
declared improvisation that owes a `question` card (worked example: ELITEA-2421).

Related: [[network_capture_timing_can_manufacture_a_false_bug]]
