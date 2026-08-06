---
name: Chat-participants version_id-mixup defect family
description: Any Agent+Pipeline chat-participant case should expect this known-unstable family — check #684/#687/#689/#1279 before re-diagnosing
type: project
---

## The family

A shared root cause — participant-state `version_id` resolution instability
in the chat PARTICIPANTS panel — surfaces under multiple distinct symptoms
depending on order/timing. First documented during the ELITEA-2094
investigation (PR EliteaAI/elitea-testing-public#688, still OPEN/unmerged,
R2-cap "Underlying product change" parked 2026-07-20):

- **#684** — Pipeline participant with an orphaned version crashes silently
  (no warning UI) instead of showing a misconfiguration warning like MCPs do.
- **#687** — A healthy remote MCP toolkit (no OAuth required) falsely shows
  "Server is disconnected!" as a misconfiguration warning.
- **#689** — The already-added-entity picker-exclusion filter intermittently
  fails once a Pipeline participant also coexists (correlated with #684's
  trigger condition, NOT a confirmed shared root cause — keep that
  distinction if citing it).
- **#1279** (filed working ELITEA-2455/#963) — Combining an Agent + a
  Pipeline participant in one conversation: Agent-then-Pipeline order is a
  **silent no-op** adding the pipeline; Pipeline-then-Agent order adds both
  but throws a console error (`version/prompt_lib` 400 + `icon_meta`
  TypeError, `ChatBox.jsx:1601`), and even that order wasn't reliably
  reproduced 2/2 inside the automated pytest harness.

All four are still OPEN as of 2026-08-06.

## Rule of thumb

Before dispatching (or re-diagnosing) any case touching the chat
PARTICIPANTS panel — especially anything combining an Agent and a Pipeline
as simultaneous participants — check #684/#687/#689/#1279 first. A new
symptom in this area is very likely a NEW SIBLING of this family (different
trigger/object, same underlying version_id instability), not a fresh
unrelated bug and not automatically a duplicate of any one of the four. Cite
the sibling relationship explicitly when filing (dedup rule — sibling ≠
duplicate, but cross-link both ways). A case that can't reliably reach a
stable multi-participant-type state because of this family is a legitimate
`defect-found`/blocked AFS status (Merge-gate analysis-time-entry rule) —
it genuinely blocks reaching later steps, it isn't an isolable tail
assertion.
