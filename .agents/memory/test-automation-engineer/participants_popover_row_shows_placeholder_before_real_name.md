---
name: Participants popover row renders a placeholder before the real name
description: chat-participant-row-{uniqueId} briefly shows literal text "Participant Name" (a loading skeleton) before the real participant name lands — a one-shot wait_for(visible)+text_content() read can capture the placeholder. Use expect(row).to_contain_text(name, timeout=...) instead.
type: feedback
---

## What happened (ELITEA-2465, 2026-08-16)

After `open_participants_popover(section="agents")` + resolving the row via
`PARTICIPANT_ROW.format(f"application_{agent_id}_{project_id}")`, a plain
`row.wait_for(state="visible")` followed by `row.text_content()` intermittently
read back the literal string `"Participant Name"` instead of the real agent
name — the row visibly mounts before its content fetch/render settles.

**Symptom:** `assert agent_name in (row.text_content() or "")` failed with
`assert 'autotest_2465_...' in (('Participant Name'))` — the row WAS visible
(so the `wait_for` didn't time out), it just hadn't rendered real content yet.

**Fix:** use Playwright's web-first `expect(row).to_contain_text(agent_name,
timeout=...)` instead of `wait_for(visible)` + a one-shot `text_content()`
read — it retries until the real text lands (or times out), rather than
reading whatever happens to be there the instant visibility is achieved.

## When this applies

Any read of `PARTICIPANT_ROW`'s (or any other dynamically-populated
participants-list row's) text content, in the popover OR the expanded
side-panel form (`get_participant_row_by_name()`). Not observed yet on
`switch_participant_button`/`chat_version_selector_trigger` (composer chips) —
those already get read via `expect(...).to_contain_text()` in existing code,
which is why they haven't shown this symptom.
