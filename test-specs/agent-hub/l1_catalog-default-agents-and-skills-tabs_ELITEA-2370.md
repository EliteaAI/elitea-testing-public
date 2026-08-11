---
tms_case_id: ELITEA-2370
title: "Catalog — default view opens on Agents tab and user must click Skills to navigate to Skills"
priority: high
feature: agent-hub
status: ready-for-automation
family_afs: false
---

# ELITEA-2370: Catalog default view and tab navigation

**Objective:** Verify the Catalog page loads with the Agents tab selected by
default, and that clicking the Skills tab activates it and switches the view
content.

**Priority correction:** the TMS source case's own `priority:` field is
`high` (→ `p1` per `pytest.ini`'s documented scale, same mapping as the
sibling `ELITEA-2350` case in this same feature — `priority: high` →
`@pytest.mark.p1`, confirmed live in
`automation/tests/ui/agents/test_agent_hub_page_loads_private_project.py`).
A prior (unmerged, stripped) attempt at this case filed its AFS as
`priority: 3` / `l3` — that was a mis-transcription against the TMS source,
not a deliberate override; corrected here to `l1`/`p1`.

## Preconditions

- User is authenticated and logged in to Elitea (`auth_state` fixture,
  localhost login skipped via `VITE_DEV_TOKEN`).

## Test Data

| Field | Value |
|-------|-------|
| (none) | — |

