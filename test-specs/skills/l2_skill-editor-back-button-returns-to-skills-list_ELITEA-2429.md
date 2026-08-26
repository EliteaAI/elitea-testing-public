# Test Case: Skills editor back button returns to Skills list

## Metadata
- **TMS ID**: ELITEA-2429
- **Linked Story**: none
- **Priority**: l2 (medium, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: `ready-for-automation` — all 3 case steps executed end-to-end
  against the live system; back navigation lands on the Skills list, not
  Chat, exactly as the case describes. No product defect found.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- At least one skill exists in the current project. **Confirmed live**: the
  `Private` / project 399 Skills dashboard already contains 21 skills — no
  new skill needed to be created.

## Test Data
### reuse-existing
- Any existing skill in the project's Skills list. This run used
  **`formatter`** (skill id `948`) — a pre-existing fixture-seeded skill,
  not created or deleted by this analysis run. No disposable test data was
  generated; nothing to clean up (see § Cleanup).

## Test Steps
1. Navigate to `${BASE_URL}/skills/all`, then click into an existing skill
   card (`formatter`) to open it for editing.
   - **Verify — PASSES.** Skills dashboard loads first (`Page Title:
     "Skills: all - project_user_659"`); clicking the card navigates to
     `/skills/all/948?viewMode=owner&name=formatter` (`Page Title: "Skill:
     formatter - project_user_659"`), the skill editor renders (General
     section, VERSION selector, Save/Save As Version/Discard controls, test
     panel).
2. Click the Back button (`data-testid="back-button"`, top-left of the
   skill editor header — confirmed present via a live accessibility
   snapshot before clicking; shared `BackButton.jsx` component, same
   element already exposed as `AgentDetailPage.back_button` on the Agent
   detail page).
   - **Verify — PASSES.** Browser navigates to `http://localhost:5173/skills/all`
     (confirmed via the live page URL immediately after the click).
3. Verify navigation goes to the Skills list page and NOT to the Chats page.
   - **Verify — PASSES.** Landed URL is `/skills/all` — it does **not**
     contain `/chat` (the Chats page route). `Page Title: "Skills: all -
     project_user_659"`; the "Skills" header and Import / view-toggle
     toolbar are present — same DOM shape as the initial Step-1 load, not
     the Chat page or any other unrelated route. All skill cards
     (`formatter` included) render again in the grid.

## Expected Results
Clicking the Back button in the Skill editor header returns the user to the
Skills list (`/skills/all`) — never to the Chats page (`/chat`) or any other
route. The case's "Expected Final State" and Pass/Fail criteria are exactly
this single navigation-target assertion; no other product behavior is
implied.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| 1 Open any Skill for editing | Target page/section loads successfully | Step 1 | URL `/skills/all/948?...`, page title, editor sections render | asserted |
| 2 Click the Back button in the Skill editor header | Control responds; expected next state is shown | Step 2 | URL becomes `/skills/all` | asserted |
| 3 Verify navigation goes to the Skills list page and NOT to the Chats page | Condition holds as described | Step 3 | URL contains `/skills/all`, does not contain `/chat`; page title + header/toolbar DOM shape matches Step 1's dashboard load | asserted |
| Expected Final State: navigation goes to the Skills list page and NOT to the Chats page | — | Step 3 | same as above | asserted |
| Pass/Fail: "all steps complete without errors" | No errors | Steps 1–3 | console error/warning check across the flow (0 throughout) | asserted |

### Axis 2 — Analyst additions

- Explicit negative URL assertion (`"/chat" not in page.url`), not just a
  positive `/skills/all` match — *added: the case's title and Expected
  Final State both name the Chats page explicitly as the wrong outcome
  ("NOT to the Chats page"); a positive-only assertion would not by itself
  prove the negative the case is actually guarding against.*
- List-content re-render check post-back (the previously opened skill's
  card, `formatter`, is present again in the grid via
  `SkillsListPage.get_skill_card_names()`) — *added: mirrors the sibling
  `ELITEA-1869` (agent detail back-navigation) regression test's "list
  intact" check; distinguishes "the list correctly re-fetched" from "a
  blank/stuck page that merely isn't `/chat`".*
- Source-level root-cause investigation (not asserted in the test, recorded
  here for the reviewer/future maintainer): `BackButton.jsx`'s `onBack()`
  falls back to `gotoListPage()` → `NavigationHelpers.getListRouteByPageType(pageType,
  RouteDefinitions.Chat)` whenever `useBackPath()` has no `prevPath` for
  the current route (true for a direct/first-visit navigation into a
  skill, since `useBackPath.js`'s `hasMultiplePaths`/`getPrevPath` have no
  case for the Skills route prefix — unlike Applications/Pipelines/
  Toolkits/Apps). `Chat` is the **fallback** route only when `pageType` is
  unmapped; `getListRouteByPageType`'s `pageTypeToListRoute` map (`EliteaUI
  src/[fsd]/shared/lib/helpers/navigation.helpers.js`) DOES include
  `SkillDetails: RouteDefinitions.Skills`, so the fallback is never
  actually reached for the Skills editor — confirmed both by live click
  and by this source read. This case is a real, well-targeted regression
  guard against exactly this fallback-to-Chat class of bug (that class
  visibly exists in the code's *shape*, just not triggered for Skills
  today) — *added context, not a new assertion.*
- Zero console errors/warnings check across the flow — clean this run.

## Cleanup
None required. This run used a pre-existing project skill (`formatter`, id
`948`) read-only — no skill was created, edited, or deleted. No test data
was generated and nothing needs teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Status |
|---|---|---|---|
| Back button (skill editor header) | `data-testid="back-button"` — confirmed present/visible via a live accessibility snapshot before click; shared `BackButton.jsx` component, same testid already wired as `AgentDetailPage.back_button` (`automation/pages/agent_detail_page.py:542`). Added this run to `SkillDetailPage.back_button` + `SkillDetailPage.click_back_button()` (mirrors `AgentDetailPage.click_back_button()` exactly). | none needed — testid pre-exists project-wide | pre-existing (newly exposed on this page object) |
| Skills dashboard header | existing `SkillsListPage.page_header` (`testid="skills-page-header"`) — added `SkillsListPage.verify_dashboard_header_visible()` this run, mirroring `AgentsListPage.verify_dashboard_header_visible()` | none | pre-existing (newly exposed as a method) |
| Skill card (click into detail) | existing `SkillsListPage.click_skill_card(name)` (testid-only, `entity-card` filtered by text, `automation/pages/skills_list_page.py:366`) | none needed | pre-existing |
| Skill list card names (post-back verification) | Added `SkillsListPage.get_skill_card_names()` this run, mirroring `AgentsListPage.get_agent_card_names()` — reads the existing `skill_card_name` (`testid="entity-card-name"`) collection locator | none needed — testid-compliant | pre-existing testid, newly exposed as a method |

No new testids were required for this case — the Back button, dashboard
header, and card-name testids all already exist on `main`; only page-object
methods were added (additive-only, no existing method bodies touched).

## Network Behavior
- `GET /api/v2/elitea_core/skill/prompt_lib/399/948` — fires once on Step 1
  (skill detail fetch), confirming the editor loaded real data before Back
  is clicked.
- `GET /api/v2/elitea_core/skills/prompt_lib/399?sort_by=created_at&sort_order=desc&query=&tags=&limit=20&offset=0`
  — fires on the initial Step 1 list load AND again after the Step 2 Back
  click; `200 OK` both times (confirmed via live network capture). This is
  the implementer's wait signal for "list has re-loaded" post-back.

## Known Defects Found During Exploration
None found. The feature under test (Back-button navigation from the Skill
editor to the Skills list, not Chat) works exactly as the case describes —
no reverse-masking, no functional defect, no clarification needed. See
Axis 2 for the source-level trace showing *why* this is a meaningful
regression guard (a code-shape fallback-to-Chat path exists for unmapped
page types, but Skills is correctly mapped).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillsListPage` (`automation/pages/skills_list_page.py`)
  for Steps 1 and 3; `SkillDetailPage` (`automation/pages/skill_detail_page.py`)
  for Steps 1–2. Both received small additive method additions this run
  (see Concrete Handles) — no existing method body was modified.
- Suggested test-data approach: reuse an existing skill via
  `skill_api.list_skills()` (read-only, per the project's Rule 10 —
  prefer stable existing data) and `SkillsListPage.click_skill_card(name)`
  to open it through the UI (not a direct URL navigation) — this exercises
  the client-side-navigation code path (`useBackPath()`'s `routeStack`
  state), which is the more at-risk scenario for the fallback-to-Chat bug
  class traced in Axis 2.
- Wait strategy: after clicking Back, wait for the
  `skills/prompt_lib/399?...` response (or `wait_for_network()`) before
  asserting on `get_skill_card_names()` — asserting immediately on URL
  change risks a race against the re-fetch. `SkillsListPage.wait_for_page_load()`
  already does this (URL regex `.*/skills/all/?$` + `wait_for_network()`).
- Suggested test file: new `automation/tests/ui/skills/test_skill_back_navigation.py`,
  mirroring `automation/tests/ui/agents/test_agent_back_navigation.py`
  1:1 (same structure, `p2`/`regression` markers matching this case's
  medium priority).
