# Skills surface — exploration digest

Confirmed handles/quirks from live runs on `http://localhost:5173`
(`automation/testids` branch). Cache only — verify a handle as you use it,
don't take it on faith. One writer at a time (whoever is the active
analyst); update in place, don't append duplicate entries.

## Build with AI (skill creation) — `/skills/create` → `GenerateSkillModal`

- Modal shell (`GenerateEntityModal.jsx`) is shared with the Agent "Build
  with AI" flow via `GenerateEntityModalPageBase` — same loading/error/retry
  mechanics, entity-specific testids (`generate-skill-*` vs `generate-agent-*`).
- Steps: `input` (prompt) → `loading` → `review` (Name/Description/
  Instructions only — no Welcome Message/conversation starters, unlike Agent).
- Generate-draft endpoint: `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}`.
- Create endpoint: `POST /api/v2/elitea_core/skills/prompt_lib/{projectId}`
  → `201`, payload `{name, description, versions: [{name: "base"|"latest", instructions}]}`
  — no `temperature`/`reasoning_effort` fields (unaffected by bug #524, which
  is Agent-only via a different endpoint/payload shape).
- Review-form fields are fully client-validated, synchronously, no network
  call: `validateSkillDraft()` in
  `../EliteaUI/src/[fsd]/features/skill/lib/helpers/skillDraftValidation.helpers.js`.
  Name regex: `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` (lowercase/digits/hyphens,
  no leading/trailing hyphen), max 64 chars — **and the Name `<input>` also
  carries a native HTML `maxlength="64"`, so an over-64-char value can never
  actually be entered manually (typed or `.fill()`'d) — it silently truncates
  at 64 before validation ever runs.** The `Create <Entity>` button's
  `disabled` prop is `isApproving || !isDraftValid`
  (`GenerateEntityModal.jsx:189`) — `isDraftValid` flows from
  `onValidationChange` in the review-form component.
- Testids (all `generate-skill-*`): `open-button`, `modal`, `close-button`,
  `prompt-input`, `error-alert`, `loading-indicator`, `submit-button`
  (Generate, also the retry control), `cancel-button`, `back-button`,
  `approve-button` (Create Skill), `review-name-input`,
  `review-description-input`, `review-instructions-input` (all pre-existing
  as of ELITEA-1990), plus **`review-name-helper-text`** (added ELITEA-1993,
  commit `8e78723b` on `automation/testids`) — the Name field's validation-
  error / `{len}/64`-counter helper text; only the Name field's helper text
  has a testid so far (Description/Instructions helper text untouched — no
  case has asserted them yet).
- Page object: `automation/pages/generate_skill_modal_page.py`
  (`GenerateSkillModalPage`, extends `GenerateEntityModalPageBase`).
  `set_review_name()`/`set_review_description()`/`set_review_instructions()`
  all use plain `.click()` + `.fill()` — confirmed live this correctly
  triggers React's controlled-component `onChange` (the testid resolves to
  the native `<input>`/`<textarea>` via MUI `slotProps.htmlInput`), unlike
  the general MUI-fill gotcha documented in `.claude/rules/mui-patterns.md`.
- Test file: `automation/tests/ui/skills/test_skill_build_with_ai.py` —
  covers ELITEA-2001 (generation failure/retry), ELITEA-1990 (fields
  editable, create with edits), ELITEA-1991 (create with no edits, keeps
  generated values), ELITEA-1989 (loading text + no extra sections),
  ELITEA-1988 (modal open + static elements), ELITEA-1993 (Name-field
  validation on invalid manual edits, pending implementation).
- Skill cleanup: `SkillAPI.delete_skill(skill_id)` (cookie-auth,
  `automation/api/client.py:1270`) in a `try/finally`; get `skill_id` from
  the post-create redirect URL regex `/skills/all/(\d+)$`. Never use a raw
  `fetch()`-from-page-JS-context DELETE — CORS-fails on this app's DEV
  backend (redirects through a Keycloac forward-auth path with no
  `Access-Control-Allow-Origin`); use the UI delete flow or the API client
  instead.
