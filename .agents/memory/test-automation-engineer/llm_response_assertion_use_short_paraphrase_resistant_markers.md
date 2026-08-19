---
name: LLM response assertion — short paraphrase-resistant markers
description: Asserting an LLM prose reply engages with N inputs — use short per-input markers with OR fallback, not one long exact-substring per input.
type: feedback
---

## The trap

A test that sends an AI/agent N distinctly-named/labeled inputs (e.g. 4
attached files) and then asserts the reply "references" each one is tempting
to write as:

```python
for name in inputs:
    assert name in response_text  # requires the LITERAL label, every time
```

This is real (asserts against the live, captured response — not fabricated,
per `.agents/testing.md` § Fidelity policy), but **over-specifies HOW the
model must phrase engagement**, and LLM prose is not that stable run to run.

## What actually happened (ELITEA-2201, 2026-08-19)

Same prompt, same 4 files, 3 consecutive live runs, 3 different phrasing
styles:
1. 3 files named by filename, the 4th referenced only via its embedded
   distinguishing content token inside a generic closing sentence.
2. NO filenames or tokens at all — every file's business-content line
   quoted close to verbatim, organized by topic instead of by source file.
3. That same content line **paraphrased mid-phrase** — "Revenue grew 12% in
   Q1" became "12% growth in Q1" (same fact, different word order) — which
   broke a first fix attempt that used a longer *exact*-phrase marker
   ("12% in q1").

All three are genuine engagement with every input's content — the model
just varies *how* it identifies each one.

## The fix pattern

Per input, build a **markers list**: the label/filename, any embedded
identifying token, AND a **short** (single word, a bare number, or a
tightly-bound 2-word phrase — never a long exact phrase) content-derived
keyword. Assert `any(marker.lower() in response.lower() for marker in
markers)` per input — every input still individually checked (not
"majority" or "response is non-empty"), just tolerant of the model's
observed phrasing variance. Short markers survive word-order/insertion
paraphrase; long exact phrases don't.

## Verification discipline

One green run is NOT enough evidence for this class of assertion — run it
standalone at least 2-3× before trusting it; each run is a real, independent
LLM sample and different failure styles surface on different runs (as
above, 2 different failure modes hit on 2 consecutive attempts before the
markers design stabilized).

## Where

`automation/tests/ui/chat/test_send_message_with_attachments_verify_included.py`
(ELITEA-2201) — `ATTACHMENT_SPECS` markers-list pattern, module docstring
"Per-file check technique" has the full worked reasoning.
