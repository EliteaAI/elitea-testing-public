# Test Case: Personalization settings save automatically, without a Save button

## Metadata
- **TMS ID**: ELITEA-2387
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w08`, cluster ELITEA-2371/2372/2373/2380/2387, 2026-08-28
- **Status**: ready-for-automation (**case-text drift — asserts the LIVE contract**)
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: clarification **#1960**
- **Reuse**: `automation/pages/user_profile_settings_page.py` already has `wait_for_autosave()`
  (line 489) built for exactly this `PUT /api/v2/social/author/` round-trip — reuse it rather than
  re-deriving a wait.

---

## ⚠️ Case-text drift — read this before implementing

| Case text | Live product (verified 2026-08-28) |
|---|---|
| "Navigate to Settings → Personalization" | `/settings/personalization` **404s**. "Default Personality" is the **`Default persona`** select of the `PERSONA MANAGEMENT` accordion on **Settings → AI Personality** (`/settings/ai-personality`) |
| "Change Default Personality to \"QA\"" | Option exists: label `QA`, value `qa` (`PERSONA_OPTIONS`, `src/common/constants.js:1122`), description "Precise, technical, testing-focused" |
| "Navigate away (e.g. Settings → Notifications)" | Works as written — `settings-nav-item-notifications` |

Everything the case actually verifies — **no Save button + the change survives navigation** —
is real and was reproduced end to end this session. Only the route name is stale.

---

## Preconditions
- User logged in (`auth_state`; login skipped on localhost via `VITE_DEV_TOKEN`).
- **This case MUTATES shared account state** (`personalization.persona` on the shared
  `${TEST_USER}` record, and the persona also drives chat behaviour). The spec MUST:
  1. read the persona **before** the change (do not assume `Generic` — it is whatever the
     last session left; observed `Generic` this session);
  2. pick a target that differs from the current value (case asks for `QA`; if the current
     value already **is** `qa`, flip to `generic` first or choose another option and record it);
  3. **restore the original value in teardown**, waiting for its autosave `PUT` too.
  Analyst did exactly this by hand (Generic → QA → verified → Generic) and left the account
  as found.

## Test Data
### reuse-existing
Persona options are static product constants — no seeding.

---

## Test Steps

### Step 1 — Open Settings → AI Personality
Navigate via the drawer (`settings-nav-item-ai-personality`).
**Expected:** `PERSONA MANAGEMENT` accordion visible, expanded; `Default persona` select
rendered; record its current value as `original_persona`.
⚠️ **Render race (observed live):** immediately after navigation the select is not yet in
the DOM — a probe run one turn after `goto` returned `null`, the next returned the value.
Wait on the select being visible, never a sleep.

### Step 2 — Verify there is no "Save" button on the page
**Expected:** zero buttons whose accessible text matches `/save/i` anywhere in the page
(verified live on `/settings/ai-personality`, and also on `/settings/preferences` and
`/settings/memory` — the whole personalization area is Save-button-free).
Assert this **scoped to `settings-content`** plus a page-level check; the assertion is an
absence assertion and is a first-class reference for the coverage metric (canon #511 extension).

### Step 3 — Change `Default persona` to `QA`
Open the select, click the `QA` option.
**Expected (verified live):**
- the select's displayed value becomes `QA`;
- a **`PUT /api/v2/social/author/` fires immediately → 200**, followed by a refetch
  `GET /api/v2/social/author/` (network capture confirmed). This is the wait signal —
  use `wait_for_autosave()`, never a sleep;
- the `User instructions` placeholder switches to
  *"No custom instructions for the QA persona yet. Type here to add some."* (per-persona
  instruction slots — `PERSONA_INSTRUCTIONS_PLACEHOLDERS`).

### Step 4 — Navigate away (Settings → Notifications)
Click `settings-nav-item-notifications`. **Expected:** URL `/settings/notifications`, page renders.

### Step 5 — Navigate back to AI Personality
Click `settings-nav-item-ai-personality`.

### Step 6 — Verify `Default persona` still shows `QA`
**Expected:** the select reads `QA` (verified live).

### Step 7 (Axis 2) — Full page reload, verify `QA` persisted server-side
`page.reload()` / re-navigate, then re-read.
**Expected:** still `QA` (verified live). This is what distinguishes *saved* from *cached
in the SPA store* — Step 6 alone cannot tell them apart.

### Teardown — restore `original_persona`
Set the select back and wait for its autosave `PUT`. Assert the restore landed.

**Route-guarded, and best-effort only on the failure path** (shipped shape, added in
fix round 1 of PR #1961). The restore first checks `page.url` and re-opens
`/settings/ai-personality` when the body died elsewhere — Steps 4–5 leave the browser
on `/settings/notifications`, where the persona select does not exist, so an
unguarded read auto-waits and raises. Two consequences the guard removes: the restore
could not run at all (shared `${TEST_USER}` state left on the changed persona), and
the teardown exception *replaced* the real failure in the report. When the body
already failed the restore swallows its own exception (logged, `exc_info`); when the
body passed it stays strict and a failed restore fails the test. Pinned by
`tests/unit/test_personalization_restore_route_guard.py`.

---

## Concrete Handles

| Element | Handle | Provenance (verified `git fetch origin`, 2026-08-28) |
|---|---|---|
| Settings content pane | `settings-content` | on `automation/testids`; not on `main` |
| AI Personality nav item | `settings-nav-item-ai-personality` (+ `data-active`) | on `automation/testids`; not on `main` |
| Notifications nav item | `settings-nav-item-notifications` | on `automation/testids`; not on `main` |
| `PERSONA MANAGEMENT` accordion wrapper | `ai-personality-persona-section` | **testid needed** — `AIPersonalityPersonalization.jsx`, `<BasicAccordion data-testid=…>` (prop already supported, `BasicAccordion.jsx:40,45`) |
| `Default persona` select | `ai-personality-persona-select` | **testid needed** — same file, `<SingleSelect data-testid=…>`. `SingleSelect` already reads `'data-testid': dataTestId` and additionally emits `${dataTestId}-combobox` on the display element (`SingleSelect.jsx:82,661-662`) — pure prop pass-through, no new node |
| Select display value (read + click to open) | `ai-personality-persona-select-combobox` | derived automatically by `SingleSelect` from the above |
| Persona options | `select-option-{value}` → `select-option-qa`, `select-option-generic` | **pre-existing generic** shared-component testid (`SingleSelect.jsx:416`, `option.testId ?? select-option-${value}`). Dynamic pattern ⇒ UPPER_CASE class constant `SELECT_OPTION = '[data-testid="select-option-{}"]'` |
| `User instructions` textarea | `ai-personality-user-instructions-textarea` | **testid needed** (optional — only if Step 3's placeholder assertion is kept). `Input.StyledInputEnhancer` already plumbs testids elsewhere in this repo |
| Save-button absence | absence assertion over `button` text `/save/i` scoped to `settings-content` | no testid to add — the point is that no such control exists |

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Navigate to Settings → Personalization | page loads | Step 1 (`/settings/ai-personality`) | page + accordion assertions | **clarification #1960** — case route 404s |
| Step 2 — no "Save" button on the page | absent | Step 2 | absence assertion | covered |
| Step 3 — change Default Personality to "QA" | change applies | Step 3 | displayed value + autosave `PUT` 200 | covered |
| Step 4 — navigate away (Notifications) | page loads | Step 4 | URL + render | covered |
| Step 5 — navigate back to Personalization | page loads | Step 5 | URL + render | covered |
| Step 6 — Default Personality still "QA" | value persisted | Step 6 | displayed value | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| The autosave `PUT /api/v2/social/author/` returns **200** (Step 3) | "Saved without a Save button" is only proven by the write actually succeeding; a UI value that persists in the SPA store would satisfy Step 6 without anything being saved |
| Value survives a **full page reload** (Step 7) | Same reason, one level stronger — separates server persistence from client cache |
| `User instructions` placeholder follows the selected persona | Cheap, already observed, and pins that the change reached Formik state rather than only the select's own display |
| Original persona restored in teardown | Shared-account hygiene — the persona affects other chat specs' behaviour |

---

## Known traps

- **Shared mutable account state.** See § Preconditions. Never hardcode `Generic` as the
  "original" value.
- **Render race** after navigating to `/settings/ai-personality` (Step 1).
- **Known console error #1771** (`disableUnderline` React warning) fires on this route via
  `StyledInputEnhancer`. If a "no console errors" assertion is added, it must filter exactly
  that message (known defect, linked) — nothing broader.
- **Numeric-field autosave bug #1129** does **not** apply here: this is a select, and the
  toggle/select autosave path is the reliable one (`_surface.md` § Autosave).

---

## Amendments — implementer exploration (ELITEA-2387 implementation, 2026-08-29)

Attributed to test-automation-engineer; the AFS's *what* is unchanged.

**The autosave wait is `page.expect_response`, not
`UserProfileSettingsPage.wait_for_autosave()`.** That helper is a
`networkidle` wait with a `wait_for_timeout` fallback — it awaits *some* network
quiet, and can neither identify the PUT nor read its status. This AFS's own Axis 2
requires the assertion "the autosave `PUT /api/v2/social/author/` returns **200**",
so the spec wraps the select interaction in
`page.expect_response(<PUT to /api/v2/social/author/>)` and asserts `status == 200`
— strictly stronger, still no sleep, and it is the shape the repo's other autosave
assertions already use (`set_target_summary_tokens`'s docstring names it as the
caller's contract). `wait_for_autosave()` is left untouched for its existing callers.

Additional note: `networkidle` is a documented flake source on this app
(`.agents/testing.md` § Unconfirmed, issue #1847 — the Socket.IO polling transport
never goes quiet), which is a second reason not to route this case's wait through it.

Handles landed on `automation/testids` in EliteaAI/EliteaUI@fa505e37:
`ai-personality-persona-section`, `ai-personality-persona-select` (+ the
`-combobox` element `SingleSelect` derives), `ai-personality-user-instructions-textarea`
(via the established `inputProps={{ 'data-testid': ... }}` shape — the placeholder
assertion of Step 3 was kept).

**Spec:** `automation/tests/ui/settings/test_personalization_autosave_no_save_button.py`
