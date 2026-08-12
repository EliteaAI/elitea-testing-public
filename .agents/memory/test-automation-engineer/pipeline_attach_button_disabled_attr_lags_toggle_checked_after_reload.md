---
name: Pipeline attach button disabled attribute lags toggle checked after reload
description: chat-attach-button's disabled attr syncs ~2s after a hard reload, behind the toggle's already-correct checked value — use expect().to_be_enabled()/.to_be_disabled(), not a one-shot read
type: feedback
---

## What happens

On the Pipeline detail page, the "Attachments" MODULES toggle
(`agent-canvas-tools-toggle-attachments`) and the embedded chat's attach
button (`chat-attach-button`, `PipelineDetailPage.chat_attach_button`) are
linked: the toggle's checked state gates the button's `disabled` attribute.
Live-confirmed (ELITEA-2066, 2026-08-09) that this link IS genuinely
server-persisted across Save + a hard page reload, in both directions. BUT
on the FIRST render right after a hard reload (`PipelineDetailPage.navigate()`
called again, not a same-page re-check), there's a race:

- The toggle's `checked` DOM property reads the persisted value correctly
  **immediately**.
- The attach button's `disabled` attribute can still read the OLD/wrong
  value for up to ~2s before syncing to match the toggle.

A one-shot `.is_disabled()` snapshot read taken right after
`wait_for_canvas()`/`wait_for_detail_page_load()` can catch that stale
window and produce a false failure (or false pass, if you're asserting the
wrong direction) on an otherwise-correct persistence check.

## Fix

Use Playwright's auto-retrying assertions for any POST-RELOAD check of this
button — they poll until the DOM settles, absorbing the lag for free:

```python
expect(pipeline_page.chat_attach_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
expect(pipeline_page.chat_attach_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
```

The toggle's own `checked` property does NOT need this treatment — it reads
correctly immediately, no retry needed
(`pipeline_page.is_tools_module_toggle_checked("attachments")` is fine as a
plain one-shot read).

This is NOT a product defect — the persisted value was always correct on
reload in every observation; only the button's own attribute took a moment
to catch up, with zero console errors and zero extra network requests.

See: `test-specs/pipelines/_surface.md` (Attachments toggle persistence
section), `test-specs/pipelines/lextend_pipeline-modules-attachments-toggle-persists_ELITEA-2066.md`,
`automation/tests/ui/pipelines/test_pipeline_attach_files_in_chat.py::test_attachments_toggle_persists_across_save_and_reload`.
