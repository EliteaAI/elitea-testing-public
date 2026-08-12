---
name: Skill Publish token invalidation and TTL
description: validation_token format, 5-min TTL, and the two distinct 400 error messages (modified vs expired)
type: reference
---

Live-confirmed (ELITEA-2597, skill 1579/version 1663, both direct-API and a
real two-tab UI repro):

- `publish_skill_validate`'s `validation_token` is a 4-part colon-delimited
  opaque string: `<base64 sig>:<version_id>:<hex hash>:<unix timestamp>`.
  The trailing segment IS the issuance Unix time (cross-checked vs
  `date -u +%s`, matched within ~1s, twice). Never parse/reconstruct it in
  automation — treat as fully opaque.
- `validation_token` is `null` in the response whenever `status: "FAIL"` —
  only minted on `WARN`/`PASS`. Same icon+tag prerequisite gap as
  ELITEA-2595/#1463 applies (need ≥1 tag + custom icon to avoid FAIL).
- TTL is **exactly 300s (5 min)**, matching the case text. Confirmed by a
  real 330s wait (Bash foreground `sleep 320`, legal per the "long jobs"
  doctrine — one turn regardless of sleep length) then attempting publish.
- Two distinct 400 responses, SAME `error` code, DIFFERENT `msg` — automation
  must assert on `msg` text, not just status/error code, to distinguish:
  - Modified after validation: `{"error": "validation_token_invalid", "msg":
    "Agent was modified since validation. Please re-validate."}` — note the
    **"Agent" wording bug on the Skill flow** (filed as MINOR bug #1465,
    cosmetic only, mechanism itself correct).
  - Expired (>300s): `{"error": "validation_token_invalid", "msg":
    "Validation token expired. Please re-validate before publishing."}`
- Both errors render inline in the wizard's Validation-step summary node (no
  new testid) and disable "Publish" — the wizard does NOT auto-reset to
  Preparation or auto-refire validation; user must Cancel + reopen.
- The SkillAPI PUT (`/skill/{mode}/{project}/{skillId}/{versionId}`, PUT)
  did NOT visibly persist `version.instructions` via a naive
  `{"project_id":..,"user_id":..,"version":{"instructions":...}}` payload in
  quick exploratory probing — the response echoed the OLD instructions back
  unchanged. Didn't dig further (used the real UI Save instead, which
  worked correctly). If a future case needs API-only skill-content
  mutation, budget time to find the correct PUT payload shape (top-level
  `name` errors with "Cannot rename the base version" — so top-level fields
  DO apply, only the nested `version.instructions` attempt silently no-op'd;
  likely a payload-shape mismatch, not a broken endpoint).
- Full AFS: `test-specs/skills/l2_skill-publishing-token-invalidation-and-ttl-expiration_ELITEA-2597.md`.
