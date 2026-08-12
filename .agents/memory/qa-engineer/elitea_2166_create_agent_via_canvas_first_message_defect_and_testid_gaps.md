---
name: ELITEA-2166 create-agent-via-canvas — first-message defect (#708) + new testid-gap cluster
description: In-chat "+ Create New Agent" canvas is new page-object surface with a real, isolated first-message-only response bug (retry succeeds) and a cluster of missing testids (create-new button, 5 accordion section headers, canvas Save/Close/title/subtitle) — read before touching this flow again.
type: feedback
---

## What happened

Analyzing ELITEA-2166 (chat → `+` → Agents → "+ Create New Agent" canvas →
fill/save → send first message), found:

1. **Confirmed defect #708** — the FIRST message sent to a just-created (via
   this exact canvas) agent participant gets a reply row with an EMPTY body,
   staying empty for 5+ minutes, confirmed empty even after a hard page
   reload (fresh server fetch — not a client-side stuck-animation glitch).
   During the wait, Socket.IO degrades: 502/503 on the local polling
   endpoint, then CORS-blocked cross-origin fallback polling directly to
   `https://dev.elitea.ai/socket.io/...`. A retry (second message, SAME
   agent/conversation, no reload) got a normal reply ~5s later. This
   precisely localizes the bug to "first message only" — a general outage
   would also break the retry. Don't assume this is the same mechanism as
   #691 (orphaned empty conversation) or #692 (stale active-conversation
   flag) — both were ruled out (conversation wasn't orphaned; this isn't
   about re-selecting a conversation).
2. **CLARIFICATION #709** — while the just-created agent's OWN canvas/editor
   panel is still open, the composer shows a literal **"Editing…"** status
   label instead of the `<agent> | <version>` two-chip display — this is
   correct, intentional UX (`AgentEditorPanel.jsx`, gated on
   `edited_participant_id`), not a bug. The two-chip display only appears
   once the canvas is closed. If a case's steps imply the two-chip display
   is visible WHILE the canvas is still open, that's case-text drift, not a
   product defect.
3. **New testid-gap cluster** (all confirmed `needs-adding` on BOTH `main`
   and `automation/testids` via `git fetch origin` + `git grep` in
   `EliteaUI`):
   - The "+ Create New Agent" menu item itself
     (`PlusChatSubmenu.jsx`'s `showCreateNew` `MenuItem` block — zero
     `data-testid`; only the REGULAR items get one, via
     `${sectionKey}-menu-item-${item.key}`).
   - All 5 canvas accordion section headers (GENERAL/INSTRUCTIONS/WELCOME
     MESSAGE/CHAT STARTERS/ADVANCED) — `BasicAccordion.jsx` ALREADY supports
     a per-item `testId` prop wired straight to `data-testid` on
     `StyledAccordionSummary`; none of the 5 call sites
     (`CreateAgentForm.jsx`, `InstructionsInput.jsx`, and the
     WelcomeMessage/ConversationStarters/AdvanceSettings equivalents) pass
     it. Mechanical one-line fix per site — the plumbing already exists.
   - The canvas Save button — rendered by `CreateApplicationSaveButton.jsx`
     (create-mode), which has ZERO testid/props threading, unlike its
     edit-mode sibling `SaveApplicationButton.jsx` which already carries
     `agent-save-button` (used by `AgentFormPage.save_button`).
     `BaseEditor`'s `saveButton` slot renders exactly one of the two,
     never both — recommend reusing the identical `agent-save-button` name
     on `CreateApplicationSaveButton.jsx` rather than inventing a new one.
   - The canvas X (close) button and the post-save title/subtitle
     (agent name / version name) — `EditorHeader.jsx` has ZERO
     `data-testid` occurrences anywhere in the whole file (`grep -c testid`
     = 0 on both branches).

## Why this matters going forward

- If picking up ELITEA-2166's implementation (or any case touching the
  in-chat agent-creation canvas), the testid gaps above BLOCK compliant
  (testid-only) automation of the create/save/close actions — this is
  `add-data-testid` work, not optional polish, before a `.spec.ts`/pytest
  test can be written for this flow.
- Bug #708 should be automated via `expect.soft()` + a linked
  `# Known defect: #708` comment (merge-gate Sanctioned-RED exception per
  `.agents/testing.md` § Merge gate) — NOT masked by a silent
  retry-inside-the-test (that would hide a real product bug from CI).
- Don't confuse #708 with a general local-dev-environment flakiness episode
  — the retry-succeeds data point is the key discriminator; if a future
  session sees a similar hang WITHOUT a successful retry on the same
  agent, that's a DIFFERENT signature and needs its own fresh
  investigation, not an assumption it's "the same #708".
