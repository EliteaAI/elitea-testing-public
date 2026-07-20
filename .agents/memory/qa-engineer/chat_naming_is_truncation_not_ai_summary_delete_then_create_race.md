---
name: Chat naming is client truncation, not AI summary; delete-then-create races (ELITEA-2090)
description: Conversation "naming" in the chat UI is a one-shot truncation of the first message (not a distinct AI-generated summary) — confirmed via network capture the name field never changes again after generation completes. The "Naming…" placeholder is real but extremely short-lived (~100ms-2.4s observed) — don't hard-assert its appearance, only its resolution (existing tolerant wait_for_naming_label_to_resolve() is the correct shape). Deleting the active conversation then immediately creating a new one in the same tab produced console 500/400s and a conversation that never persisted — ruled out as self-inflicted session pollution after a clean re-run in a fresh tab, not filed as a defect.
type: feedback
---

## Context

First `test-case-analysis` pass over the `chat-interface` feature area (ELITEA-2090,
"Create New Conversation from Private Project via +Chat with default LLM"). No AFS existed
for this feature before this session — `test-specs/chat-interface/` was created fresh.

## Finding 1 — "Naming" is a truncation, not an AI summary

Network capture across two clean conversation-creation runs:
- `POST .../conversations/prompt_lib/{project}` → `201`, initial `name: "New Chat"`.
- `PUT .../conversation/prompt_lib/{project}/{id}` → `200`, `name` updated to a **truncated
  prefix of the first user message** (e.g. `"Generate test cases for login functionality"`
  → `"Generate test cases for login"`).
- A THIRD fetch of the same conversation, taken AFTER the LLM fully finished responding
  (20+ seconds later), still showed the **identical** `name` — it never changed again.

**Implication for automation**: don't assert or expect a "smarter"/different final title
than the truncated first-message text. The naming mechanism completes essentially
synchronously with the send action, well before generation finishes — it is NOT gated on or
derived from the LLM's response.

## Finding 2 — the "Naming…" placeholder is real but extremely short-lived

Confirmed via a `document.body.innerText` poll (100-200ms interval) started immediately
after the Send click, in TWO separate clean runs:
- Run A: absent at t+0, present at t+~100-200ms (first poll tick already caught it).
- Run B (cleanest timing capture): absent at t=37.7s, present t=37.9s→40.2s (**~2.4s visible
  window**), absent again by t=40.4s.

The visible window can be as short as ~100ms. **Do not write a hard/blocking assertion that
the "Naming" placeholder becomes visible** (`expect(...).to_be_visible(timeout=500)`-style) —
it's a coin-flip depending on scheduler/network timing between the Send click and the next
Playwright poll. `ChatPage.wait_for_naming_label_to_resolve()` already has the correct
shape: it checks `count() > 0` first (tolerant of the placeholder having already resolved by
the time it's checked) and only waits for `hidden` if it's currently present. Reuse that
pattern; don't try to prove the placeholder's *appearance*, only its eventual absence/
resolution.

## Finding 3 — delete-active-conversation-then-immediately-create races (NOT filed as a defect)

While exploring, I deleted a conversation via the UI (three-dot menu → Delete → confirm)
while it was still the displayed/active conversation, then immediately clicked `+Chat` and
sent a new message in the SAME tab. That produced:
- 6 console errors: `500` on `entity_settings/prompt_lib/{project}/{new_id}`, `400`s on both
  `conversation/.../{new_id}` and `select_conversation/.../{new_id}` (plus stale `400`s still
  referencing the just-deleted old id).
- A "The conversation you are looking for does not exist in your project..." alert dialog.
- The "Naming" placeholder never resolved even after 2+ minutes (vs. the normal ~100ms-2.4s).
- On a fresh page reload, the sidebar reported "Still no conversations created" — the new
  conversation never appears to have persisted server-side.

**This sequence (delete-the-active-conversation, then immediately create another in the same
tab) is NOT part of ELITEA-2090's own steps/preconditions.** Per this project's Synthetic
Input Hygiene discipline, I re-verified in a **brand-new browser tab** (fresh React app
state, same auth cookies) running the case's own actual flow with NO prior delete — that run
completed with **0 console errors**, a clean ~2.4s naming resolution, and correct button
toggling. This strongly indicates the anomaly is self-inflicted state pollution from the
unusual delete-then-create sequence, not a defect the case's own flow would ever trigger —
so it was **not filed as a tracker issue**, only documented here.

**If a future session independently reproduces conversation-creation failures specifically
following a delete of the previously-active conversation** (a genuinely different repro
target than ELITEA-2090), THAT would be worth its own dedicated reproduction pass and
likely a bug report — this note is a heads-up, not a closed investigation.

## Reusable pattern

When timing a transient UI placeholder that might resolve within one MCP round-trip, don't
rely on `browser_snapshot` alone (each call has enough round-trip latency to reliably miss a
sub-200ms state). Use `browser_evaluate` with an in-page polling loop
(`document.body.innerText` + `setTimeout`) started in the SAME evaluate call that triggers
the action — that's fast enough to catch states a snapshot-based workflow will always miss.
