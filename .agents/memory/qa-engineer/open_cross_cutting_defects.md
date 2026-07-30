---
name: Open cross-cutting defects that bite any case
description: Five open defects that are not scoped to the surface you happen to be testing — they break fixtures, leak data, or silently red a merged test on surfaces you never touched. Check here before debugging your own setup.
type: project
---

> **Decays fast — re-verify state before acting.** Each row names the issue to
> check. Last verified 2026-07-30.

## The five

1. **#524 — agent create 400s (temperature + reasoning_effort conflict).** OPEN.
   `AgentAPI.create_agent()` hardcodes `temperature` alongside `reasoning_effort`
   on a reasoning-capable model (`automation/api/client.py` ~386–390), so the
   `agent_id` fixture dies across the agents/chat/skills suites. Park before
   dispatching anything that creates an agent via API.
   **Carve-out:** skills are unaffected — they POST `/skills/prompt_lib/{id}`
   with no `temperature`/`reasoning_effort` fields, so a skills-only case need
   not park. (Details: `bug_524_does_not_affect_skill_create.md`.)
   **Related:** the house workaround `reasoning_effort: "none"` 500s the moment
   a test opens embedded chat — use `"low"` for any fixture whose agent will chat.
2. **#694 — BaseModal `aria-labelledby` points at a non-existent id.**
   `BaseModal.jsx`'s `Dialog` references `alert-dialog-title` while the real
   title `<h2>` carries a stale `id="variables-dialog-title"` (EL-2863 refactor
   regression, EliteaUI commit `459c1f8a`). Silently broke the merged
   `test_delete_conversation_with_confirmation` — verified RED by a live run.
   ~15 call sites; any modal-titled assertion may be affected.
3. **`artifact_bucket` fixture delete silently fails (404, both URL formats).**
   Buckets leak on every run. Root cause is a URL-shape mismatch between the UI's
   query-param delete and `ArtifactAPI.delete_bucket()`'s path-segment shape
   (informs #636). Don't assume a clean bucket list.
4. **#551 / #585 — CardList clear-after-zero-result redirects to the create page.**
   Clearing a zero-match search navigates away from the list entirely. Confirmed
   on Credentials (#551) and MCP (#585), same root-cause shape, likely present on
   every other `CardList`-based page. Also: `customEmptyState` always wins over
   the query-aware placeholder — don't testid the dead one.
5. **#607 — Support Assistant conversation pagination truncation.** The
   conversation list truncates on fetch; any count- or presence-based assertion
   over a long Support Assistant history can read short. A delta-shaped assertion
   survives it only if the action between the two counts never re-triggers the
   truncating fetch — a checkable implementation fact, not an inference.

## Why these are indexed and the surface notes are not

Each of these fires on a surface you did not choose to test — a fixture, a shared
modal, a shared list component. You would debug your own setup for an hour before
thinking to grep for them. That is the preventive test; the per-surface entries
(which only matter once you are already on that surface) are on disk, unindexed.

See also: agent_create_400_temperature_reasoning_conflict.md ·
bug_524_does_not_affect_skill_create.md (test-automation-lead) ·
basemodal_aria_labelledby_id_mismatch_and_conversation_menu_gaps.md ·
artifact_bucket_fixture_delete_silently_fails_404.md ·
shared_list_search_empty_state_and_clear_redirect_bug.md ·
support_assistant_conversation_pagination_truncation_defect.md
