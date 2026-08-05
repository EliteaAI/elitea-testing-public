---
name: Agent Hub detail modal testid gaps and drift
description: AgentModal.jsx — 6 of ~10 fields have zero testids; CHAT STARTERS/Start Chat/copy-link drift already tracked
type: project
---

Confirmed live 2026-08-05 (ELITEA-2356, `AgentModal.jsx` — the Catalog agent
preview modal opened by clicking any agent card):

**Testid coverage is sparse.** Only 3 pre-existing testids on the whole modal:
`catalog-agent-modal-agent-name`, `catalog-agent-modal-show-instructions-link`,
`catalog-agent-modal-start-chat-button` (all from ELITEA-2075), plus
`agent-hub-modal-menu-button` (the overflow "..." menu, unrelated dispatch).
Everything else — agent icon, owner name, like button, close "x" button,
description, and both content sections (Chat Starters / Welcome Message) —
has ZERO testid as of this dispatch. Full recommended names + exact JSX line
numbers: `test-specs/agent-hub/l3_agent-hub-open-agent-detail-modal_ELITEA-2356.md`
§ Concrete Handles — reuse that table rather than re-deriving it.

**The like button in the modal is a DIFFERENT code path than the card-list
like button** — both use the shared `Like.jsx`/`AgentHubLike.jsx`, but
`AgentCard.jsx` threads a `testId` prop (`catalog-agent-like-button-{id}`,
ELITEA-2354) while `AgentModal.jsx`'s own `<AgentHubLike>` call
(`AgentModal.jsx:198-201`) threads none at all. Don't assume the modal's like
button is covered just because the card's is.

**Case-text drift, recurring across the whole family that opens this modal**
(cite, don't re-derive):
- "CONVERSATION STARTERS" / "Start conversation" → live is "CHAT STARTERS" /
  "Start Chat" — [#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042),
  explicitly names ELITEA-2356/2357/2358/2359/2360/2361/2362/2368/2369 as
  affected siblings.
- "copy link icon" → live has no standalone icon, it's the
  `agent-hub-modal-menu-button` overflow menu's "Share" item —
  [#1218](https://github.com/EliteaAI/elitea-testing-public/issues/1218)
  (filed ELITEA-2356), names ELITEA-2359/#867 as the sibling that actually
  exercises the copy-link action.
- Minor, not worth a ticket: "Welcome Message" header renders title-case,
  NOT all-caps, unlike the adjacent "CHAT STARTERS" header (also all-caps in
  source) — a real product copy inconsistency, but too trivial to file.

**Ready-signal**: the modal's content (icon/description/sections) depends on
`GET /api/v2/elitea_core/public_application/prompt_lib/{id}` (singular)
resolving, not just the modal becoming visible — `AgentHubPage.open_agent_by_name()`
already waits on this exact response; reuse it rather than a bare visibility wait
(the same race class as known defect #1043, which manifests on the Start Chat
button specifically but the root cause is generic to every field sourced from
`agentDetails`).
