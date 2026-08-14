---
name: Grep own memory before building a DOM-read workaround
description: Before writing a scroll-and-stitch/evaluate() workaround for a flaky or truncating page-object read, grep this memory dir for the symptom — a simpler, already-team-sanctioned fix may already exist
type: feedback
---

## What happened (ELITEA-1990/1991/1993 rework, 2026-08-14)

Removing a fabricated `mock_generate_success()` payload from
`test_create_skill_from_unmodified_draft_persists_generated_values`
(ELITEA-1991) let a real, long, multi-paragraph AI-generated Instructions
value flow through for the first time. `SkillDetailPage.get_instructions()`/
`get_instructions_multiline()` silently truncated it — CodeMirror only keeps
a viewport-sized window of `.cm-line` nodes in the DOM.

First move: build a full DOM-scroll-and-stitch page-object method
(`get_instructions_full_multiline()`), mirroring the already-merged
`mcp_form_page.py::get_raw_json_full()` technique. Took 2 reruns to get
right (a blank-line-doubling artifact, then the viewport-truncation itself)
and added real complexity — `page.evaluate()` calls that then needed
fidelity-policy justification in the self-check grep.

Only after building and shipping that did a memory grep turn up
`skill_instructions_editor_long_ai_content_use_api_not_dom.md` (ELITEA-2611,
already in this same directory) — which documents this EXACT symptom for
this EXACT field and recommends the much simpler fix: read
`skill_api.get_skill(skill_id)["version_details"]["instructions"]` instead
of fighting the DOM (the pattern `test_skill_edit_with_ai_happy_path.py` /
`test_skill_fork_end_to_end.py` already use). Reverted the DOM workaround,
switched to the API read — simpler, no new page-object code, no
`.evaluate()` hits to justify, and a *stronger* persistence proof (server
ground truth) besides.

## The lesson

Hard Rule 7 ("reuse before create") says grep for existing helpers/fixtures/
page objects before adding new ones — but I only grepped `automation/`
source, not `.agents/memory/test-automation-engineer/`. When a page-object
read starts behaving unreliably for a NEW content shape (long/multi-line/
AI-generated), grep memory for the symptom (`grep -ril "truncat\|virtualiz\|
CodeMirror\|long.*content" .agents/memory/test-automation-engineer/`) before
reaching for a technical workaround — someone may have already hit this and
recorded the fix, sometimes a much simpler one than the obvious DOM-level
patch.