## Coverage Map — Axis 1 (Original case requirements)

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Click "Catalog" in left sidebar | Page navigates to Catalog | Step 1 | `AgentHubPage.navigate()` | asserted |
| "Welcome to ELITEA Catalog!" page loads | Page heading visible and correct | Step 2 | `page_heading` testid, `to_have_text()` | asserted |
| Agents tab selected by default | Agents tab `aria-selected="true"` | Step 3 | `is_agents_tab_selected()` | asserted |
| Skills tab visible next to Agents tab with a lightning-bolt icon | Skills tab visible + icon child rendered | Step 4 | `skills_tab` + `skills_tab_icon` testids, `to_be_visible()` | asserted |
| Main content area displays Agents content by default | Agent-scoped filter rail + agent cards render (Agents tab's own component tree is mounted) | Step 5 | `get_visible_category_filter_chips()` count == 11, `get_visible_skill_category_filter_chips()` count == 0 (absence), `wait_for_any_agent_card()` | asserted |
| Click the "Skills" tab | Skills tab receives click | Step 6 | `click_skills_tab()` | asserted |
| Skills tab becomes active/highlighted | Skills tab `aria-selected="true"` after click | Step 7 | `is_skills_tab_selected()` (also awaited inside `click_skills_tab()`) | asserted |
| Main content area switches to display Skills content with Trending and category sections | Agent-scoped filter rail unmounts, skill-scoped filter rail (incl. Trending/My Liked FEATURED chips) mounts; Agents tab's own content (cards) unmounts | Step 8 | `get_visible_skill_category_filter_chips()` count == 11, `get_visible_category_filter_chips()` count == 0 (absence), `wait_for_agent_card_count(0)` | asserted |
| Right panel shows FEATURED (Trending, My Liked) and CATEGORIES filters | ≥11 filter chips visible in both tab views (2 FEATURED + 9 CATEGORIES, confirmed live for this project) | Step 9 | chip-count assertions folded into Steps 5 + 8 (no separate step — see Notes) | asserted |

## Coverage Map — Axis 2 (Observations beyond the case)

| Observable | Why | Where |
|---|---|---|
| `catalog-skills-tab-icon` testid added to the SkillsIcon svg | Case Step 4 explicitly names the icon as part of the Skills tab's identity; no testid existed on it before this case (EliteaAI/EliteaUI@da16c70a) | `skills_tab_icon` locator |
| `aria-selected` is MUI `Tabs`' own native accessibility-state attribute, not a custom one this suite added | Confirms the "state via attribute, not a state-switched testid" pattern applies without any new app-side wiring | `is_agents_tab_selected()`/`is_skills_tab_selected()` docstrings |
| Filter-chip-prefix swap (`catalog-agent-category-filter-chip-*` <-> `catalog-skill-category-filter-chip-*`) is a robust content-switch signal independent of whether the project currently has any agents/skills loaded | The chip rail is driven by static per-project category config, not the live agent/skill result set — confirmed live (23 agent cards / 0 on this run — count is NOT asserted as a fixed number, only used via `wait_for_any_agent_card()`/`wait_for_agent_card_count(0)` for presence/absence) | Steps 5 + 8 |

## Declared Improvisation (role-overrides.md § canon-gap protocol)

The AFS produced by two prior (unmerged) attempts at this case specified the
"main content switched" observable as `page.locator("main")` read for
"agent"/"skill" substring text. **That is a non-testid handle and is out of
contract under this project's testid-only locator policy** — the second prior
attempt's review flagged it, the fix round invented a `catalog-main-content`
wrapper testid to route around it, but never actually added that testid to
EliteaUI (`add-data-testid` was never run for it), and the branch was
eventually stripped from the batch trunk for exactly this reason (see
`automation/pages/agent_hub_page.py` git history, commit
`a1416e5e`: *"strip ELITEA-2370's broken testid reference
(catalog-main-content)"*).

**Chosen improvisation:** verify the content switch via two already-testid-backed,
independently-verified-live signals instead of reading `main`'s raw text:

1. The right-panel filter-chip prefix swap (`catalog-agent-category-filter-chip-*`
   ⇄ `catalog-skill-category-filter-chip-*}`) — confirmed live to flip cleanly
   11→0 / 0→11 on tab click, with **zero new testid needed** (both prefixes
   already existed on `automation/testids` from ELITEA-2352/2367).
2. Agent-card presence/absence (`wait_for_any_agent_card()` /
   `wait_for_agent_card_count(0)`) — the AgentsTab component tree unmounting is
   itself evidence the main content area re-rendered to a different tab's
   content, independent of card count (which is live, mutable data — not
   hardcoded).

Both signals are driven by the SAME underlying component swap
(`isSkillsTab ? <SkillsTab .../> : <AgentsTab .../>}` in `EliteaCatalog.jsx`)
that the case's "main content" language describes — this is a **technique**
substitution (the *how*), not a scope change (the *what*): the case's actual
requirement ("content switches when the tab is clicked") is still fully
asserted, just through a testid-compliant handle instead of a raw HTML
landmark.

**Reasoning for the reviewer:** this closes the exact defect class that sank
both prior attempts (an invented-but-never-added testid) without weakening
any assertion — if anything it strengthens the check, since the filter-chip
swap is verifiable in BOTH the populated and empty-catalog cases where a
"main contains the word 'skill'" text check would be far more fragile (the
word "skill" appears in agent names/descriptions too, in this project's real
data — confirmed live: several agent cards' visible text contains "skill").

## Steps

### Step 1 — Navigate to Catalog

**Action:** `AgentHubPage.navigate()` → `/elitea-catalog`.

**Expected:** Page loads; `page_heading` becomes visible (built into `navigate()`).

### Step 2 — Verify page heading

**Action:** Read `page_heading` text.

**Expected:** `"Welcome to ELITEA Catalog!"`

### Step 3 — Verify Agents tab selected by default

**Action:** `is_agents_tab_selected()`.

**Expected:** `True`.

### Step 4 — Verify Skills tab visible with icon

**Action:** Check `skills_tab` and `skills_tab_icon` visibility.

**Expected:** Both visible.

### Step 5 — Verify main content displays Agents content by default

**Action:**
1. `wait_for_any_agent_card()` (at least one agent card rendered).
2. `get_visible_category_filter_chips()` count == 11.
3. `get_visible_skill_category_filter_chips()` count == 0 (absence — skill-scoped rail not mounted while on Agents tab).

**Expected:** All three hold.

### Step 6 — Click Skills tab

**Action:** `click_skills_tab()`.

**Expected:** Click succeeds; method's own `expect(...).to_have_attribute("aria-selected", "true")` wait resolves (no separate step needed for the click itself — folded with Step 7's assertion, since the method encapsulates both per this project's "smart navigation/action" page-object convention, `.claude/rules/page-objects.md`).

### Step 7 — Verify Skills tab active after click

**Action:** `is_skills_tab_selected()`.

**Expected:** `True`. `is_agents_tab_selected()` == `False` (both signals flip together — a defect if only one does, per the original case's own framing).

### Step 8 — Verify main content switches to Skills

**Action:**
1. `wait_for_agent_card_count(0)` (Agents tab's own cards unmounted).
2. `get_visible_skill_category_filter_chips()` count == 11.
3. `get_visible_category_filter_chips()` count == 0 (absence — agent-scoped rail unmounted).

**Expected:** All three hold.

### Step 9 — Right panel FEATURED + CATEGORIES filters

Folded into Steps 5 and 8's chip-count assertions (11 = 2 FEATURED + 9
CATEGORIES for this project, confirmed live) rather than a separate step —
there is no additional observable beyond "the expected chip count is
present in each tab", already covered above. No `FEATURED`/`Categories`
section-header text assertion is added (no testid exists on those labels and
the chip-count check already proves the rail rendered); flag as a
possible follow-up backfill, not required by this case's Pass/Fail criteria
(chip *presence*, not the labels' text, is what the case asks for).

## Known Defects

None at analysis time (2026-08-11).

## Notes

- **Tab behavior:** switching tabs updates `aria-selected` and the filter-rail
  content synchronously (no network round-trip — confirmed live), so
  `expect(...).to_have_attribute(...)` is sufficient; no `wait_for_response()`
  is needed around the click.
- **Empty-state tolerance:** `wait_for_any_agent_card()`/`wait_for_agent_card_count(0)`
  are presence/absence checks, not fixed counts — if this project ever has
  zero agents or zero skills, the filter-chip-prefix checks (Steps 5/8 parts
  2–3) remain the primary signal and don't depend on card population.

## Handles Reference

PROVENANCE verified via fresh `git fetch origin` + two-ref `git grep` against
`EliteaUI` (`.agents/role-overrides.md` § Analyst slot), 2026-08-11. **None of
these are on `main` yet** — all currently live only on `automation/testids`,
awaiting a human cherry-pick (the prior AFS's "on-main ✓" claims for the
pre-existing rows were stale/unverified; corrected here).

| Element | Locator | PROVENANCE | Status |
|---|---|---|---|
| Page heading | `[data-testid="catalog-page-heading"]` | on-automation/testids only ✓ (awaiting human promotion to main) | existing |
| Agents tab | `[data-testid="catalog-agents-tab"]` | on-automation/testids only ✓ (awaiting human promotion to main) | existing |
| Skills tab | `[data-testid="catalog-skills-tab"]` | on-automation/testids only ✓ (awaiting human promotion to main) | existing |
| Skills tab icon | `[data-testid="catalog-skills-tab-icon"]` | on-automation/testids only ✓ (EliteaAI/EliteaUI@da16c70a, this case; awaiting human promotion to main) | added this case |
| Agent filter chips | `[data-testid^="catalog-agent-category-filter-chip-"]` | on-automation/testids only ✓ (ELITEA-2352; awaiting human promotion to main) | existing |
| Skill filter chips | `[data-testid^="catalog-skill-category-filter-chip-"]` | on-automation/testids only ✓ (ELITEA-2352/2367 wiring, `SKILL_CATEGORY_FILTER_CHIP_PREFIX` constant added this case; awaiting human promotion to main) | existing testid, new page-object constant |
| Agent cards | `[data-testid^="catalog-agent-card-"]` | on-automation/testids only ✓ (awaiting human promotion to main) | existing |
