---
name: PipelineDetailPage.clear_embedded_chat() is a silent no-op
description: stale aria-label selector matches nothing live; use chat_clear_button testid directly instead
type: project
---

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
