# Test Case: Skills listing — card view shows correct fields

## Metadata
- **TMS ID**: ELITEA-2428
- **Linked Story**: none
- **Priority**: l2 (case frontmatter/body header: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` / id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value for this project, not an
  exclusion — proceeded to full execution.
- **Case snapshot note**: the batch dispatch named the intake folder
  `skills-remaining-w1`, which does not exist; the case's actual snapshot
  was found at `.agents/automation/skills-remaining/cases/ELITEA-2428.md`
  (sibling folder `skills-remaining`, no `-w1` suffix). Flagging for the
  orchestrator — likely a dispatch-slug drift, not a missing case.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all`).
- **At least one Skill exists with a name, description, and at least one
  tag** — this AFS creates a dedicated skill for the assertions (own data,
  not a mutation of pre-existing skills), per Test Data below.

## Test Data

### generate-per-test (created in test setup via the live UI create form,
cleaned up in its own teardown)
- Skill: name `autotest-card-fields-<ts_or_uuid8>` (must match the
  create-form's client-validated regex
  `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` — lowercase/digits/hyphens only, no
  leading/trailing hyphen), description a distinctive, non-empty string
  (used later to assert the hover tooltip shows the SAME text — e.g.
  `"ELITEA-2428 card-view field verification description text, unique
  enough to spot in a hover tooltip."`), one tag (e.g.
  `cardfields2428`), instructions any non-empty string.
