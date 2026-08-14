---
name: RESOLVED — PipelineDetailPage.clear_embedded_chat() was a silent no-op (fixed)
description: HISTORICAL. Fixed for ELITEA-2011; the method now calls chat_clear_button directly. Do not act on the body below.
type: project
---

> ⚠️ **RESOLVED 2026-08-10 — do NOT act on this entry.** Verified against
> `automation/pages/pipeline_detail_page.py:6858`: `clear_embedded_chat()` now calls
> `self.chat_clear_button.click(timeout=timeout)` and its docstring records the fix
> ("Fixed for ELITEA-2011 … this method now uses it directly"). **Calling
> `clear_embedded_chat()` is the correct move.** De-indexed by scout 2026-08-10 —
> kept on disk as the record of the original defect and its fix. The secondary claim
> below (that `click_history_tab()` / `get_history_entries()` are also stale) was
> NOT re-verified; both still exist at `:2199` / `:2212`.

`automation/pages/pipeline_detail_page.py`'s `clear_embedded_chat()` (~line 6811)
clicks `[aria-label="Clear the chat history"]`. That string matches **zero**
elements on the live product — the real button is `ClearChatButton.jsx`,
`aria-label="clear the chat"` (lowercase, different wording),
`data-testid="chat-clear-button"`. The correct `chat_clear_button`
`LocatorDescriptor` field already exists on the same page object (added for
ELITEA-2016) — the method body just never uses it.

Confirmed live twice (ELITEA-2011 analysis, 2026-08-09): calling the existing
broken method before a second `send_message_in_embedded_chat()` call produced
only 1 Run History entry after 2 sent messages (both landed in the SAME
conversation, silent no-op). Calling `self.chat_clear_button.click()` directly
instead produced the expected 2 distinct entries.

**Any test that needs to start a fresh pipeline conversation mid-test (Run
History multi-entry setups, differential-routing resets, etc.) must call
`chat_clear_button` directly until this method is fixed.** The fix itself is
trivial (`self.chat_clear_button.click(timeout=timeout)`), flagged as a required
Automation Hint in `test-specs/pipelines/l2_pipeline-run-history-panel-view-executions_ELITEA-2011.md`.

Also relevant: `PipelineDetailPage.click_history_tab()` / `get_history_entries()`
are separately stale — raw CSS (`table tbody tr`, `[class*="version"]`) that
predates the current `ViewRunHistoryButton`/`RunHistoryContainer` shared-component
implementation. Don't use them for Run History work; the correct pattern mirrors
`AgentDetailPage`'s `open_run_history()`/`get_run_history_item_count()`/etc.
