---
name: ELITEA-2059 attach-files-in-chat — step-7 keyword matcher too narrow for LLM phrasing
description: CI #244 flagged "regression" but 3/3 clean DEV repros proved class D — response correctly describes the known bare-LLM-node limitation, just without the "attach"/filename substrings the test checks for
type: feedback
---

## What happened

CI run #244 (`main`@`d46c955`, issue #2408) flagged
`tests.ui.pipelines.test_pipeline_attach_files_in_chat.test_attach_files_in_chat`
as a "product behavior regression in file attachment handling" because the AI
response was: *"It looks like the file content wasn't actually included in
your message—I only see a reference to the file path, not the text itself.
Could you please paste the content..."* — which contains neither the test
filename nor the literal substring `"attach"`, so
`assert (filename in response_lower or "attach" in response_lower)` failed.

Triage (ELITEA-2059 adjust dispatch, 2026-10-07): reproduced live on DEV, 3
separate clean process runs, **3/3 PASS**. This is **not** a regression — the
CI response is just another valid phrasing of the exact same, already-known,
already-documented architecture limitation recorded in the AFS's own "Known
Defects" section: a bare `llm`-type pipeline node only receives a path-like
reference to an attachment, never its byte content, and an honest response
says so. The AFS/test docstring even pre-flagged this exact risk ("a bare LLM
node's phrasing varies run to run and does not always cite the filename
verbatim") — it just didn't anticipate a phrasing that drops BOTH accepted
keywords ("file path" / "reference" / "paste the content", no "attach").

## Durable lesson

**A keyword-OR-list assertion against free-text LLM output is a flake
generator, not a safety net** — same root-cause shape as
`elitea_2336_pr1204_r3_known_1203_matcher_too_strict.md`'s console-matcher
case (anchoring on an exact substring combo that the underlying text producer
doesn't guarantee). Before classifying a CI "LLM response doesn't match
assertion" failure as a product regression: **reproduce 3x clean on DEV
first.** If it passes repeatedly, the fix is broadening the matcher's
semantic coverage (e.g. add `"file path"`, `"reference"`, `"paste the
content"`, `"don't have access"` as additional accepted phrasings of "I see a
reference, not the content") — not touching the *expected result* itself,
since the response still substantively satisfies the AFS's actual contract
(no execution error + an honest acknowledgment of the attachment/its
reference). That broadening is a robustness fix (class D), not a weakened
assertion — but because it edits assertion *content*, flag it for explicit
sign-off per the preserve-the-nature rail rather than silently widening it.