- **Created via `SkillFormPage`, not `SkillAPI.create_skill()`** — the API
  helper's payload (`{name, description, versions: [...]}`,
  `automation/api/client.py:1427`) has no `tags` field; confirmed via
  source (`skillsApi.js`'s `skillCreate` mutation body builder) that the
  create endpoint's request payload EliteaUI actually sends has no tags
  parameter either. The live UI form nonetheless persists the tag
  correctly end-to-end (confirmed live this run: `form_page.add_tag()`
  before `Save` → the tag appears on the card immediately after) — same
  pattern already used by `test_skill_tag_filter.py` (ELITEA-1740) to seed
  tagged skills. Use `SkillFormPage.fill_form(name=..., description=...,
  instructions=...)` + `SkillFormPage.add_tag(tag)` +
  `wait_for_form_validation()` + `save_and_wait_for_navigation()`, then
  `SkillDetailPage.get_skill_id()` for cleanup, exactly mirroring
  `test_skill_tag_filter.py` Step 1's Skill-A flow.
- `SkillAPI.delete_skill(skill_id)` for teardown (cookie auth,
  `automation/api/client.py:1460`) — same cleanup pattern as every other
  skill test in this suite (`try/finally`, tolerate "already gone").

## Test Steps

1. **Create a Skill with a name, description, and tag(s)** via
   `/skills/create` (`SkillFormPage`) — see Test Data. Confirm the create
   succeeds: redirected to `/skills/all/{id}`
   (`SkillDetailPage.verify_on_detail_page()`), `Skill ID` visible in the
   Information panel.
2. **Navigate to `/skills/all`** (`SkillsListPage.navigate()`). Confirm
   **Card view is the active view by default** — no click needed on the
   view toggle; the "Card list view" button in the page-header's Small View
   Toggler carries `aria-pressed`/visually-pressed state on page load
   (confirmed live this run: fresh navigation to `/skills/all` renders the
   grid of cards directly, "Card list view" toggle button shows `[pressed]`
   in the accessibility tree with no interaction).
3. **Locate the created Skill's card in the grid** and verify it shows:
   - **a. Skill icon** — the `EntityIcon` glyph at the top-left of the card
     (confirmed live: a generic skill glyph, visually present on every
     card regardless of whether the skill has a custom icon set).
   - **b. Skill name** — the card's title text matches the created skill's
     exact name.
   - **c. Description upon hover** — hovering the card's name/title area
     opens a tooltip (MUI Popper, `role="tooltip"`, ~1s `enterDelay`)
     whose content is the skill's name (bold) followed by its full
     description text, matching exactly what was entered at creation.
     Confirmed live this run: the description is NOT visible anywhere on
     the un-hovered card — it renders ONLY inside this hover tooltip.
   - **d. Assigned tag(s)** — the tag chip(s) added at creation render on
     the card's bottom-left tag section, exact text match.

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: Card
view is the default view on `/skills/all` with no interaction required;
each skill card in the grid shows its icon, name, description (revealed
only on hover via a tooltip), and assigned tag(s) — all four fields
confirmed present and correct for a freshly created skill with all four
attributes populated. No functional defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| 1 Create a Skill with name, description, and tags | operation completes; state updates, confirmation shown | step 1 | step 1: redirect to `/skills/all/{id}`, detail page loads, Skill ID visible | asserted |
| 2 Navigate to Skills list; confirm Card view is active by default | target page/section loads | step 2 | step 2: `/skills/all` loads, "Card list view" toggle button `[pressed]` with no click | asserted |
| 3 Verify each card shows: icon, name, description (on hover), tags | condition holds as described | step 3a–3d | step 3a (icon element present), 3b (name text match), 3c (hover → tooltip text match), 3d (tag chip text match) | asserted *(decomposed — the case's single expected result bundles four distinct observables, each needs its own assertion to be meaningful)* |
| Expected Final State: each card shows icon, name, description-on-hover, tags | — | steps 1–3 | full create → list → per-field verify | asserted |

### Axis 2 — Analyst additions

- step 2 documents the exact toggle-button testids (`agent-card-view-button`
  / `agent-table-view-button`, shared `ViewToggle.jsx` component, see
  Concrete Handles) — *added: the case only says "confirm Card view is
  active by default," the implementer needs a concrete assertion target
  (pressed-state attribute), not just a visual read.*
- step 3c documents that the description is asserted ONLY via the hover
  tooltip, never as always-visible card text — *added: this is the crux of
  the case's own step 3 wording ("description (upon hover)") and is easy
  to get wrong by asserting a `title` HTML attribute or a truncated
  always-visible description instead of the actual hover-revealed tooltip
  content; confirmed live which behavior is real.*
- "zero console errors/warnings across the full flow (create → navigate →
  hover → inspect tags)" — *added: side-channel check per this skill's
  standard discipline; not itself a case requirement.*
- Confirmed live that the description tooltip's ~1s `enterDelay` means a
  fixed short wait/no-wait hover assertion will flake — *added: implementer
  must use a proper wait (`expect(...).to_be_visible()` with Playwright's
  auto-retry, or `wait_for_selector`), never a fixed `page.wait_for_timeout`
  under ~1.2s.*

## Cleanup
1. Delete the skill created in Test Data via `SkillAPI.delete_skill(skill_id)`
   in test teardown (regardless of pass/fail) — same pattern as every other
   skill test in this suite.
2. No other product state is created by this case.
3. **This run's own skill (`skill-card-2428-1e8db006`, id `1421`) was
   deleted live via the UI delete-confirmation flow** (typed the exact name
   to confirm) before this AFS was written — no stray skill left behind.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Skill create form — Name / Description / Tags / Instructions / Save | `skill-name-input-field`, `skill-description-input-field`, `skill-tags-input-field`, `skill-instructions-editor-content`, `skill-save-button` — all **pre-existing**, already wired in `SkillFormPage` | on-main ✓ (established, reused by ELITEA-1740/1990/2001 etc.) |
| Skills list → Card view toggle button (`ViewToggle.jsx`, shared across Skills/Agents/Applications/Pipelines/Credentials/Toolkits pages) | `page.get_by_test_id("agent-card-view-button")` — **existing testid**, confirmed live `[pressed]` on fresh `/skills/all` load with no click. **Naming quirk, not a defect** (same shape as `SkillsListPage.search_input`'s documented `agent-search-input` reuse): `ViewToggle.jsx`'s default prop values are `cardViewTestId = 'agent-card-view-button'` / `tableViewTestId = 'agent-table-view-button'`, and `Skills.jsx:70` renders `<ViewToggle />` with no prop override, so the Skills page's toggle literally carries `agent-*` testids. Confirmed via source (`ViewToggle.jsx` lines 14–15, `Skills.jsx:70`) — functionally correct on the Skills page, just the shared-component-hardcodes-a-feature-scoped-name pattern documented in `.agents/testing.md` § Locator policy. No `add-data-testid` fix needed to satisfy THIS case (the handle resolves correctly); flagging only so a future testid-hygiene pass knows the root cause. | on-main ✓ (`agent-card-view-button`/`agent-table-view-button` both present on `main`) |
| Skills list → Table view toggle button (companion, for negative/contrast checks only — not this case's target) | `page.get_by_test_id("agent-table-view-button")` | on-main ✓ |
| Skill card outer container (list view) | `page.get_by_test_id("entity-card")` — **existing testid**, already `SkillsListPage.skill_card` | on-main ✓ |
| Skill card name (title) | `page.get_by_test_id("entity-card-name")` — **existing testid**, already `SkillsListPage.skill_card_name` | on-main ✓ |
| Skill card icon | `page.get_by_test_id("entity-card-icon")` (outer) / `page.get_by_test_id("entity-card-icon-img")` (inner `<img>`) — **existing testids** on the shared `Card.jsx`'s `EntityIcon`, added for ELITEA-1899 (Agents). Confirmed via source read this run (`Card.jsx` lines ~174–180: `<EntityIcon data-testid="entity-card-icon" imgTestId="entity-card-icon-img" .../>`) that the SAME `Card.jsx` renders skill cards — no skill-specific fix needed. **No page-object field exists yet on `SkillsListPage`** (only `AgentsListPage.entity_card_icon`/`get_card_icon_src()` exist today) — this case's implementer adds the equivalent fields to `SkillsListPage`, mirroring `AgentsListPage` exactly (page-object plumbing only, testid already present). | **`entity-card-icon`/`entity-card-icon-img`: on `automation/testids` only** (added for ELITEA-1899, not yet on `main` — awaiting human cherry-pick). `entity-card` (parent scope) is on-main ✓. |
| Skill card tag chip(s) | `page.get_by_test_id("entity-card-tag-chip")` (`CARD_TAG_CHIP` class constant) — **existing testid + existing page-object method** `SkillsListPage.get_card_tags(skill_name)` (`automation/pages/skills_list_page.py:141,230-265`) — reuse directly, no new work. | on-main ✓ |
| Skill card description — **hover tooltip content** (the case's step 3 "description (upon hover)" target) | **TESTID NEEDED — confirmed live gap.** `Card.jsx`'s `StyledTooltip` `title` prop renders two app-owned `<Typography>` nodes (name, then description — lines ~188–199) into a MUI Popper (`role="tooltip"`, confirmed live via accessibility snapshot: `tooltip "skill-card-2428-1e8db006 ELITEA-2428 card-view field verification description text, unique enough to spot in a hover tooltip."`). This is **not** the #579 third-party-internal-render-node exception — the tooltip's content JSX is fully app-owned (`Card.jsx` itself), MUI's `Tooltip` accepts arbitrary JSX in `title` and renders it verbatim, so a `data-testid` can be added directly to the description `<Typography sx={styles.descriptionTooltip}>` node. Fix: add `data-testid="entity-card-description-tooltip"` to that element (mirrors the `entity-card-*` shared-component naming family — this case's own code path only needs the description node, not the sibling name/title node, per the "referenced = called on the test's actual code path" ruling — do not also testid the title Typography unless a future case asserts it). Route through `add-data-testid`. | **needs-adding** — confirmed live gap, zero `data-testid` on either tooltip `Typography` today, neither on `main` nor `automation/testids` (verified via `git grep` for `descriptionTooltip`/`titleTooltip` styles keys — no `data-testid` attribute present at either JSX node). |

**Summary for the implementer / `add-data-testid`:** one real testid gap —
the card's hover-tooltip description text has no `data-testid` (add
`entity-card-description-tooltip` to `Card.jsx`'s description `Typography`,
inside the existing `StyledTooltip`'s `title` JSX). Everything else this
case touches (icon, name, tags, view-toggle) already has a testid; the icon
pair (`entity-card-icon`/`entity-card-icon-img`) is on `automation/testids`
only (ELITEA-1899, awaiting human cherry-pick to `main`) but needs no NEW
`add-data-testid` work — just page-object plumbing mirroring
`AgentsListPage`.

## Network Behavior
- `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}` — create, `201`,
  payload `{name, description, versions: [{name: "base", instructions}]}`
  (Test Data setup, via `SkillFormPage`, not asserted as part of the case
  itself).
- `GET /api/v2/elitea_core/skills/prompt_lib/{project_id}?sort_by=
  created_at&sort_order=desc&query=&tags=&limit=20&offset=0` — list load on
  `/skills/all`; each row carries `name`, `description`, `tags`, `icon_meta`
  — usable for a data-level cross-check alongside the visual card
  assertions (not strictly required, since the case is explicitly a UI
  presence/hover check).
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project_id}/{id}` —
  cleanup, via `SkillAPI.delete_skill()`.

## Known Defects / Observations Found During Exploration

No functional product defect was found. All 3 case steps live-verified
end-to-end: Card view is the default view on `/skills/all` (no click
needed); the created skill's card correctly shows its icon, name, tag, and
reveals its exact description text only via a ~1s-delayed hover tooltip.

One non-blocking observation, informational only (not a defect — see
Concrete Handles for the reasoning):

1. **[Informational — not filed] The Skills page's view-toggle buttons
   carry `agent-*`-prefixed testids** (`agent-card-view-button` /
   `agent-table-view-button`) because the shared `ViewToggle.jsx` component
   hardcodes those as its default prop values and `Skills.jsx` doesn't
   override them. Functionally correct — not filed as a defect, same
   reasoning already recorded for `SkillsListPage.search_input`'s identical
   `agent-search-input` reuse.

## Blocked Steps
None. All 3 case steps were executed end-to-end live against the real DEV
backend: create → navigate → per-field card verification (icon, name,
hover-description, tags), then cleanup.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_card_view_fields.py` (new file —
  no existing test asserts all four card fields together; closest neighbor
  is `test_skill_tag_filter.py`'s tag-chip assertions and
  `test_skill_pin_unpin.py`'s `entity-card`/`entity-card-name` reuse).
- Reuse `SkillsListPage.skill_card` / `.skill_card_name` /
  `.get_card_tags(name)` as-is. Add `entity_card_icon` +
  `get_card_icon_src(name)` to `SkillsListPage`, copying
  `AgentsListPage.entity_card_icon` / `get_card_icon_src()` verbatim
  (same shared `Card.jsx`/`EntityIcon` component, same testids).
  Add `card_view_button`/`table_view_button` fields to `SkillsListPage`
  using the confirmed-live `agent-card-view-button`/`agent-table-view-button`
  testids (do NOT rename/re-add — reuse exactly, per the naming-quirk note
  above), mirroring `AgentsListPage.card_view_button`/`table_view_button`
  minus the `fallback=` param (legacy, forbidden in new code — the AGENTS
  page object's `fallback=lambda ...` on these same two fields is
  pre-existing tech debt, do not copy it).
- Hover assertion: `card_name_locator.filter(has_text=skill_name).hover()`
  then assert the tooltip's testid (`entity-card-description-tooltip`,
  once added) `to_be_visible()` and `to_have_text(description)` — Playwright
  auto-retries past the ~1s `enterDelay`, no manual wait needed once the
  testid exists. Do not assert via a raw `role=tooltip` locator once the
  testid lands (testid-only policy) — the `role="tooltip"` accessibility
  snapshot was used only for THIS exploration to confirm the tooltip's
  existence/content, not as the shipped locator.
- Test data: use a fresh `SkillFormPage`-created skill (see Test Data) —
  do not mutate/reuse a pre-existing production-like skill, since this case
  needs full control over all four asserted fields (icon is generic/
  unconfigurable either way, but name/description/tags must be
  test-authored and distinctive).
