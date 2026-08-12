---
name: Skill unpublish/republish — public_skill_id coexistence mechanics
description: Unpublish allocates a NEW public_skill_id on republish (real deletion); publishing a sibling version while an existing published version stays live REUSES the same public_skill_id — this is the actual "version coexistence" mechanism (ELITEA-2599).
type: project
---

Discovered analysing ELITEA-2599 (`test-specs/skills/l3_skill-unpublish-
republish-lifecycle_ELITEA-2599.md`). Confirmed live end-to-end on skill 1595,
project 399.

**The rule, easy to get backwards:**
- Publish → Unpublish → Republish (same or different version of the same
  skill) → `public_skill_id` changes (unpublish is a real deletion,
  `unpublish_skill` response is `{msg, status: "deleted"}`, not a toggle).
  Confirmed: v1.0 published → `public_skill_id=51` → unpublished → v2.0
  published → `public_skill_id=52` (NEW).
- Publishing a SIBLING version of the same skill WITHOUT unpublishing the
  currently-live published version first → SAME `public_skill_id`, new
  `public_version_id` only. Confirmed: v2.0 live at `public_skill_id=52,
  public_version_id=56`; publishing the skill's `base` draft as v3.0 (v2.0
  never unpublished) → `public_skill_id=52, public_version_id=57`. A further
  v4.0 (from the reusable now-unpublished-v1.0 version) → still `52,
  public_version_id=58`. 3 versions coexisting under one public entry, no
  cap enforcement observed at 3.

**Catalog card** is keyed `catalog-skill-card-{public_skill_id}` — one card
per ACTIVE public_skill_id. Opening it shows only current content, no
version-history UI exposed to viewers. "Only latest shown" is structural
(one growing entry), not a client-side latest-filter.

**Confirm-unpublish testid**: `agent-unpublish-confirm-button` — same
cross-entity naming artifact as `agent-publish-*` (component hardcodes it
regardless of `entityLabel` prop). Not a defect, already-accepted pattern.

**Unrelated but hit in the same session**: one `publish_skill_validate` call
502'd then 503'd then succeeded on a 3rd immediate retry, alongside unrelated
socket.io 502/503s and a CORS failure hitting `dev.elitea.ai` directly —
transient local dev-backend/proxy flakiness, not a publish-specific defect.
Bounded retry (2-3x) on `publish_skill_validate` is reasonable; don't
hard-fail on one isolated hit, but don't swallow a repeating one either.

A true 4th-version-BEYOND-3-coexisting publish was not exercised (turn
budget) — unconfirmed whether a hard cap exists past 3. TMS case's own
language for this edge ("handled appropriately") is non-prescriptive.
